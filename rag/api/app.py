# api/app.py
from __future__ import annotations
import os
from typing import List, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.documents import Document
from pathlib import Path
import csv

from rag.chains import make_qa_chain, make_classify_chain
from rag.retrieval import get_hybrid_retriever
from rag.semantic_cache import get_semantic_cache
from rag.heuristics import auto_rule_hits, infer_regions
from api.schemas import (
    AskRequest, AskResponse,
    SearchRequest, SearchResponse, SearchDoc,
    ClassifyRequest, ClassifyResponse,
    ClassifyAutoRequest,
    BatchClassifyRequest, BatchClassifyResponse, BatchClassifyRow,
    BatchClassifyAutoRequest
)
from api.utils import rows_to_csv

load_dotenv()

app = FastAPI(title="Geo-Reg Compliance API", version="0.1.0")

# --- CORS for Next.js localhost ---
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Chains ---
# Groq-backed chains (Step 3)
QA_CHAIN = make_qa_chain(k=5, mmr=False)
CLASSIFY_CHAIN = make_classify_chain(k=5, mmr=False)

@app.get("/health")
def health():
    return {"ok": True}

# ---------- Ask (RAG QA) ----------
@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    try:
        # Get semantic cache instance
        cache = get_semantic_cache()
        
        # Try to get cached response
        cached_answer = cache.get(req.question)
        if cached_answer is not None:
            return AskResponse(answer=cached_answer)
        
        # No cache hit, process normally
        chain = make_qa_chain(k=req.k, mmr=req.mmr)
        answer: str = chain.invoke(req.question)
        
        # Cache the result
        cache.set(req.question, answer)
        
        return AskResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Search (raw retrieval preview) ----------
@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest):
    try:
        retriever = get_hybrid_retriever(k=req.k, mmr=req.mmr)
        docs: List[Document] = retriever.invoke(req.query)
        return SearchResponse(
            docs=[SearchDoc(content=d.page_content, metadata=d.metadata) for d in docs]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Laws manifest ----------
@app.get("/laws")
def list_laws():
    try:
        manifest = os.getenv("MANIFEST_CSV", "data/laws_manifest.csv")
        # Try as-is first (assuming cwd=rag/). If missing, resolve relative to this file.
        p = Path(manifest)
        if not p.exists():
            p = (Path(__file__).resolve().parents[1] / manifest).resolve()
        if not p.exists():
            return {"laws": []}
        rows = []
        with p.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append({
                    "file_path": r.get("file_path", ""),
                    "law_name": r.get("law_name", ""),
                    "region": r.get("region", ""),
                    "source": r.get("source", ""),
                    "article_or_section": r.get("article_or_section", ""),
                })
        return {"laws": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Classify (single) ----------
@app.post("/classify", response_model=ClassifyResponse)
def classify(req: ClassifyRequest):
    try:
        # Get semantic cache instance
        cache = get_semantic_cache()
        
        # Create cache key from feature_text (main content to classify)
        cache_key = f"classify:{req.feature_text}"
        
        # Try to get cached response
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return ClassifyResponse(**cached_result)
        
        # No cache hit, process normally
        # Use override regions if provided, else infer from text
        regions = req.regions if getattr(req, "regions", None) else infer_regions(req.feature_text)
        # Build provenance from retrieval (law snippets surfaced)
        filtered_used = bool(regions)
        retriever = get_hybrid_retriever(k=req.k, mmr=req.mmr, regions=regions if regions else None)
        docs: List[Document] = retriever.invoke(req.feature_text)
        # Fallbacks: try each region solo, then drop filter entirely
        if not docs and regions:
            for r in regions:
                retriever_single = get_hybrid_retriever(k=req.k, mmr=req.mmr, regions=[r])
                docs = retriever_single.invoke(req.feature_text)
                if docs:
                    filtered_used = True
                    break
        if not docs:
            retriever_any = get_hybrid_retriever(k=req.k, mmr=req.mmr, regions=None)
            docs = retriever_any.invoke(req.feature_text)
            if docs:
                filtered_used = False

        # Post-filter safeguard: if we inferred regions but had to drop the store filter,
        # keep only matching regions from retrieved docs when possible.
        if docs and regions and not filtered_used:
            docs_filtered = [d for d in docs if (d.metadata or {}).get("region") in regions]
            if docs_filtered:
                docs = docs_filtered[: req.k]
                filtered_used = True
        retrieved = []
        for d in docs:
            m = d.metadata or {}
            retrieved.append({
                "law_name": m.get("law_name"),
                "region": m.get("region"),
                "article_or_section": m.get("article_or_section"),
                "source": m.get("source"),
                "h1": m.get("h1"),
                "h2": m.get("h2"),
                "h3": m.get("h3"),
                "source_path": m.get("source_path"),
            })

        # If region-filtered retrieval wasn’t used (or failed), build unfiltered chain for answer quality
        use_regions = regions if filtered_used else None
        chain = make_classify_chain(k=req.k, mmr=req.mmr, regions=use_regions)
        out: Dict[str, Any] = chain.invoke({"feature_text": req.feature_text, "rule_hits": req.rule_hits})
        
        # Cache the result
        cache.set(cache_key, out)
        
        # Merge/ensure provenance
        prov = out.get("provenance", {}) or {}
        input_rules = req.rule_hits or []
        llm_rules = prov.get("rules_hit", []) or []
        # keep both: 'rules_input' = provided; 'rules_hit' = union for audit
        prov["rules_input"] = input_rules
        prov["rules_hit"] = sorted(set(llm_rules + input_rules))
        prov.setdefault("retrieved", retrieved)
        # Fill retrieved_law_ids if missing, e.g., ["US-UT:Utah Social Media Regulation Act"]
        if not prov.get("retrieved_law_ids"):
            ids = []
            for r in retrieved:
                rgn = (r.get("region") or "").strip()
                name = (r.get("law_name") or "").strip()
                if rgn or name:
                    ids.append(f"{rgn}:{name}".strip(":"))
            prov["retrieved_law_ids"] = ids
        prov.setdefault("regions_inferred", regions)
        prov.setdefault("region_filter_used", filtered_used)
        # Confidence calibration
        out_conf = float(out.get("confidence", 0.5))
        rules_combined = prov.get("rules_hit", [])
        out["confidence"] = _calibrate_confidence(out_conf, rules_combined, regions, filtered_used)
        out["provenance"] = prov
        return ClassifyResponse(**out)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Classify (auto rules) ----------
@app.post("/classify_auto", response_model=ClassifyResponse)
def classify_auto(req: ClassifyAutoRequest):
    try:
        rules = auto_rule_hits(req.feature_text)
        return classify(ClassifyRequest(feature_text=req.feature_text, rule_hits=rules, k=req.k, mmr=req.mmr, regions=getattr(req, "regions", None)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Batch Classify ----------
@app.post("/batch_classify", response_model=BatchClassifyResponse)
def batch_classify(req: BatchClassifyRequest):
    try:
        rows: List[BatchClassifyRow] = []
        for item in req.rows:
            regions = req.regions if getattr(req, "regions", None) else infer_regions(item.feature_text)
            chain = make_classify_chain(k=req.k, mmr=req.mmr, regions=regions)
            out: Dict[str, Any] = chain.invoke({"feature_text": item.feature_text, "rule_hits": item.rule_hits})
            # Calibrate confidence per row
            rules_combined = item.rule_hits or []
            calibrated = _calibrate_confidence(float(out.get("confidence", 0.5)), rules_combined, regions, bool(regions))
            rows.append(BatchClassifyRow(
                feature_text=item.feature_text,
                needs_geo_logic=out.get("needs_geo_logic","unclear"),
                reasoning=out.get("reasoning",""),
                laws=out.get("laws",[]),
                confidence=calibrated,
                rule_hits=item.rule_hits,
            ))
        payload = {"rows": rows}
        if req.csv:
            # Build CSV string (for downloads)
            flat_rows = [r.model_dump() for r in rows]
            payload["csv"] = rows_to_csv(flat_rows)
        return BatchClassifyResponse(**payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Cache Management ----------
@app.get("/cache/stats")
def cache_stats():
    """Get semantic cache statistics."""
    try:
        cache = get_semantic_cache()
        return cache.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/cache/clear")
def clear_cache():
    """Clear the semantic cache."""
    try:
        cache = get_semantic_cache()
        cache.clear()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Batch Classify (auto rules) ----------
@app.post("/batch_classify_auto", response_model=BatchClassifyResponse)
def batch_classify_auto(req: BatchClassifyAutoRequest):
    try:
        rows: List[BatchClassifyRow] = []
        for item in req.rows:
            rules = auto_rule_hits(item.feature_text)
            regions = req.regions if getattr(req, "regions", None) else infer_regions(item.feature_text)
            chain = make_classify_chain(k=req.k, mmr=req.mmr, regions=regions)
            out: Dict[str, Any] = chain.invoke({"feature_text": item.feature_text, "rule_hits": rules})
            calibrated = _calibrate_confidence(float(out.get("confidence", 0.5)), rules, regions, bool(regions))
            rows.append(BatchClassifyRow(
                feature_text=item.feature_text,
                needs_geo_logic=out.get("needs_geo_logic","unclear"),
                reasoning=out.get("reasoning",""),
                laws=out.get("laws",[]),
                confidence=calibrated,
                rule_hits=rules,
            ))
        payload = {"rows": rows}
        if req.csv:
            flat_rows = [r.model_dump() for r in rows]
            payload["csv"] = rows_to_csv(flat_rows)
        return BatchClassifyResponse(**payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Confidence calibration ----------
def _calibrate_confidence(base: float, rules: List[str], regions: List[str], filter_used: bool) -> float:
    base = max(0.0, min(1.0, float(base)))
    bump_cues = {"legal_cue", "eu", "utah", "florida", "california", "us_federal", "gh", "asl", "nsp", "lcp"}
    if filter_used and (set(rules) & bump_cues):
        base += 0.05
    if not filter_used:
        base -= 0.05
    # clamp
    if base < 0.2:
        base = 0.2
    if base > 0.95:
        base = 0.95
    return round(base, 4)

# (helper moved to rag.heuristics.infer_regions)

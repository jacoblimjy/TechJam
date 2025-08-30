# api/app.py
from __future__ import annotations
import os
from typing import List, Dict, Any
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.documents import Document
from pathlib import Path
import csv

from rag.chains import make_qa_chain, make_classify_chain
from rag.retrieval import get_hybrid_retriever, rerank_docs, rerank_with_info
from rag.heuristics import auto_rule_hits, infer_regions
from api.schemas import (
    AskRequest, AskResponse,
    SearchRequest, SearchResponse, SearchDoc,
    ClassifyRequest, ClassifyResponse,
    ClassifyAutoRequest,
    BatchClassifyRequest, BatchClassifyResponse, BatchClassifyRow,
    BatchClassifyAutoRequest,
    FeedbackRequest, FeedbackResponse,
)
from api.utils import rows_to_csv, append_jsonl, utc_now_iso, jsonl_has_record, write_json
from rag.config import get_config
from rag.chunking import header_first_then_recursive
from rag.qdrant_store import add_documents, delete_by_source_path, delete_by_source_paths

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
        chain = make_qa_chain(k=req.k, mmr=req.mmr)
        answer: str = chain.invoke(req.question)
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

# ---------- Laws upload (PDF → txt → manifest → chunk + index) ----------
@app.post("/laws/upload")
async def upload_law(
    file: UploadFile = File(...),
    law_name: str = Form(...),
    region: str = Form(...),
    source: str = Form(""),
    article_or_section: str = Form(""),
):
    try:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF uploads are supported")

        # 1) Save uploaded PDF to tmp
        cfg = get_config()
        tmp_dir = (Path(__file__).resolve().parents[1] / "data/tmp_uploads").resolve()
        tmp_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = tmp_dir / file.filename
        content = await file.read()
        pdf_path.write_bytes(content)

        # 2) Extract text using docling if available, else fallback to pypdf
        text = ""
        try:
            from docling.document_converter import DocumentConverter  # type: ignore
            conv = DocumentConverter()
            res = conv.convert(str(pdf_path))
            text = getattr(res, "text", None) or getattr(res, "plaintext", None) or ""
            if not text and hasattr(res, "document"):
                try:
                    text = res.document.export_to_text()
                except Exception:
                    pass
        except Exception:
            text = ""
        if not text:
            try:
                from pypdf import PdfReader  # type: ignore
                reader = PdfReader(str(pdf_path))
                parts = []
                for p in reader.pages:
                    try:
                        parts.append(p.extract_text() or "")
                    except Exception:
                        continue
                text = "\n\n".join(parts).strip()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to extract text: {e}")
        if len(text.strip()) < 50:
            raise HTTPException(status_code=400, detail="Parsed text seems empty or too short")

        # 3) Save txt into kb_raw
        safe_base = "".join(c if c.isalnum() or c in ("-","_"," ") else "_" for c in law_name).strip().replace(" ", "_")
        if not safe_base:
            safe_base = Path(file.filename).stem
        txt_name = f"{safe_base}.txt"
        kb_dir = (Path(__file__).resolve().parents[1] / cfg.raw_dir).resolve()
        kb_dir.mkdir(parents=True, exist_ok=True)
        txt_path = kb_dir / txt_name
        txt_path.write_text(text, encoding="utf-8")

        # 4) Update manifest CSV
        manifest = os.getenv("MANIFEST_CSV", "data/laws_manifest.csv")
        man_path = Path(manifest)
        if not man_path.exists():
            man_path = (Path(__file__).resolve().parents[1] / manifest).resolve()
        write_header = not man_path.exists()
        man_path.parent.mkdir(parents=True, exist_ok=True)
        with man_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["file_path","law_name","region","source","article_or_section"])
            if write_header:
                writer.writeheader()
            writer.writerow({
                "file_path": txt_name,
                "law_name": law_name,
                "region": region,
                "source": source,
                "article_or_section": article_or_section,
            })

        # 5) Chunk the text and index into Qdrant (only the new law)
        content_with_header = f"## {law_name}\n\n{text.strip()}"
        docs = header_first_then_recursive(
            text=content_with_header,
            source_path=str(txt_path),
            headers=[("#","h1"),("##","h2"),("###","h3")],
            max_header_chunk_chars=cfg.max_header_chunk_chars,
            recursive_chunk_chars=cfg.recursive_chunk_chars,
            recursive_overlap_chars=cfg.recursive_overlap_chars,
            skip_reference_sections=cfg.skip_reference_sections,
        )
        for d in docs:
            m = d.metadata
            m.setdefault("law_name", law_name)
            m.setdefault("region", region)
            m.setdefault("source", source)
            if article_or_section:
                m.setdefault("article_or_section", article_or_section)
        added = add_documents(docs)

        return {
            "ok": True,
            "txt_file": str(txt_path.name),
            "manifest": str(man_path),
            "indexed_chunks": added,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Laws delete (remove txt + manifest row + index) ----------
@app.post("/laws/delete")
def delete_law(body: Dict[str, Any]):
    try:
        file_path = (body.get("file_path") or "").strip()
        if not file_path:
            raise HTTPException(status_code=400, detail="file_path is required")

        # Resolve kb_raw absolute path
        cfg = get_config()
        kb_dir = (Path(__file__).resolve().parents[1] / cfg.raw_dir).resolve()
        abs_txt = (kb_dir / file_path).resolve()

        # 1) Delete from Qdrant by source_path (try common variants)
        # Stored payload may be absolute or repo-relative depending on how it was indexed previously.
        proj_root = Path(__file__).resolve().parents[1]
        v1 = str(abs_txt)
        v2 = str((Path(cfg.raw_dir) / file_path))  # e.g., data/kb_raw/file.txt
        v3 = str((Path("rag") / Path(cfg.raw_dir) / file_path))  # e.g., rag/data/kb_raw/file.txt
        variants = [v1, v2, v3]
        deleted = delete_by_source_paths(variants)

        # 2) Remove from manifest
        manifest = os.getenv("MANIFEST_CSV", "data/laws_manifest.csv")
        man_path = Path(manifest)
        if not man_path.exists():
            man_path = (Path(__file__).resolve().parents[1] / manifest).resolve()
        kept_rows = []
        if man_path.exists():
            with man_path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    if (r.get("file_path") or "").strip() != file_path:
                        kept_rows.append(r)
            with man_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["file_path","law_name","region","source","article_or_section"])
                writer.writeheader()
                for r in kept_rows:
                    writer.writerow(r)

        # 3) Remove the txt file
        removed_file = False
        try:
            if abs_txt.exists():
                abs_txt.unlink()
                removed_file = True
        except Exception:
            pass

        return {"ok": True, "deleted_points": deleted, "removed_file": removed_file, "manifest_rows": len(kept_rows)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Classify (single) ----------
@app.post("/classify", response_model=ClassifyResponse)
def classify(req: ClassifyRequest):
    try:
        req_id = str(uuid.uuid4())
        import time
        t0 = time.perf_counter()
        # Use override regions if provided, else infer from text
        regions = req.regions if getattr(req, "regions", None) else infer_regions(req.feature_text)
        # Build provenance from retrieval (law snippets surfaced)
        filtered_used = bool(regions)
        retriever = get_hybrid_retriever(k=req.k, mmr=req.mmr, regions=regions if regions else None)
        docs: List[Document] = retriever.invoke(req.feature_text)
        rerank_info: Dict[str, Any] = {"method": "disabled"}
        try:
            docs, rerank_info = rerank_with_info(req.feature_text, docs, top_k=req.k)
        except Exception:
            rerank_info = {"method": "error"}
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
        # Final rerank on the chosen set (capture info if earlier failed)
        if docs and (rerank_info.get("method") in {"disabled", "error"}):
            try:
                docs, rerank_info = rerank_with_info(req.feature_text, docs, top_k=req.k)
            except Exception:
                rerank_info = {"method": "error"}
        t1 = time.perf_counter()

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
        # Metrics
        metrics = prov.get("metrics", {}) or {}
        metrics.update({
            "elapsed_ms": int((t1 - t0) * 1000),
            "k": req.k,
            "mmr": bool(req.mmr),
            "retrieved_count": len(docs),
            "model": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            "rerank": rerank_info,
            "request_id": req_id,
        })
        prov["metrics"] = metrics
        # Confidence calibration
        out_conf = float(out.get("confidence", 0.5))
        rules_combined = prov.get("rules_hit", [])
        out["confidence"] = _calibrate_confidence(out_conf, rules_combined, regions, filtered_used)
        out["provenance"] = prov
        # Append server-side inference log (best-effort)
        try:
            log_path = os.getenv("CLASSIFY_LOG_JSONL", "data/classify_log.jsonl")
            append_jsonl(log_path, {
                "ts": utc_now_iso(),
                "request_id": req_id,
                "feature_text": req.feature_text,
                "rule_hits": req.rule_hits,
                "regions": regions,
                "response": out,
            })
        except Exception:
            pass
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

# ---------- Feedback (review + logging) ----------
@app.post("/feedback", response_model=FeedbackResponse)
def feedback(req: FeedbackRequest):
    try:
        path = os.getenv("FEEDBACK_LOG_JSONL", "data/feedback.jsonl")
        # Enforce one feedback per classification request
        if not req.request_id:
            raise HTTPException(status_code=400, detail="request_id is required for feedback")
        if jsonl_has_record(path, "request_id", req.request_id):
            raise HTTPException(status_code=409, detail="Feedback already recorded for this request_id")
        saved = append_jsonl(path, {
            "ts": utc_now_iso(),
            "request_id": req.request_id,
            "feature_text": req.feature_text,
            "verdict": req.verdict,
            "vote": req.vote,
            "correction_needs_geo_logic": req.correction_needs_geo_logic,
            "correction_reasoning": req.correction_reasoning,
            "notes": req.notes,
            "rules_input": req.rules_input,
            "regions": req.regions,
        })
        return FeedbackResponse(ok=True, saved_path=saved)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/feedback/stats")
def feedback_stats():
    try:
        import json
        from pathlib import Path
        path = os.getenv("FEEDBACK_LOG_JSONL", "data/feedback.jsonl")
        p = Path(path)
        if not p.exists():
            p = (Path(__file__).resolve().parents[1] / path).resolve()
        if not p.exists():
            return {"total": 0, "by_vote": {}, "by_correction": {}}
        by_vote: Dict[str, int] = {}
        by_corr: Dict[str, int] = {}
        total = 0
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                total += 1
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                v = (rec.get("vote") or "").lower() or "unknown"
                by_vote[v] = by_vote.get(v, 0) + 1
                corr = (rec.get("correction_needs_geo_logic") or "none").lower()
                by_corr[corr] = by_corr.get(corr, 0) + 1
        return {"total": total, "by_vote": by_vote, "by_correction": by_corr}
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

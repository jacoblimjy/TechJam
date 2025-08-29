# api/app.py
from __future__ import annotations
import os
from typing import List, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.documents import Document

from rag.chains import make_qa_chain, make_classify_chain
from rag.retrieval import get_hybrid_retriever
from api.schemas import (
    AskRequest, AskResponse,
    SearchRequest, SearchResponse, SearchDoc,
    ClassifyRequest, ClassifyResponse,
    BatchClassifyRequest, BatchClassifyResponse, BatchClassifyRow
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

# ---------- Classify (single) ----------
@app.post("/classify", response_model=ClassifyResponse)
def classify(req: ClassifyRequest):
    try:
        chain = make_classify_chain(k=req.k, mmr=req.mmr)
        out: Dict[str, Any] = chain.invoke({"feature_text": req.feature_text, "rule_hits": req.rule_hits})
        # Coerce to response model
        return ClassifyResponse(**out)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Batch Classify ----------
@app.post("/batch_classify", response_model=BatchClassifyResponse)
def batch_classify(req: BatchClassifyRequest):
    try:
        chain = make_classify_chain(k=req.k, mmr=req.mmr)
        rows: List[BatchClassifyRow] = []
        for item in req.rows:
            out: Dict[str, Any] = chain.invoke({"feature_text": item.feature_text, "rule_hits": item.rule_hits})
            rows.append(BatchClassifyRow(
                feature_text=item.feature_text,
                needs_geo_logic=out.get("needs_geo_logic","unclear"),
                reasoning=out.get("reasoning",""),
                laws=out.get("laws",[]),
                confidence=float(out.get("confidence", 0.5)),
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

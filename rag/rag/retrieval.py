from __future__ import annotations
from typing import Dict, Any, List
import os
from functools import lru_cache
from langchain_core.vectorstores import VectorStoreRetriever
from rag.qdrant_store import get_vectorstore
from qdrant_client.http.models import Filter, FieldCondition, MatchAny, MatchValue
from langchain_core.documents import Document

# Optional cross-encoder reranker (sentence-transformers). Fallback to a simple lexical score.
try:
    from sentence_transformers import CrossEncoder  # type: ignore
except Exception:  # pragma: no cover
    CrossEncoder = None  # type: ignore

def _build_filter(regions: list[str] | None):
    if not regions:
        return None
    if len(regions) == 1:
        cond = FieldCondition(key="region", match=MatchValue(value=regions[0]))
    else:
        cond = FieldCondition(key="region", match=MatchAny(any=regions))
    return Filter(must=[cond])


def get_hybrid_retriever(k: int = 5, mmr: bool = False, regions: list[str] | None = None) -> VectorStoreRetriever:
    """
    Returns a retriever over Qdrant hybrid store.
    - k: top-k docs
    - mmr: enable Maximal Marginal Relevance (diverse results)
    - regions: optional list of region codes to filter results (e.g., ["US-UT", "US"]).
    """
    vs = get_vectorstore()
    flt = _build_filter(regions)
    if mmr:
        return vs.as_retriever(search_type="mmr", search_kwargs={"k": k, "fetch_k": max(2*k, 20), "filter": flt})
    return vs.as_retriever(search_kwargs={"k": k, "filter": flt})

def debug_print_hits(docs):
    for i, d in enumerate(docs, 1):
        m = d.metadata
        title = m.get("h3") or m.get("h2") or m.get("h1") or m.get("law_name") or "Untitled"
        print(f"[{i}] {title} | {m.get('region','')} | src={m.get('source_path','')}")
        print(d.page_content[:240].replace("\n"," ") + ("..." if len(d.page_content)>240 else ""))
        print("-"*80)


# --------- Reranker ---------

@lru_cache(maxsize=1)
def _get_cross_encoder():
    """Lazily create a CrossEncoder if enabled and available.
    Controlled by env:
      - ENABLE_RERANK=true|false (default true)
      - RERANK_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2 (default)
    """
    enabled = str(os.getenv("ENABLE_RERANK", "true")).lower() in {"1", "true", "yes"}
    if not enabled or CrossEncoder is None:
        return None
    model_name = os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    try:
        return CrossEncoder(model_name)
    except Exception:
        return None


def _lexical_scores(query: str, docs: List[Document]) -> List[float]:
    import re
    q_tokens = set(re.findall(r"\w+", (query or "").lower()))
    scores: List[float] = []
    for d in docs:
        t = set(re.findall(r"\w+", (d.page_content or "").lower()))
        inter = len(q_tokens & t)
        denom = max(1, len(q_tokens) + len(t) - inter)
        scores.append(inter / denom)
    return scores


def rerank_with_info(query: str, docs: List[Document], top_k: int | None = None) -> tuple[List[Document], Dict[str, Any]]:
    """Return reranked docs and an info dict: {method, model?, scores[]}.
    If rerank disabled or unavailable, method is 'disabled' and docs unchanged.
    """
    info: Dict[str, Any] = {"method": "disabled"}
    if not docs:
        return docs, info
    enabled = str(os.getenv("ENABLE_RERANK", "true")).lower() in {"1", "true", "yes"}
    if not enabled:
        return docs, info
    k = top_k or len(docs)
    ce = _get_cross_encoder()
    if ce is not None:
        pairs = [(query, d.page_content[:2048]) for d in docs]
        try:
            scores = ce.predict(pairs)
            ranked = sorted(zip(docs, scores), key=lambda x: float(x[1]), reverse=True)
            info = {
                "method": "cross_encoder",
                "model": os.getenv("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"),
                "scores": [float(s) for _, s in ranked[:k]],
            }
            return [d for d, _ in ranked[:k]], info
        except Exception:
            pass
    # Fallback lexical
    scores = _lexical_scores(query, docs)
    ranked = sorted(zip(docs, scores), key=lambda x: float(x[1]), reverse=True)
    info = {"method": "lexical_fallback", "scores": [float(s) for _, s in ranked[:k]]}
    return [d for d, _ in ranked[:k]], info


def rerank_docs(query: str, docs: List[Document], top_k: int | None = None) -> List[Document]:
    ranked, _ = rerank_with_info(query, docs, top_k=top_k)
    return ranked

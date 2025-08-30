from __future__ import annotations
from typing import Dict, Any
from langchain_core.vectorstores import VectorStoreRetriever
from rag.qdrant_store import get_vectorstore
from qdrant_client.http.models import Filter, FieldCondition, MatchAny, MatchValue

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

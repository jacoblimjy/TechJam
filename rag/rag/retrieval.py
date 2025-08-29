from __future__ import annotations
from typing import Dict, Any
from langchain_core.vectorstores import VectorStoreRetriever
from rag.qdrant_store import get_vectorstore

def get_hybrid_retriever(k: int = 5, mmr: bool = False) -> VectorStoreRetriever:
    """
    Returns a retriever over Qdrant hybrid store.
    - k: top-k docs
    - mmr: enable Maximal Marginal Relevance (diverse results)
    """
    vs = get_vectorstore()
    if mmr:
        return vs.as_retriever(search_type="mmr", search_kwargs={"k": k, "fetch_k": max(2*k, 20)})
    return vs.as_retriever(search_kwargs={"k": k})

def debug_print_hits(docs):
    for i, d in enumerate(docs, 1):
        m = d.metadata
        title = m.get("h3") or m.get("h2") or m.get("h1") or m.get("law_name") or "Untitled"
        print(f"[{i}] {title} | {m.get('region','')} | src={m.get('source_path','')}")
        print(d.page_content[:240].replace("\n"," ") + ("..." if len(d.page_content)>240 else ""))
        print("-"*80)

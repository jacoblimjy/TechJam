# rag/qdrant_store.py
from __future__ import annotations
import os
from typing import List
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, FilterSelector
from langchain_qdrant import QdrantVectorStore, RetrievalMode, FastEmbedSparse
from langchain_core.documents import Document

try:
    from rag.embeddings import BGEM3DenseEmbeddings
except ImportError:
    from .embeddings import BGEM3DenseEmbeddings

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") or None
COLLECTION = os.getenv("QDRANT_COLLECTION", "laws")

DENSE_NAME = "dense"
SPARSE_NAME = "sparse"

def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

def get_vectorstore(collection_name: str = COLLECTION, use_fastembed_sparse: bool = True) -> QdrantVectorStore:
    client = get_qdrant_client()
    dense = BGEM3DenseEmbeddings()
    sparse = FastEmbedSparse(model="Qdrant/bm25") if use_fastembed_sparse else None

    return QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=dense,
        sparse_embedding=sparse,
        retrieval_mode=RetrievalMode.HYBRID,
        vector_name=DENSE_NAME,            # <-- tell LC which dense vector to use
        sparse_vector_name=SPARSE_NAME,    # <-- and which sparse vector
        # force_recreate=True,             # only if you want to wipe & recreate
    )

def add_documents(docs: List[Document], batch_size: int = 128, collection_name: str = COLLECTION) -> int:
    vs = get_vectorstore(collection_name=collection_name)
    n = 0
    for i in range(0, len(docs), batch_size):
        vs.add_documents(docs[i:i+batch_size])
        n += len(docs[i:i+batch_size])
    return n

def delete_by_source_path(abs_path: str, collection_name: str = COLLECTION) -> int:
    """Delete all points where payload.source_path == abs_path.
    Returns an estimated number of deleted points (count before delete).
    """
    client = get_qdrant_client()
    flt = Filter(must=[FieldCondition(key="source_path", match=MatchValue(value=abs_path))])
    try:
        cnt = client.count(collection_name=collection_name, count_filter=flt, exact=True).count or 0
    except Exception:
        cnt = 0
    selector = FilterSelector(filter=flt)
    client.delete(collection_name=collection_name, points_selector=selector, wait=True)
    return int(cnt)

def delete_by_source_paths(paths: list[str], collection_name: str = COLLECTION) -> int:
    total = 0
    for p in paths:
        try:
            total += delete_by_source_path(p, collection_name=collection_name)
        except Exception:
            # best-effort; continue to next variant
            pass
    return total

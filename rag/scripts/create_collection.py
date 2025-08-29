#!/usr/bin/env python
from __future__ import annotations
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path: sys.path.insert(0, ROOT)

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, SparseVectorParams

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") or None
COLLECTION = os.getenv("QDRANT_COLLECTION", "laws")

BGE_M3_DIM = 1024  # bge-m3 dense size

def main():
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    if client.collection_exists(COLLECTION):
        print(f"Collection '{COLLECTION}' already exists. Skipping creation.")
        return

    print(f"Creating collection '{COLLECTION}' (dense={BGE_M3_DIM}, sparse enabled) ...")
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config={
            # name your dense vector
            "dense": VectorParams(size=BGE_M3_DIM, distance=Distance.COSINE)
        },
        sparse_vectors_config={
            # name your sparse vector
            "sparse": SparseVectorParams()
        },
        # optional: on-disk payload, optimizers, etc.
    )
    print("✅ Created.")

if __name__ == "__main__":
    main()

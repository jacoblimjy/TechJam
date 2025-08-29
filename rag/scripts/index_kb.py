from __future__ import annotations
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
    
import argparse, json
from pathlib import Path
from typing import List

from langchain_core.documents import Document
from rag.qdrant_store import add_documents

def load_chunks(jsonl_path: str) -> List[Document]:
    docs: List[Document] = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            text = rec["text"].strip()
            meta = rec.get("metadata", {})
            docs.append(Document(page_content=text, metadata=meta))
    return docs

def main():
    ap = argparse.ArgumentParser(description="Index chunks.jsonl into Qdrant (hybrid)")
    ap.add_argument("--jsonl", default="data/kb_chunks/chunks.jsonl")
    ap.add_argument("--collection", default=os.getenv("QDRANT_COLLECTION", "laws"))
    ap.add_argument("--batch", type=int, default=128)
    args = ap.parse_args()

    p = Path(args.jsonl)
    assert p.exists(), f"File not found: {p}"

    docs = load_chunks(str(p))
    print(f"Indexing {len(docs)} chunks → collection='{args.collection}' ...")
    n = add_documents(docs, batch_size=args.batch, collection_name=args.collection)
    print(f"✅ Done. Upserted {n} docs into Qdrant.")

if __name__ == "__main__":
    main()

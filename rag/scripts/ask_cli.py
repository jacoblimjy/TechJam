#!/usr/bin/env python
from __future__ import annotations
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path: sys.path.insert(0, ROOT)

from rag.chains import make_qa_chain

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="+", help="Your question")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--mmr", action="store_true")
    args = ap.parse_args()

    q = " ".join(args.question)
    chain = make_qa_chain(k=args.k, mmr=args.mmr)
    ans = chain.invoke(q)
    print("\n=== Answer ===\n")
    print(ans)

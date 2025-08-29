#!/usr/bin/env python
from __future__ import annotations
import os, sys, json
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path: sys.path.insert(0, ROOT)

from rag.chains import make_classify_chain

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="Path to a text file containing the feature artifact")
    ap.add_argument("--text", help="Inline text for the feature artifact")
    ap.add_argument("--rules", nargs="*", default=[], help="Optional rule hits to include (e.g., legal_cue asl eu)")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--mmr", action="store_true")
    args = ap.parse_args()

    assert args.file or args.text, "Provide --file or --text"
    feature_text = args.text
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            feature_text = f.read()

    chain = make_classify_chain(k=args.k, mmr=args.mmr)
    out = chain.invoke({"feature_text": feature_text, "rule_hits": args.rules})
    print(json.dumps(out, indent=2, ensure_ascii=False))

#!/usr/bin/env python
from __future__ import annotations

# --- path shim so 'rag' package resolves when run as a script ---
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
# ----------------------------------------------------------------

import argparse
from rag.config import get_config
from rag.chunking import chunk_directory, export_jsonl_and_meta

def main():
    cfg = get_config()
    parser = argparse.ArgumentParser(description="Header-first chunking with recursive fallback (skips Reference sections)")
    parser.add_argument("--raw_dir", default=cfg.raw_dir)
    parser.add_argument("--out_jsonl", default=cfg.out_jsonl)
    parser.add_argument("--out_meta_csv", default=cfg.out_meta_csv)
    parser.add_argument("--manifest", default=cfg.manifest_csv)
    parser.add_argument("--max_header_chars", type=int, default=cfg.max_header_chunk_chars)
    parser.add_argument("--chunk_chars", type=int, default=cfg.recursive_chunk_chars)
    parser.add_argument("--overlap_chars", type=int, default=cfg.recursive_overlap_chars)
    parser.add_argument("--no_skip_references", action="store_true", help="Include 'References' sections if set")
    args = parser.parse_args()

    docs = chunk_directory(
        raw_dir=args.raw_dir,
        headers=[("#","h1"),("##","h2"),("###","h3")],
        max_header_chunk_chars=args.max_header_chars,
        recursive_chunk_chars=args.chunk_chars,
        recursive_overlap_chars=args.overlap_chars,
        manifest_csv=args.manifest,
        skip_reference_sections=not args.no_skip_references,
    )
    export_jsonl_and_meta(docs, out_jsonl=args.out_jsonl, out_meta_csv=args.out_meta_csv)
    print(f"✅ Done. Wrote {len(docs)} chunks -> {args.out_jsonl}")
    print(f"   Meta CSV -> {args.out_meta_csv}")

if __name__ == "__main__":
    main()

from __future__ import annotations
import os
from dataclasses import dataclass

@dataclass
class ChunkingConfig:
    raw_dir: str = "data/kb_raw"
    out_jsonl: str = "data/kb_chunks/chunks.jsonl"
    out_meta_csv: str = "data/kb_chunks/chunks.meta.csv"
    manifest_csv: str | None = "data/laws_manifest.csv"

    # Header-first, then recursive fallback
    headers: tuple = (("#", "h1"), ("##", "h2"), ("###", "h3"))

    # Target ~900–1000 tokens via char proxy
    recursive_chunk_chars: int = 4000
    recursive_overlap_chars: int = 350

    # If a header chunk is longer than this → split recursively
    max_header_chunk_chars: int = 4200

    # Cleaners
    normalize_newlines: bool = True
    collapse_whitespace: bool = True

    # Filters
    skip_reference_sections: bool = True   # skip headers containing "reference(s)"

def get_config() -> ChunkingConfig:
    return ChunkingConfig(
        raw_dir=os.getenv("RAW_DIR", "data/kb_raw"),
        out_jsonl=os.getenv("OUT_JSONL", "data/kb_chunks/chunks.jsonl"),
        out_meta_csv=os.getenv("OUT_META_CSV", "data/kb_chunks/chunks.meta.csv"),
        manifest_csv=os.getenv("MANIFEST_CSV", "data/laws_manifest.csv") or None,
    )

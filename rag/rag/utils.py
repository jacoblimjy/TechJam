from __future__ import annotations
import json, re
from typing import List
from langchain_core.documents import Document

def format_docs_for_context(docs: List[Document]) -> str:
    lines = []
    for i, d in enumerate(docs, 1):
        m = d.metadata
        title = m.get("h3") or m.get("h2") or m.get("h1") or m.get("law_name") or "Untitled"
        cite = []
        if m.get("law_name"): cite.append(m["law_name"])
        if m.get("region"): cite.append(m["region"])
        if m.get("article_or_section"): cite.append(m["article_or_section"])
        lines.append(f"[{i}] {title} — {' | '.join([c for c in cite if c])}".strip(" —"))
        lines.append(d.page_content.strip())
        lines.append("")  # blank line
    return "\n".join(lines).strip()

def extract_json_block(text: str) -> str:
    # try to grab first {...} JSON block
    m = re.search(r"\{.*\}", text, flags=re.S)
    return m.group(0) if m else "{}"

def parse_json_safe(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        return json.loads(extract_json_block(text) or "{}")

from __future__ import annotations
import csv
import io
from typing import List, Dict, Any
from pathlib import Path
import json
from datetime import datetime, timezone

def rows_to_csv(rows: List[Dict[str, Any]]) -> str:
    # Flatten laws as compact strings for CSV
    def law_str(l):
        parts = [l.get("name",""), l.get("region",""), l.get("article_or_section",""), l.get("source","")]
        return " | ".join([p for p in parts if p])
    buf = io.StringIO()
    fieldnames = ["feature_text", "needs_geo_logic", "reasoning", "laws", "confidence", "rule_hits"]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow({
            "feature_text": r["feature_text"],
            "needs_geo_logic": r["needs_geo_logic"],
            "reasoning": r["reasoning"],
            "laws": "; ".join([law_str(l) for l in r["laws"]]),
            "confidence": r["confidence"],
            "rule_hits": ";".join(r.get("rule_hits", [])),
        })
    return buf.getvalue()


# ---- Lightweight JSONL logging helpers ----
def _resolve_rel_path(rel: str) -> Path:
    """Resolve a repo-relative path like 'data/feedback.jsonl' from api/ runtime.
    Tries as-is, else relative to the project root two levels up from this file.
    """
    p = Path(rel)
    if p.exists() or p.is_absolute():
        return p
    return (Path(__file__).resolve().parents[1] / rel).resolve()

def append_jsonl(rel_path: str, rec: Dict[str, Any]) -> str:
    p = _resolve_rel_path(rel_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return str(p)

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def jsonl_has_record(rel_path: str, key: str, value: Any) -> bool:
    p = _resolve_rel_path(rel_path)
    if not p.exists():
        return False
    try:
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if obj.get(key) == value:
                    return True
    except Exception:
        return False
    return False

def write_json(rel_path: str, obj: Any) -> str:
    """Write a JSON object to a repo-relative path, creating parents.
    Returns the resolved absolute path as a string.
    """
    p = _resolve_rel_path(rel_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return str(p)

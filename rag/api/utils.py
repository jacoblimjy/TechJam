from __future__ import annotations
import csv
import io
from typing import List, Dict, Any

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

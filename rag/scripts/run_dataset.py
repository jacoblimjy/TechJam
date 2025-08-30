#!/usr/bin/env python
from __future__ import annotations
import os, sys, csv, json
from pathlib import Path
from typing import List, Dict, Any

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from rag.chains import make_classify_chain
from rag.heuristics import auto_rule_hits, infer_regions


def law_str(l: Dict[str, Any]) -> str:
    parts = [l.get("name",""), l.get("region",""), l.get("article_or_section",""), l.get("source","")]
    return " | ".join([p for p in parts if p])


def run_dataset(in_csv: str, out_csv: str, out_jsonl: str, k: int = 5, mmr: bool = False, auto_rules: bool = True) -> None:
    rows: List[Dict[str, Any]] = []
    with open(in_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            name = (r.get("feature_name") or "").strip()
            desc = (r.get("feature_description") or r.get("feature_text") or "").strip()
            if not (name or desc):
                continue
            feature_text = f"{name}\n\n{desc}".strip()
            rules = auto_rule_hits(feature_text) if auto_rules else []
            rows.append({"feature_text": feature_text, "rule_hits": rules})

    # Ensure out dir
    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
    Path(out_jsonl).parent.mkdir(parents=True, exist_ok=True)

    with open(out_csv, "w", newline="", encoding="utf-8") as cf, open(out_jsonl, "w", encoding="utf-8") as jf:
        w = csv.writer(cf)
        w.writerow(["feature_text", "needs_geo_logic", "reasoning", "laws", "confidence", "rule_hits"]) 
        for item in rows:
            # Region-aware chain per row
            regs = infer_regions(item["feature_text"]) if auto_rules else None
            chain = make_classify_chain(k=k, mmr=mmr, regions=regs)
            out: Dict[str, Any] = chain.invoke({"feature_text": item["feature_text"], "rule_hits": item["rule_hits"]})
            # JSONL dump for audit
            rec = {
                "feature_text": item["feature_text"],
                "rule_hits": item["rule_hits"],
                **out,
            }
            jf.write(json.dumps(rec, ensure_ascii=False) + "\n")

            # CSV row (flatten laws)
            laws_flat = "; ".join(law_str(l) for l in out.get("laws", []))
            w.writerow([
                item["feature_text"],
                out.get("needs_geo_logic"),
                out.get("reasoning",""),
                laws_flat,
                out.get("confidence", 0.0),
                ";".join(item.get("rule_hits", [])),
            ])

    print(f"✅ Wrote {out_csv} and {out_jsonl}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Run dataset CSV through classifier → outputs.csv + outputs.jsonl")
    ap.add_argument("--in", dest="inp", default="data/test_dataset.csv")
    ap.add_argument("--out_csv", default="data/outputs.csv")
    ap.add_argument("--out_jsonl", default="data/outputs.jsonl")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--mmr", action="store_true")
    ap.add_argument("--no_auto_rules", action="store_true", help="Disable heuristics and send no rule hits")
    args = ap.parse_args()

    run_dataset(
        in_csv=args.inp,
        out_csv=args.out_csv,
        out_jsonl=args.out_jsonl,
        k=args.k,
        mmr=args.mmr,
        auto_rules=not args.no_auto_rules,
    )

from __future__ import annotations
import re
from typing import List, Set

_RULES = [
    # Age-sensitive logic (expanded)
    (
        r"\bASL\b|age[- ]?sensitive|age[- ]?verification|age[- ]?gate|age\s*check|parental\s+consent|"
        r"curfew|night\s*hours|after\s*10:?30\s*(?:pm|p\.m\.)?|before\s*6:?30\s*(?:am|a\.m\.)?|"
        r"under\s*1[38]|minor[s]?",
        "asl",
    ),
    # Geo routing/targeting (expanded synonyms)
    (r"\bGH\b|geo[- ]?handler|geo[- ]?route|geo[- ]?fenc\w*|geofenc\w*|region[- ]specific|EEA|EU/EEA|\bEU\b|European Union", "gh"),
    (r"\bNSP\b|non[- ]shareable policy", "nsp"),
    (r"\bLCP\b|local compliance policy", "lcp"),
    (r"\bEchoTrace\b", "echotrace"),
    (r"\bRedline\b", "redline"),
    (r"\bCDS\b|compliance detection system", "cds"),
    (r"\bDRT\b|data retention", "drt"),
    (r"\bSpanner\b", "spanner"),
    (r"\bSnowcap\b", "snowcap"),
    (r"\bJellybean\b", "jellybean"),
    (r"\bIMT\b|internal monitoring trigger", "imt"),
    (r"\bFR\b|feature rollout", "fr"),
    (r"\bT5\b|high[- ]?risk|sensitive\s+reports|child\s+abuse|NCMEC", "t5"),
    (r"\bPF\b|personalized feed|addictive feed", "pf"),
    (r"\bNR\b|not\s+recommended", "nr"),
    (r"\bSoftblock\b|soft[- ]?block", "softblock"),
    (r"\bShadowMode\b|shadow[- ]?mode", "shadowmode"),
    (r"\bGlow\b", "glow"),
    (r"\bBB\b|baseline\s+behavior", "bb"),
    # Region/law cues (tight word-boundary rules to avoid 'status can' → 'US CA')
    (r"\bUtah\b|\bUS-UT\b|\bUS UT\b|Utah Social Media Regulation Act\b", "utah"),
    (r"\bFlorida\b|\bUS-FL\b|\bUS FL\b|Online Protections for Minors\b", "florida"),
    (r"\bCalifornia\b|\bUS-CA\b|\bUS CA\b|\bSB\s*976\b|Protecting Our Kids", "california"),
    (r"\bEU\b|\bEEA\b|Digital Services Act\b|\bDSA\b|EU/EEA", "eu"),
    (r"\bUS\b|\bFederal\b|2258A|NCMEC|provider[s]?\s+to\s+report", "us_federal"),
]

_COMPILED = [(re.compile(pat, re.I), tag) for pat, tag in _RULES]

def auto_rule_hits(text: str, max_rules: int | None = None) -> List[str]:
    hits: Set[str] = set()
    for rx, tag in _COMPILED:
        if rx.search(text or ""):
            hits.add(tag)
            # Promote a generic legal cue if we see region/law keywords
            if tag in {"utah", "florida", "california", "eu", "us_federal"}:
                hits.add("legal_cue")
        if max_rules and len(hits) >= max_rules:
            break
    return sorted(hits)


def infer_regions(text: str) -> List[str]:
    """Infer region codes from text using rule hits.
    - US state hits include that state and US federal ("US").
    - EU/EEA maps to "EU".
    - Explicit federal cues add "US".
    Order is preserved and duplicates removed.
    """
    tags = set(auto_rule_hits(text))
    regions: List[str] = []
    state_hit = False
    if "utah" in tags:
        regions.append("US-UT"); state_hit = True
    if "florida" in tags:
        regions.append("US-FL"); state_hit = True
    if "california" in tags:
        regions.append("US-CA"); state_hit = True
    if "eu" in tags:
        regions.append("EU")
    if "us_federal" in tags or state_hit:
        if "US" not in regions:
            regions.append("US")
    seen = set()
    out: List[str] = []
    for r in regions:
        if r not in seen:
            seen.add(r); out.append(r)
    return out

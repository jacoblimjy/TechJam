#!/usr/bin/env python
from __future__ import annotations
import os, sys
from pathlib import Path

def parse_pdf_to_text(pdf_path: str) -> str:
    p = Path(pdf_path)
    assert p.exists(), f"PDF not found: {p}"
    text = ""
    # Try docling
    try:
        from docling.document_converter import DocumentConverter  # type: ignore
        conv = DocumentConverter()
        res = conv.convert(str(p))
        text = getattr(res, "text", None) or getattr(res, "plaintext", None) or ""
        if not text and hasattr(res, "document"):
            try:
                text = res.document.export_to_text()
            except Exception:
                pass
    except Exception:
        text = ""
    if text:
        return text
    # Fallback to pypdf
    try:
        from pypdf import PdfReader  # type: ignore
        reader = PdfReader(str(p))
        parts = []
        for page in reader.pages:
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                continue
        return "\n\n".join(parts).strip()
    except Exception as e:
        raise RuntimeError(f"Failed to extract text: {e}")


def main():
    if len(sys.argv) < 3:
        print("Usage: parse_pdf_to_txt.py input.pdf output.txt", file=sys.stderr)
        sys.exit(2)
    inp, outp = sys.argv[1], sys.argv[2]
    text = parse_pdf_to_text(inp)
    Path(outp).parent.mkdir(parents=True, exist_ok=True)
    Path(outp).write_text(text, encoding="utf-8")
    print(f"✅ Wrote {outp} ({len(text)} chars)")

if __name__ == "__main__":
    main()


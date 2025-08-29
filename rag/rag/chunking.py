from __future__ import annotations
import os, re, uuid, csv, json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

# --------- File helpers ---------

def _read_text_file(p: Path) -> str:
    with p.open("r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def _normalize_text(s: str, normalize_newlines=True, collapse_whitespace=True) -> str:
    if normalize_newlines:
        s = s.replace("\r\n", "\n").replace("\r", "\n")
    if collapse_whitespace:
        s = re.sub(r"\n{3,}", "\n\n", s)
        s = re.sub(r"[ \t]{2,}", " ", s)
    return s.strip()

def _load_manifest(csv_path: Optional[str]) -> Dict[str, Dict[str, str]]:
    mapping: Dict[str, Dict[str, str]] = {}
    if not csv_path or not os.path.exists(csv_path):
        return mapping
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = Path(row["file_path"]).name
            mapping[key] = {
                "law_name": row.get("law_name") or "",
                "region": row.get("region") or "",
                "article_or_section": row.get("article_or_section") or "",
                "source": row.get("source") or "",
            }
    return mapping

def _guess_meta_from_filename(name: str) -> Dict[str, str]:
    base = name.lower()
    region = ""
    if "eu" in base: region = "EU"
    elif "california" in base or "sb976" in base or "_ca" in base: region = "US-CA"
    elif "florida" in base or "hb3" in base or "_fl" in base: region = "US-FL"
    elif "utah" in base or "_ut" in base: region = "US-UT"
    elif "usc" in base or "us_code" in base: region = "US"
    return {
        "law_name": Path(name).stem.replace("_", " ").title(),
        "region": region,
        "article_or_section": "",
        "source": "",
    }

# --------- Core splitters ---------

def _is_reference_header(meta: dict) -> bool:
    """
    True if any header contains 'reference' (case-insensitive).
    """
    header_text = " ".join([meta.get("h1",""), meta.get("h2",""), meta.get("h3","")]).lower()
    return "reference" in header_text  # matches 'reference' or 'references'

def header_first_then_recursive(
    text: str,
    source_path: str,
    headers: List[Tuple[str, str]],
    max_header_chunk_chars: int,
    recursive_chunk_chars: int,
    recursive_overlap_chars: int,
    skip_reference_sections: bool = True,
) -> List[Document]:
    """
    1) Split by Markdown headers (H1/H2/H3)
    2) Any resulting piece > max_header_chunk_chars → recursively split
    3) Optionally skip sections where headers contain 'reference(s)'
    """
    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers, strip_headers=False)
    docs = splitter.split_text(text)

    out_docs: List[Document] = []
    big_chunks: List[Document] = []

    for d in docs:
        content = d.page_content
        meta = d.metadata.copy()
        meta["source_path"] = source_path
        meta.setdefault("h1", meta.get("Header 1", ""))
        meta.setdefault("h2", meta.get("Header 2", ""))
        meta.setdefault("h3", meta.get("Header 3", ""))
        for k in ["Header 1", "Header 2", "Header 3"]:
            meta.pop(k, None)

        if skip_reference_sections and _is_reference_header(meta):
            continue

        if len(content) <= max_header_chunk_chars:
            out_docs.append(Document(page_content=content, metadata=meta))
        else:
            big_chunks.append(Document(page_content=content, metadata=meta))

    if big_chunks:
        rec = RecursiveCharacterTextSplitter(
            chunk_size=recursive_chunk_chars,
            chunk_overlap=recursive_overlap_chars,
            separators=["\n\n", "\n", " ", ""],
            length_function=len,
            is_separator_regex=False,
        )
        for bc in big_chunks:
            # carry the same header meta; still skip if it was a reference section
            if skip_reference_sections and _is_reference_header(bc.metadata):
                continue
            for sub in rec.split_documents([bc]):
                out_docs.append(sub)

    return out_docs

# --------- Pipeline ---------

def chunk_directory(
    raw_dir: str,
    headers: List[Tuple[str, str]],
    max_header_chunk_chars: int,
    recursive_chunk_chars: int,
    recursive_overlap_chars: int,
    manifest_csv: Optional[str] = None,
    skip_reference_sections: bool = True,
) -> List[Document]:
    raw_path = Path(raw_dir)
    assert raw_path.exists(), f"raw_dir not found: {raw_dir}"

    manifest = _load_manifest(manifest_csv)

    all_docs: List[Document] = []
    for p in sorted(raw_path.glob("**/*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in (".txt", ".md", ".markdown"):
            continue

        text = _normalize_text(_read_text_file(p))
        if not text:
            continue

        docs = header_first_then_recursive(
            text=text,
            source_path=str(p),
            headers=headers,
            max_header_chunk_chars=max_header_chunk_chars,
            recursive_chunk_chars=recursive_chunk_chars,
            recursive_overlap_chars=recursive_overlap_chars,
            skip_reference_sections=skip_reference_sections,
        )

        base = p.name
        inferred = manifest.get(base, _guess_meta_from_filename(base))
        for d in docs:
            d.metadata.setdefault("law_name", inferred.get("law_name", ""))
            d.metadata.setdefault("region", inferred.get("region", ""))
            d.metadata.setdefault("article_or_section", inferred.get("article_or_section", ""))
            d.metadata.setdefault("source", inferred.get("source", ""))

        all_docs.extend(docs)

    return all_docs

def export_jsonl_and_meta(docs: List[Document], out_jsonl: str, out_meta_csv: str) -> None:
    Path(out_jsonl).parent.mkdir(parents=True, exist_ok=True)
    Path(out_meta_csv).parent.mkdir(parents=True, exist_ok=True)

    with open(out_jsonl, "w", encoding="utf-8") as jf:
        for d in docs:
            rec = {
                "id": str(uuid.uuid4()),
                "text": d.page_content,
                "metadata": d.metadata,
            }
            jf.write(json.dumps(rec, ensure_ascii=False) + "\n")

    with open(out_meta_csv, "w", newline="", encoding="utf-8") as cf:
        writer = csv.writer(cf)
        writer.writerow(["id","chars","source_path","h1","h2","h3","law_name","region","article_or_section","source"])
        for d in docs:
            rid = str(uuid.uuid4())
            m = d.metadata
            writer.writerow([
                rid, len(d.page_content),
                m.get("source_path",""), m.get("h1",""), m.get("h2",""), m.get("h3",""),
                m.get("law_name",""), m.get("region",""),
                m.get("article_or_section",""), m.get("source",""),
            ])

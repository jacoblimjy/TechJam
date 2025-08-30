
---

# From Guesswork to Governance — Automating Geo-Regulation with LLM

**One-liner:** Paste a product feature (title + description) → the system flags whether **geo-specific compliance logic** is required, **explains why**, and **maps to laws** with **audit-ready** provenance.
**Tech:** FastAPI · LangChain · Groq Llama-3.1-8B-Instant · Qdrant (hybrid search) · BGE-M3 embeddings · Next.js

---

## 🗂 Repository structure

```
TechJam/
├─ rag/                      # Backend + RAG library + scripts
│  ├─ api/                   # FastAPI app, Pydantic schemas, CSV utils
│  │  ├─ app.py
│  │  ├─ schemas.py
│  │  └─ utils.py
│  ├─ rag/                   # LangChain components
│  │  ├─ chains.py           # QA + Classify chains (Groq-backed)
│  │  ├─ prompts.py          # QA / Classify prompts (JSON-safe)
│  │  ├─ retrieval.py        # Qdrant hybrid retriever (BGE-M3 dense+sparse)
│  │  ├─ qdrant_store.py     # Vector store wiring
│  │  ├─ embeddings.py       # BGE-M3 embedding wrapper
│  │  └─ heuristics.py       # Server-side rule hits (regex cues)
│  ├─ scripts/
│  │  ├─ build_chunks.py     # Build header-aware text chunks from raw .txt
│  │  ├─ create_collection.py# Create Qdrant collection (dense + sparse)
│  │  ├─ index_kb.py         # Index chunks.jsonl into Qdrant
│  │  ├─ ask_cli.py          # RAG QA CLI (uses Groq)
│  │  ├─ classify_cli.py     # Classifier CLI (strict JSON)
│  │  └─ run_dataset.py      # Batch classify CSV → outputs.csv (+ .jsonl)
│  └─ data/
│     ├─ kb_raw/             # Put your raw law .txt here
│     ├─ kb_chunks/          # Generated chunks (jsonl + meta.csv)
│     └─ laws_manifest.csv   # Maps file→law name→region→source
└─ web/                      # Next.js frontend (App Router + Tailwind)
   ├─ app/                   # pages: /, /search, /demo
   └─ components/            # AnalyzeBox, ResultCard, BatchPanel, etc.
```

---

## ✅ Prerequisites

* **Python 3.10+** and **Node 18+**
* **Docker** (for Qdrant)
* **Groq API key** (free tier works)
* 2 terminals (one for API, one for Web)

---

## 🔑 Environment variables

Create **TechJam/rag/.env** (backend):

```
# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
RAW_DIR=data/kb_raw
OUT_JSONL=data/kb_chunks/chunks.jsonl
OUT_META_CSV=data/kb_chunks/chunks.meta.csv
MANIFEST_CSV=data/laws_manifest.csv
QDRANT_COLLECTION=laws

# Groq (LLM)
GROQ_API_KEY=YOUR_GROQ_KEY
GROQ_MODEL=llama-3.1-8b-instant
GROQ_TEMPERATURE=0.2

# CORS for the Next.js dev server
CORS_ORIGINS=http://localhost:3000
```

Create **TechJam/web/.env.local** (frontend):

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🧱 Setup (one-time)

```bash
# 1) Start Qdrant (vector DB)
docker run -p 6333:6333 -v $(pwd)/rag/qdrant_storage:/qdrant/storage qdrant/qdrant:latest

# 2) Backend venv + deps
cd TechJam/rag
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

---

## 📚 Build & index the knowledge base (laws)

1. **Prepare raw texts** (already provided in `data/kb_raw/`) and a manifest, e.g.:

`data/laws_manifest.csv`

```
file_path,law_name,region,source
California state law.txt,Protecting Our Kids from Social Media Addiction Act,US-CA,https://...
EU Digital Service Act.txt,Digital Services Act,EU,https://...
Florida state law.txt,Online Protections for Minors,US-FL,https://...
US law on reporting child sexual abuse content to NCMEC -.txt,18 U.S.C. § 2258A - Reporting requirements of providers,US,https://...
Utah state law.txt,Utah Social Media Regulation Act,US-UT,https://...
```

2. **Chunk the raw texts** (header-aware; skips headers containing “references”/“reference”):

```bash
# from TechJam/rag
source .venv/bin/activate
python scripts/build_chunks.py \
  --raw_dir data/kb_raw \
  --out_jsonl data/kb_chunks/chunks.jsonl \
  --out_meta_csv data/kb_chunks/chunks.meta.csv \
  --manifest data/laws_manifest.csv \
  --max_header_chars 4200 \
  --chunk_chars 4000 \
  --overlap_chars 350
```

3. **Create the Qdrant collection** (dense + sparse):

```bash
python scripts/create_collection.py
```

4. **Index chunks into Qdrant**:

```bash
python scripts/index_kb.py \
  --jsonl data/kb_chunks/chunks.jsonl \
  --collection laws \
  --batch 128
```

> Tip: Visit Qdrant dashboard: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

---

## 🔌 Run the backend API

```bash
# from TechJam/rag
source .venv/bin/activate
uvicorn api.app:app --reload --port 8000
```

Endpoints:

* `POST /ask` → grounded QA (RAG)
* `POST /search` → retrieve raw law snippets (debug)
* `POST /classify` → strict JSON verdict + reasoning + laws + provenance
* `POST /batch_classify` → multi-row; returns rows + optional CSV string
* `GET /health` → quick ping

Quick tests:

```bash
# Health
curl -s localhost:8000/health

# Ask (RAG QA)
curl -s -X POST localhost:8000/ask -H 'Content-Type: application/json' \
  -d '{"question":"What does the EU DSA require for content removal transparency?","k":5}' | jq

# Classify (single)
curl -s -X POST localhost:8000/classify -H 'Content-Type: application/json' \
  -d '{"feature_text":"To comply with Utah Social Media Regulation Act, restrict under-18 night access via GH; EchoTrace logs.","rule_hits":["utah","asl","gh","legal_cue"],"k":5}' | jq
```

---

## 🖥️ Run the frontend (Next.js)

```bash
# from TechJam/web
npm i
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local  # ensure API URL matches your backend
npm run dev
# open http://localhost:3000
```

**Pages**

* `/` — Paste/pick feature → Analyze; Download audit JSON; Batch classify → CSV
* `/search` — See retrieved law chunks (auditability)
* `/demo` — “Assume region” what-if sandbox

---

## 🧠 How it works (30-second tour) (WIP)

* **Heuristics** (`rag/heuristics.py`) parse legal cues & internal jargon (GH, ASL, LCP, …).
* **RAG** retrieves law snippets from Qdrant using **BGE-M3 embeddings** (dense + sparse hybrid).
* **LLM classifier** (Groq Llama-3.1-8B-Instant) returns **strict JSON** with:

  ```json
  {
    "needs_geo_logic": "yes|no|unclear",
    "reasoning": "...",
    "laws": [{"name":"...","region":"...","article_or_section":"...","source":"..."}],
    "confidence": 0.0-1.0,
    "provenance": {
      "rules_hit": [...],
      "retrieved_law_ids": [...],
      "metrics": {"elapsed_ms": ..., "model": "...", "k": 5, "retrieved": ...}
    }
  }
  ```
* **Frontend** shows verdict, reasons, law links, and lets you export audit JSON/CSV.

---

## New: Auto-heuristics + Dataset Runner

- API: `POST /classify_auto` — same as `/classify` but server auto-detects `rule_hits` from text using lightweight regex heuristics.

Example curl:

```bash
curl -s -X POST "http://localhost:8000/classify_auto" \
  -H 'Content-Type: application/json' \
  -d '{"feature_text":"Curfew login blocker with ASL and GH for Utah minors ..."}' | jq
```

- Script: run the provided synthetic dataset and produce the required `outputs.csv` (+ a JSONL audit):

```bash
# from TechJam/rag
source .venv/bin/activate
python scripts/run_dataset.py \
  --in data/test_dataset.csv \
  --out_csv data/outputs.csv \
  --out_jsonl data/outputs.jsonl \
  --k 5

# CSV at data/outputs.csv (for submission)
```

`run_dataset.py` concatenates `feature_name + feature_description`, applies heuristics (toggle with `--no_auto_rules`), calls the classifier, and saves both CSV and JSONL.

### Batch auto classify + region override

- API: `POST /batch_classify_auto` — auto-detects rule hits for each row. Optional `regions` overrides inference globally.

Payload example:

```json
{
  "rows": [{"feature_text": "..."}, {"feature_text": "..."}],
  "k": 5,
  "csv": true,
  "regions": ["EU"]
}
```

- UI: Batch panel has an “Assume region” dropdown. If no per-line `rule_hits` are provided, it uses `/batch_classify_auto`; otherwise `/batch_classify`. Both accept the optional `regions` override.

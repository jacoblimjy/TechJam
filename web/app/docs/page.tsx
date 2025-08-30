import FeatureGuide from "@/components/FeatureGuide";
import TermsLegend from "@/components/TermsLegend";

export default function Page() {
  return (
    <main className="space-y-6">
      <section className="card p-5 space-y-3">
        <h2 className="text-lg font-medium">Overview</h2>
        <p className="text-sm text-slate-200">
          Flags when a feature needs geo‑specific compliance logic, explains why, and links to the laws behind the
          decision. Under the hood it uses hybrid retrieval with optional cross‑encoder reranking, a JSON‑strict LLM
          classifier, and rich provenance capture for auditability and human‑in‑the‑loop review.
        </p>
        <ul className="list-disc pl-5 text-sm space-y-1 text-slate-200">
          <li><b>Hybrid retrieval</b>: Qdrant with dense <code>BAAI/bge‑m3</code> + sparse BM25 (<code>FastEmbedSparse</code>), optional MMR for diversity, and pre‑filtering by region.</li>
          <li><b>Cross‑encoder rerank</b>: If enabled (<code>ENABLE_RERANK=true</code>), results are reranked with <code>CrossEncoder</code> (default <code>cross-encoder/ms-marco-MiniLM-L-6-v2</code>); otherwise a lexical fallback scores results.</li>
          <li><b>LLM classification</b>: Groq chat model (<code>GROQ_MODEL</code>, default <code>llama-3.1-8b-instant</code>) runs in JSON mode with strict schema for decision, reasoning, laws, and confidence.</li>
          <li><b>Signals + regions</b>: Lightweight heuristics auto‑detect rule tags (e.g., <code>asl</code>, <code>gh</code>, <code>eu</code>) and infer region codes (<code>US-UT</code>, <code>US</code>, <code>EU</code>).</li>
          <li><b>Provenance</b>: Captures <code>rules_hit</code>, <code>rules_input</code>, retrieved snippets + IDs, inferred regions, whether region filter was used, rerank details, model name, k/mmr, retrieved count, elapsed ms, and a unique <code>request_id</code>.</li>
          <li><b>Confidence calibration</b>: Post‑processing bumps or nudges confidence based on strong cues and whether a region filter was applied; capped to 0.20–0.95 for stability.</li>
          <li><b>Law ingestion</b>: PDF → text (Docling if present, fallback to PyPDF) → chunking → Qdrant hybrid index with region + source metadata; managed under the Laws page.</li>
          <li><b>Feedback loop</b>: Per‑request voting writes to JSONL via <code>/feedback</code>; duplicate submissions for the same <code>request_id</code> are rejected.</li>
        </ul>
      </section>

      <section className="card p-5 space-y-2">
        <h3 className="font-medium">Quick start</h3>
        <ul className="list-disc pl-5 text-sm space-y-1 text-slate-200">
          <li><b>Analyze</b>: Paste one artifact. Optionally add <code>rule_hits</code> tags or leave empty for auto.</li>
          <li><b>Batch</b>: Import a CSV or paste JSON‑lines; run and download CSV results.</li>
          <li><b>Search</b>: Inspect retrieval chunks; adjust <code>k</code> and toggle MMR.</li>
          <li><b>Laws</b>: Upload PDFs with metadata to extend the knowledge base.</li>
        </ul>
      </section>

      <FeatureGuide />

      <section className="card p-5 space-y-3">
        <h3 className="font-medium">Single analysis details</h3>
        <ul className="list-disc pl-5 text-sm space-y-1 text-slate-200">
          <li><b>Auto mode</b>: If no tags are provided, requests go to <code>/classify_auto</code>.</li>
          <li><b>Explicit tags</b>: With tags, requests use <code>/classify</code>. See the signals list under the textbox.</li>
          <li><b>Assume region</b>: Filters retrieval to selected codes. Selecting <code>EU/EEA</code> maps to <code>["EU"]</code>.</li>
          <li><b>Outputs</b>: Decision (YES/NO/UNCLEAR), confidence, laws, and a provenance block.</li>
          <li><b>Audit</b>: Download the full JSON or copy it; send “Looks right/Needs fix” feedback when available.</li>
        </ul>
      </section>

      <section className="card p-5 space-y-3">
        <h3 className="font-medium">Batch classify details</h3>
        <ul className="list-disc pl-5 text-sm space-y-1 text-slate-200">
          <li><b>Input</b>: Paste JSON‑lines or use Import CSV (beside “Assume region”).</li>
          <li><b>CSV columns</b>: <code>feature_text</code> OR <code>feature_name</code> + <code>feature_description</code>; optional <code>rule_hits</code>.</li>
          <li><b>rule_hits format</b>: Separate with commas, semicolons, or spaces. Example: <code>asl, gh</code>.</li>
          <li><b>Auto routing</b>: If every row has empty <code>rule_hits</code>, uses <code>/batch_classify_auto</code>; otherwise <code>/batch_classify</code>.</li>
          <li><b>Result</b>: View JSON preview and <b>Download CSV</b> when done.</li>
        </ul>
        <div className="text-xs text-slate-300">Sample CSV header and rows</div>
        <pre className="text-xs bg-slate-800/70 text-slate-100 border border-white/10 p-2 rounded overflow-auto">
feature_name,feature_description,rule_hits
Curfew login blocker,Blocks late‑night access for under‑18 in Utah,"asl; gh"
Personalized feed default,PF off by default for CA teens,"pf, nr, gh"
        </pre>
      </section>

      <section className="card p-5 space-y-3">
        <h3 className="font-medium">Retrieval debugger</h3>
        <ul className="list-disc pl-5 text-sm space-y-1 text-slate-200">
          <li><b>Query</b>: Test what the retriever surfaces for a prompt.</li>
          <li><b>k</b>: Number of chunks to return; <b>MMR</b> toggles diversity.</li>
          <li><b>Display</b>: Shows law name, region, and article/section with the chunk text.</li>
        </ul>
      </section>

      <section className="card p-5 space-y-3">
        <h3 className="font-medium">Laws knowledge base</h3>
        <ul className="list-disc pl-5 text-sm space-y-1 text-slate-200">
          <li><b>Upload</b>: Provide PDF + metadata: <code>law_name</code>, <code>region</code>, <code>source</code>, optional <code>article_or_section</code>.</li>
          <li><b>Pipeline</b>: Server converts PDF → text, indexes chunks, and lists them under Laws.</li>
          <li><b>Manage</b>: Filter by region, search by name/source, and delete indexed items.</li>
        </ul>
      </section>

      <section className="space-y-2">
        <h3 className="font-medium">Terminology</h3>
        <TermsLegend />
      </section>

      <section className="card p-5 space-y-2">
        <h3 className="font-medium">Configuration</h3>
        <ul className="list-disc pl-5 text-sm space-y-1 text-slate-200">
          <li><b>API base</b>: Set <code>NEXT_PUBLIC_API_URL</code> to point the UI at your API (default <code>http://localhost:8000</code>).</li>
          <li><b>Health</b>: The UI probes <code>/health</code> to show API status.</li>
        </ul>
      </section>
    </main>
  );
}

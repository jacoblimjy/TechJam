import FeatureGuide from "@/components/FeatureGuide";
import TermsLegend from "@/components/TermsLegend";

export default function Page() {
  return (
    <main className="space-y-6">
      <section className="space-y-2">
        <h2 className="text-lg font-medium">Overview</h2>
        <p className="text-sm text-gray-700">
          This app flags whether a feature requires geo‑specific compliance logic, explains why, and links to
          relevant laws. It combines heuristics (to detect signals and regions), hybrid retrieval (Qdrant), and an
          LLM classifier returning strict JSON with audit‑ready provenance.
        </p>
      </section>
      <FeatureGuide />
      <section className="space-y-2">
        <h3 className="font-medium">Terminology</h3>
        <TermsLegend />
      </section>
      <section className="space-y-2">
        <h3 className="font-medium">Pages</h3>
        <ul className="list-disc pl-5 text-sm space-y-1">
          <li><b>Analyze</b>: Paste a single artifact; optionally choose signals; run analysis and export JSON.</li>
          <li><b>Search</b>: Debug retrieval to see which law chunks the model sees.</li>
          <li><b>What‑if</b>: Simulate different assumed regions.</li>
          <li><b>Batch</b>: Classify multiple artifacts at once and download CSV.</li>
          <li><b>Laws</b>: Browse the knowledge base and sources.</li>
        </ul>
      </section>
    </main>
  );
}


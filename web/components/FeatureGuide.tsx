export default function FeatureGuide() {
  return (
    <div className="border rounded-xl p-4 bg-white shadow-sm space-y-3">
      <h3 className="font-medium">How to use this platform</h3>
      <ul className="list-disc pl-5 text-sm space-y-1">
        <li>Paste a feature artifact (title + description) into Analyze.</li>
        <li>Select rule tags if you know them (ASL, GH, NSP). If not, leave empty for auto‑detection.</li>
        <li>Use “Assume region” to constrain retrieval (e.g., EU, US‑UT). Leave unset to infer regions automatically.</li>
        <li>Read the decision: YES/NO/UNCLEAR, with confidence and linked laws.</li>
        <li>Open “Provenance” to see exactly which snippets and signals were used.</li>
      </ul>
      <h4 className="font-medium">Interpretation guide</h4>
      <ul className="list-disc pl-5 text-sm space-y-1">
        <li><b>YES</b>: Feature likely requires geo‑specific compliance logic.</li>
        <li><b>NO</b>: No geo‑specific legal requirement identified in the context.</li>
        <li><b>UNCLEAR</b>: Insufficient information; human review advised.</li>
        <li><b>Confidence</b>: Calibrated 0.20–0.95. Higher when region filters and strong legal cues align.</li>
      </ul>
    </div>
  );
}


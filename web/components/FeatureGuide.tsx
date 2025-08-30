export default function FeatureGuide() {
  return (
    <div className="card p-5 space-y-3">
      <h3 className="font-medium">How to use</h3>
      <ul className="list-disc pl-5 text-sm space-y-1 text-slate-200">
        <li>Paste a feature artifact (title + description) into Analyze.</li>
        <li>Select rule tags if you know them (ASL, GH, NSP), or leave empty to auto‑detect.</li>
        <li>Use “Assume region” to constrain retrieval (EU, US‑UT). Leave unset to auto‑infer.</li>
        <li>See decision, confidence, and linked laws. Expand Provenance for the audit trail.</li>
      </ul>
      <h4 className="font-medium">Interpretation</h4>
      <ul className="list-disc pl-5 text-sm space-y-1 text-slate-200">
        <li><b>YES</b>: Likely needs geo‑specific logic.</li>
        <li><b>NO</b>: No geo‑specific legal requirement found.</li>
        <li><b>UNCLEAR</b>: Needs human review.</li>
        <li><b>Confidence</b>: 0.20–0.95, higher when regions and cues align.</li>
      </ul>
    </div>
  );
}

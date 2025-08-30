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
      <div className="text-sm space-y-2 text-slate-200">
        <div className="flex items-center gap-2">
          <span className="text-white text-[10px] px-2 py-0.5 rounded bg-green-600">YES</span>
          <span>Likely needs geo‑specific logic.</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-white text-[10px] px-2 py-0.5 rounded bg-red-600">NO</span>
          <span>No geo‑specific legal requirement found.</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-white text-[10px] px-2 py-0.5 rounded bg-yellow-600">UNCLEAR</span>
          <span>Needs human review.</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-white text-[10px] px-2 py-0.5 rounded bg-sky-600">Confidence</span>
          <span>0.20–0.95, higher when regions and cues align.</span>
        </div>
      </div>
    </div>
  );
}

"use client";
import { LawChips } from "./LawChips";
import { Badge, CopyButton, InfoTip } from "./Ui";

function DecisionBadge({ v }: { v: string }) {
  const m = (v || "unclear").toLowerCase();
  const bg = m === "yes" ? "bg-green-600" : m === "no" ? "bg-gray-700" : "bg-yellow-600";
  return <span className={`text-white text-xs px-2 py-1 rounded ${bg}`}>{m.toUpperCase()}</span>;
}

function ConfidenceBar({ c }: { c: number }) {
  const pct = Math.max(0, Math.min(100, Math.round((c || 0) * 100)));
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-32 bg-gray-200 rounded">
        <div className="h-2 bg-gray-800 rounded" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-600">{pct}%</span>
    </div>
  );
}

export default function DecisionSummary({ res }: { res: any }) {
  if (!res) return null;
  const prov = res.provenance || {};
  const rules: string[] = prov.rules_hit || [];
  const rulesInput: string[] = prov.rules_input || [];
  const regions: string[] = prov.regions_inferred || [];
  const filterUsed = prov.region_filter_used;
  return (
    <div className="grid md:grid-cols-2 gap-4">
      <div className="border rounded-xl p-4 bg-white shadow-sm space-y-3">
        <div className="flex items-center gap-3">
          <DecisionBadge v={res.needs_geo_logic} />
          <ConfidenceBar c={Number(res.confidence ?? 0)} />
          {regions?.length ? <Badge>regions: {regions.join(", ")}</Badge> : null}
          {typeof filterUsed === "boolean" ? <Badge>filter {filterUsed ? "on" : "off"}</Badge> : null}
        </div>
        <div className="text-sm text-gray-900 whitespace-pre-wrap">{res.reasoning}</div>
        <div className="text-xs text-gray-600 flex items-center gap-1">
          <InfoTip text="Signals the model used to triage. Provided tags are 'rules_input'; detected/union are 'rules_hit'." />
          <span>signals:</span>
          <div className="flex flex-wrap gap-1">
            {(rules.length ? rules : rulesInput).map((r, i) => (
              <span key={i} className="px-1.5 py-0.5 border rounded text-xs bg-gray-50">{r}</span>
            ))}
          </div>
        </div>
        <div className="pt-1">
          <LawChips laws={res.laws || []} />
        </div>
        <div className="flex items-center gap-2">
          <CopyButton text={JSON.stringify(res, null, 2)} label="Copy JSON" />
        </div>
      </div>
      <div className="border rounded-xl p-4 bg-white shadow-sm">
        <details open>
          <summary className="cursor-pointer text-sm text-gray-700">Provenance (audit trail)</summary>
          <pre className="text-xs bg-gray-50 p-2 rounded mt-2 overflow-auto max-h-80">
            {JSON.stringify(prov, null, 2)}
          </pre>
        </details>
      </div>
    </div>
  );
}


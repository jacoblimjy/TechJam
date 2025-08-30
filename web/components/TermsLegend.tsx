const TERMS: { key: string; label: string; desc: string }[] = [
  { key: "NR", label: "Not recommended", desc: "Default policy discouraging overrides." },
  { key: "PF", label: "Personalized feed", desc: "Recommendations driven by user signals." },
  { key: "GH", label: "Geo-handler", desc: "Routes enforcement by region." },
  { key: "CDS", label: "Compliance Detection System", desc: "Audit & escalation backbone." },
  { key: "DRT", label: "Data retention threshold", desc: "Max log retention duration." },
  { key: "LCP", label: "Local compliance policy", desc: "Region-specific constraints." },
  { key: "Redline", label: "Legal review flag", desc: "Escalate to legal review." },
  { key: "Softblock", label: "Silent user-level limit", desc: "No user notification." },
  { key: "Spanner", label: "Rule engine (synthetic)", desc: "Experiment/targeting logic." },
  { key: "ShadowMode", label: "Analytics-only deploy", desc: "No user impact." },
  { key: "T5", label: "Tier 5 sensitive data", desc: "Highest sensitivity signals." },
  { key: "ASL", label: "Age-sensitive logic", desc: "Detect and handle minors." },
  { key: "Glow", label: "Geo-based alert", desc: "Compliance health indicator." },
  { key: "NSP", label: "Non-shareable policy", desc: "Restrict external sharing." },
  { key: "Jellybean", label: "Parental control", desc: "Internal framework name." },
  { key: "EchoTrace", label: "Log tracing mode", desc: "Verify routing & audits." },
  { key: "BB", label: "Baseline behavior", desc: "Reference for anomalies." },
  { key: "Snowcap", label: "Child safety framework", desc: "Underage safety rules." },
  { key: "FR", label: "Feature rollout status", desc: "Rollout flagging & logs." },
  { key: "IMT", label: "Internal monitoring trigger", desc: "Anomaly triggers." },
];

export default function TermsLegend() {
  return (
    <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-3">
      {TERMS.map((t) => (
        <div key={t.key} className="border rounded-lg p-3 bg-white">
          <div className="text-sm font-medium">{t.key} — {t.label}</div>
          <div className="text-xs text-gray-600">{t.desc}</div>
        </div>
      ))}
    </div>
  );
}


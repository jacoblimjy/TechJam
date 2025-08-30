"use client";
import { useEffect, useMemo, useState } from "react";
import { API } from "@/components/api";

type Law = { file_path: string; law_name: string; region: string; source: string; article_or_section?: string };

export default function Page() {
  const [laws, setLaws] = useState<Law[]>([]);
  const [q, setQ] = useState("");
  const [region, setRegion] = useState("");

  useEffect(() => {
    fetch(`${API}/laws`).then(r => r.json()).then(j => setLaws(j.laws || [])).catch(() => setLaws([]));
  }, []);

  const regions = useMemo(() => {
    const s = new Set(laws.map(l => l.region).filter(Boolean));
    return Array.from(s).sort();
  }, [laws]);

  const filtered = laws.filter(l => {
    const okRegion = region ? l.region === region : true;
    const okText = q ? (l.law_name?.toLowerCase().includes(q.toLowerCase()) || l.source?.toLowerCase().includes(q.toLowerCase())) : true;
    return okRegion && okText;
  });

  return (
    <main className="space-y-4">
      <h2 className="text-lg font-medium">Laws in knowledge base</h2>
      <div className="flex items-center gap-3">
        <input className="input h-9" placeholder="Search law name or source..." value={q} onChange={e => setQ(e.target.value)} />
        <select className="select" value={region} onChange={e => setRegion(e.target.value)}>
          <option value="">All regions</option>
          {regions.map(r => <option key={r} value={r}>{r}</option>)}
        </select>
        <span className="text-xs text-slate-200">{filtered.length} items</span>
      </div>
      <div className="grid md:grid-cols-2 gap-3">
        {filtered.map((l, i) => (
          <div key={i} className="card p-3">
            <div className="text-sm font-medium text-slate-100">{l.law_name}</div>
            <div className="text-xs text-slate-300">{l.region} · {l.file_path}</div>
            <a href={l.source} target="_blank" className="text-xs underline break-all">{l.source}</a>
          </div>
        ))}
      </div>
    </main>
  );
}

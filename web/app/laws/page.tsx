"use client";
import { useEffect, useMemo, useState } from "react";
import { API } from "@/components/api";

type Law = { file_path: string; law_name: string; region: string; source: string; article_or_section?: string };

export default function Page() {
  const [laws, setLaws] = useState<Law[]>([]);
  const [q, setQ] = useState("");
  const [region, setRegion] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [lawName, setLawName] = useState("");
  const [lawRegion, setLawRegion] = useState("");
  const [source, setSource] = useState("");
  const [article, setArticle] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

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
      <div className="card p-4 space-y-2">
        <div className="text-sm font-medium">Add new law (PDF → txt → index)</div>
        {msg && <div className="text-xs text-slate-200">{msg}</div>}
        <div className="grid md:grid-cols-2 gap-3">
          <div className="space-y-2">
            <input type="file" accept="application/pdf" className="input" onChange={e => setFile(e.target.files?.[0] || null)} />
            <input className="input" placeholder="Law name" value={lawName} onChange={e => setLawName(e.target.value)} />
            <input className="input" placeholder="Region code (e.g., US-UT, EU)" value={lawRegion} onChange={e => setLawRegion(e.target.value)} />
          </div>
          <div className="space-y-2">
            <input className="input" placeholder="Source URL" value={source} onChange={e => setSource(e.target.value)} />
            <input className="input" placeholder="Article/section (optional)" value={article} onChange={e => setArticle(e.target.value)} />
            <button
              className="btn-primary"
              disabled={!file || !lawName || !lawRegion || loading}
              onClick={async () => {
                try {
                  setLoading(true); setMsg(null);
                  const fd = new FormData();
                  if (file) fd.append("file", file);
                  fd.append("law_name", lawName);
                  fd.append("region", lawRegion);
                  fd.append("source", source);
                  fd.append("article_or_section", article);
                  const r = await fetch(`${API}/laws/upload`, { method: "POST", body: fd });
                  if (!r.ok) throw new Error(await r.text());
                  const j = await r.json();
                  setMsg(`Uploaded: ${j.txt_file}, indexed chunks: ${j.indexed_chunks}`);
                  const list = await fetch(`${API}/laws`).then(res => res.json());
                  setLaws(list.laws || []);
                  setFile(null); setLawName(""); setLawRegion(""); setSource(""); setArticle("");
                } catch (e: any) {
                  setMsg(e.message || String(e));
                } finally {
                  setLoading(false);
                }
              }}
            >
              {loading ? "Processing..." : "Upload & Index"}
            </button>
          </div>
        </div>
      </div>
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
            <div className="mt-2 flex gap-2">
              <button
                className="btn-danger text-xs px-2 py-1"
                onClick={async () => {
                  if (!confirm(`Delete ${l.law_name}? This will remove the index, manifest row, and source txt.`)) return;
                  try {
                    const r = await fetch(`${API}/laws/delete`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ file_path: l.file_path }),
                    });
                    if (!r.ok) throw new Error(await r.text());
                    const list = await fetch(`${API}/laws`).then(res => res.json());
                    setLaws(list.laws || []);
                  } catch (e) {
                    alert((e as any).message || String(e));
                  }
                }}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}

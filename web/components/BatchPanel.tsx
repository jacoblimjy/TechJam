"use client";
import { useRef, useState } from "react";
import { postJSON } from "./api";
import { Badge } from "./Ui";

export default function BatchPanel() {
	const [rows, setRows] = useState<string>("");
	const [csv, setCsv] = useState<string | null>(null);
	const [out, setOut] = useState<any>(null);
	const [loading, setLoading] = useState(false);
  const [assume, setAssume] = useState<string | null>(null);

  const REGIONS = ["EU/EEA", "US-CA", "US-UT", "US-FL", "US"];
  function mapAssumeToCodes(v: string | null): string[] | null {
    if (!v) return null;
    if (v === "EU/EEA") return ["EU"];
    return [v];
  }

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // --- CSV import helpers (handles basic quoted CSV) ---
  function parseCsvRow(line: string): string[] {
    const out: string[] = [];
    let cur = "";
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (ch === '"') {
        // handle escaped quotes ""
        if (inQuotes && i + 1 < line.length && line[i + 1] === '"') {
          cur += '"'; i++; continue;
        }
        inQuotes = !inQuotes;
      } else if (ch === "," && !inQuotes) {
        out.push(cur); cur = "";
      } else {
        cur += ch;
      }
    }
    out.push(cur);
    return out.map(s => s.trim().replace(/^"|"$/g, ""));
  }

  function parseCsvText(text: string): { feature_text: string; rule_hits: string[] }[] {
    const lines = text.split(/\r?\n/);
    const rows: string[] = [];
    let buf = "";
    const pushIfComplete = () => {
      const q = (buf.match(/"/g) || []).length;
      if (q % 2 === 0) { rows.push(buf); buf = ""; }
    };
    for (const raw of lines) {
      if (!buf) { buf = raw; } else { buf += "\n" + raw; }
      pushIfComplete();
    }
    if (buf) rows.push(buf);
    if (!rows.length) return [];
    const header = parseCsvRow(rows[0]).map(h => h.toLowerCase().trim());
    const idxName = header.indexOf("feature_name");
    const idxDesc = header.indexOf("feature_description");
    const idxText = header.indexOf("feature_text");
    const idxRules = header.indexOf("rule_hits");
    const out: { feature_text: string; rule_hits: string[] }[] = [];
    for (let i = 1; i < rows.length; i++) {
      const cols = parseCsvRow(rows[i]);
      if (!cols.length || cols.every(c => !c.trim())) continue;
      let ft = "";
      if (idxText >= 0 && cols[idxText]) {
        ft = cols[idxText];
      } else if (idxName >= 0 || idxDesc >= 0) {
        const name = idxName >= 0 ? (cols[idxName] || "") : "";
        const desc = idxDesc >= 0 ? (cols[idxDesc] || "") : "";
        ft = [name, desc].filter(Boolean).join("\n\n");
      } else {
        // fallback: join all columns
        ft = cols.join(", ");
      }
      const rh = idxRules >= 0 && cols[idxRules] ? String(cols[idxRules]).split(/[;,\s]+/).filter(Boolean) : [];
      if (ft.trim()) out.push({ feature_text: ft.trim(), rule_hits: rh });
    }
    return out;
  }

  async function importCsv(file: File) {
    const text = await file.text();
    const rowsParsed = parseCsvText(text);
    if (!rowsParsed.length) return;
    // Populate the textarea with JSON lines so users can review/edit
    const jsonl = rowsParsed.map(r => JSON.stringify(r)).join("\n");
    setRows(jsonl);
  }

  function triggerCsvPicker() {
    fileInputRef.current?.click();
  }

  async function handleCsvPicked(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] || null;
    if (file) {
      await importCsv(file);
    }
    // reset so picking same file twice still fires change
    e.target.value = "";
  }

	function parseRows(): { feature_text: string; rule_hits: string[] }[] {
		const lines = rows
			.split("\n")
			.map((l) => l.trim())
			.filter(Boolean);
		return lines.map((l) => {
			try {
				const obj = JSON.parse(l);
				return {
					feature_text: obj.feature_text || l,
					rule_hits: obj.rule_hits || [],
				};
			} catch {
				return { feature_text: l, rule_hits: [] };
			}
		});
	}

	async function runBatch() {
		setLoading(true);
		setCsv(null);
		setOut(null);
		try {
			const rowsParsed = parseRows();
			const allEmpty = rowsParsed.every((r) => !r.rule_hits || r.rule_hits.length === 0);
			const regions = mapAssumeToCodes(assume);
			const payload = { rows: rowsParsed, k: 5, csv: true, regions } as any;
			const path = allEmpty ? "/batch_classify_auto" : "/batch_classify";
			const res = await postJSON<any>(path, payload);
			setOut(res.rows);
			setCsv(res.csv || null);
		} catch (e: any) {
			alert(e.message || String(e));
		} finally {
			setLoading(false);
		}
	}

	function downloadCSV() {
		if (!csv) return;
		const blob = new Blob([csv], { type: "text/csv" });
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = "outputs.csv";
		a.click();
		URL.revokeObjectURL(url);
	}

	return (
		<div className="card p-5 space-y-3">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <h3 className="font-medium">Batch Classify</h3>
                </div>
                <div className="flex items-center gap-2">
                    {/* Hidden file input for CSV import */}
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".csv,text/csv"
                      className="hidden"
                      onChange={handleCsvPicked}
                    />
                    <button className="btn btn-compact" onClick={triggerCsvPicker}>Import CSV</button>
                    <span className="text-xs text-slate-300">Assume region</span>
                    <select className="select" value={assume || ""} onChange={(e) => setAssume(e.target.value || null)}>
                        <option value="">None</option>
                        {REGIONS.map((r) => (
                            <option key={r} value={r}>{r}</option>
                        ))}
                    </select>
                </div>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-200">
              <Badge>Auto mode</Badge>
              <span>One artifact per line. Leave rule_hits empty to auto‑detect.</span>
            </div>
            <div className="text-xs text-slate-300">CSV with columns: feature_text OR feature_name + feature_description (optional: rule_hits)</div>
            <textarea
                className="input h-40"
                placeholder={`One artifact per line.\nEither raw text or JSON per line: {"feature_text":"...", "rule_hits":["asl","gh"]}`}
                value={rows}
                onChange={(e) => setRows(e.target.value)}
            />
			<div className="flex gap-2">
			<button onClick={runBatch} className="btn-primary" disabled={loading || rows.trim().length === 0}>
				{loading ? "Running..." : "Batch classify"}
			</button>
            {csv && (
                <button onClick={downloadCSV} className="btn-accent">
                    Download CSV
                </button>
            )}
			</div>

			{out && (
				<div className="space-y-2">
					<div className="text-xs text-slate-200">{out.length} rows</div>
					<pre className="text-xs bg-slate-800/70 text-slate-100 border border-white/10 p-2 rounded overflow-auto max-h-80 backdrop-blur">
						{JSON.stringify(out, null, 2)}
					</pre>
				</div>
			)}
		</div>
	);
}

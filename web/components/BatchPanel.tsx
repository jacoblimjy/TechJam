"use client";
import { useState } from "react";
import { postJSON } from "./api";

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
					<h3 className="font-medium">Batch classify</h3>
					<span className="text-xs text-slate-300">One artifact per line. Leave rule_hits out to auto‑detect.</span>
				</div>
				<div className="flex items-center gap-2">
					<span className="text-xs text-slate-300">Assume region</span>
					<select className="select" value={assume || ""} onChange={(e) => setAssume(e.target.value || null)}>
						<option value="">None</option>
						{REGIONS.map((r) => (
							<option key={r} value={r}>{r}</option>
						))}
					</select>
				</div>
			</div>
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
					<button onClick={downloadCSV} className="btn">
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

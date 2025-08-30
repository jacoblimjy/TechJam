"use client";
import { useState } from "react";
import { postJSON } from "./api";
import { InfoTip } from "./Ui";

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
			<div className="flex items-center gap-2">
				<h3 className="font-medium">Batch classify</h3>
				<InfoTip text="One artifact per line. Leave rule_hits out to auto-detect. Use the region selector to constrain jurisdictions." />
			</div>
			<div className="flex items-center gap-2">
				<span className="text-sm text-gray-500">Assume region:</span>
				<select
					className="select"
					value={assume || ""}
					onChange={(e) => setAssume(e.target.value || null)}
				>
					<option value="">None</option>
					{REGIONS.map((r) => (
						<option key={r} value={r}>
							{r}
						</option>
					))}
				</select>
			</div>
			<textarea
				className="w-full h-40 border rounded-xl p-3"
				placeholder={`One artifact per line.\nEither raw text or JSON per line: {"feature_text":"...", "rule_hits":["asl","gh"]}`}
				value={rows}
				onChange={(e) => setRows(e.target.value)}
			/>
			<div className="flex gap-2">
			<button onClick={runBatch} className="btn-primary" disabled={loading}>
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
					<div className="text-xs text-gray-600">{out.length} rows</div>
					<pre className="text-xs bg-gray-50 p-2 rounded overflow-auto max-h-80">
						{JSON.stringify(out, null, 2)}
					</pre>
				</div>
			)}
		</div>
	);
}

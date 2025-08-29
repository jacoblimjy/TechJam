"use client";
import { useState } from "react";
import { postJSON } from "./api";

export default function BatchPanel() {
	const [rows, setRows] = useState<string>("");
	const [csv, setCsv] = useState<string | null>(null);
	const [out, setOut] = useState<any>(null);
	const [loading, setLoading] = useState(false);

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
			const payload = { rows: parseRows(), k: 5, csv: true };
			const res = await postJSON<any>("/batch_classify", payload);
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
		<div className="space-y-3">
			<textarea
				className="w-full h-40 border rounded-xl p-3"
				placeholder={`One artifact per line.\nEither raw text or {"feature_text":"...", "rule_hits":["asl","gh"]}`}
				value={rows}
				onChange={(e) => setRows(e.target.value)}
			/>
			<div className="flex gap-2">
				<button
					onClick={runBatch}
					className="px-4 py-2 rounded-lg bg-black text-white"
					disabled={loading}
				>
					{loading ? "Running..." : "Batch classify"}
				</button>
				{csv && (
					<button onClick={downloadCSV} className="px-4 py-2 rounded-lg border">
						Download CSV
					</button>
				)}
			</div>

			{out && (
				<pre className="text-xs bg-gray-50 p-2 rounded overflow-auto max-h-80">
					{JSON.stringify(out, null, 2)}
				</pre>
			)}
		</div>
	);
}

"use client";
import { useState } from "react";
import { postJSON } from "./api";
import { InfoTip } from "./Ui";

export default function SearchBox() {
	const [q, setQ] = useState("");
	const [docs, setDocs] = useState<any[] | null>(null);
  const [k, setK] = useState(5);
  const [mmr, setMmr] = useState(false);

	async function onSearch() {
		const res = await postJSON<any>("/search", { query: q, k, mmr });
		setDocs(res.docs || []);
	}

	return (
		<div className="card p-5 space-y-3">
			<div className="flex items-center gap-2">
				<h3 className="font-medium">Retrieval debugger</h3>
				<InfoTip text="Preview which law chunks are retrieved for a query. Helps explain what the model sees before answering." />
			</div>
			<input
				className="w-full border rounded-lg p-2"
				placeholder="Type a query to test retrieval..."
				value={q}
				onChange={(e) => setQ(e.target.value)}
			/>
			<div className="flex items-center gap-3 text-sm">
				<label className="flex items-center gap-1">
					<span>k</span>
					<input type="number" value={k} min={1} max={20} className="w-16 border rounded px-2 py-1"
						onChange={(e) => setK(Number(e.target.value) || 5)} />
				</label>
				<label className="flex items-center gap-1">
					<input type="checkbox" checked={mmr} onChange={(e) => setMmr(e.target.checked)} />
					<span>MMR (diversify)</span>
				</label>
			</div>
			<button onClick={onSearch} className="btn-primary">
				Search
			</button>
			{docs && (
				<div className="space-y-3">
					{docs.map((d, i) => (
						<div key={i} className="border rounded-lg p-3">
							<div className="text-xs text-gray-500 mb-1">
								{d.metadata?.law_name} · {d.metadata?.region} ·{" "}
								{d.metadata?.article_or_section}
							</div>
							<div className="text-sm whitespace-pre-wrap">{d.content}</div>
						</div>
					))}
				</div>
			)}
		</div>
	);
}

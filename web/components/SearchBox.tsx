"use client";
import { useState } from "react";
import { postJSON } from "./api";

export default function SearchBox() {
	const [q, setQ] = useState("");
	const [docs, setDocs] = useState<any[] | null>(null);

	async function onSearch() {
		const res = await postJSON<any>("/search", { query: q, k: 5 });
		setDocs(res.docs || []);
	}

	return (
		<div className="space-y-3">
			<input
				className="w-full border rounded-lg p-2"
				placeholder="Type a query to test retrieval..."
				value={q}
				onChange={(e) => setQ(e.target.value)}
			/>
			<button
				onClick={onSearch}
				className="px-4 py-2 rounded-lg bg-black text-white"
			>
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

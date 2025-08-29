"use client";
import { useMemo, useState } from "react";
import { postJSON } from "./api";
import { ResultCard } from "./ResultCard";
import clsx from "clsx";

const REGIONS = ["EU/EEA", "US-CA", "US-UT", "US-FL", "US"];

export default function AnalyzeBox() {
	const [text, setText] = useState("");
	const [rules, setRules] = useState<string[]>([]);
	const [loading, setLoading] = useState(false);
	const [res, setRes] = useState<any>(null);
	const [error, setError] = useState<string | null>(null);
	const [assume, setAssume] = useState<string | null>(null);

	const payloadText = useMemo(() => {
		if (!assume) return text;
		return `${text}\n\n[Assumption: operating in ${assume}]`;
	}, [text, assume]);

	async function onAnalyze() {
		setError(null);
		setLoading(true);
		setRes(null);
		try {
			const out = await postJSON<any>("/classify", {
				feature_text: payloadText,
				rule_hits: rules,
			});
			setRes(out);
		} catch (e: any) {
			setError(e.message || String(e));
		} finally {
			setLoading(false);
		}
	}

	function onRuleToggle(tag: string) {
		setRules((prev) =>
			prev.includes(tag) ? prev.filter((x) => x !== tag) : [...prev, tag]
		);
	}

	function downloadJSON() {
		if (!res) return;
		const blob = new Blob([JSON.stringify(res, null, 2)], {
			type: "application/json",
		});
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = "audit.json";
		a.click();
		URL.revokeObjectURL(url);
	}

	return (
		<div className="space-y-4">
			<textarea
				className="w-full h-48 border rounded-xl p-3 focus:outline-none"
				placeholder="Paste feature artifact (title + description)..."
				value={text}
				onChange={(e) => setText(e.target.value)}
			/>
			<div className="flex flex-wrap gap-2 items-center">
				{["legal_cue", "asl", "gh", "lcp", "nsp", "echotrace", "redline"].map(
					(t) => (
						<button
							key={t}
							onClick={() => onRuleToggle(t)}
							className={clsx(
								"text-xs px-2 py-1 rounded-full border",
								rules.includes(t)
									? "bg-black text-white border-black"
									: "bg-white"
							)}
						>
							{t}
						</button>
					)
				)}
				<div className="ml-auto flex items-center gap-2">
					<span className="text-sm text-gray-500">Assume region:</span>
					<select
						className="border rounded px-2 py-1 text-sm"
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
			</div>

			<div className="flex gap-2">
				<button
					onClick={onAnalyze}
					disabled={!text || loading}
					className="px-4 py-2 rounded-lg bg-black text-white disabled:opacity-50"
				>
					{loading ? "Analyzing..." : "Analyze"}
				</button>
				{res && (
					<button
						onClick={downloadJSON}
						className="px-4 py-2 rounded-lg border"
					>
						Download audit JSON
					</button>
				)}
			</div>

			{error && <div className="text-sm text-red-600">{error}</div>}
			{res && <ResultCard res={res} />}
		</div>
	);
}

"use client";
import { useMemo, useState } from "react";
import { postJSON } from "./api";
import DecisionSummary from "./DecisionSummary";
import { Badge } from "./Ui";
import clsx from "clsx";

const REGIONS = ["EU/EEA", "US-CA", "US-UT", "US-FL", "US"];

function mapAssumeToCodes(v: string | null): string[] | null {
  if (!v) return null;
  if (v === "EU/EEA") return ["EU"];
  return [v];
}

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
			const path = rules.length ? "/classify" : "/classify_auto";
			const regions = mapAssumeToCodes(assume);
			const body = rules.length
				? { feature_text: payloadText, rule_hits: rules, regions }
				: { feature_text: payloadText, regions };
			const out = await postJSON<any>(path, body);
			setRes(out);
		} catch (e: any) {
			setError(e.message || String(e));
		} finally {
			setLoading(false);
		}
	}

	function setExample(kind: string) {
		if (kind === "utah") {
			setText("Curfew login blocker with ASL and GH for Utah minors\n\nTo comply with the Utah Social Media Regulation Act, we are implementing a curfew-based login restriction for users under 18. GH applies enforcement within Utah only.");
			setAssume("US-UT");
			setRules(["asl", "gh"]);
		} else if (kind === "dsa") {
			setText("Content visibility lock with NSP for EU DSA\n\nA soft Softblock applies to NSP-tagged content, restricted to EU region via GH.");
			setAssume("EU/EEA");
			setRules(["nsp", "gh"]);
		} else if (kind === "fl") {
			setText("Jellybean-based parental notifications for Florida regulation\n\nExtend parental notifications per Florida minors protections; IMT checks anomalies, BB models, and CDS logs.");
			setAssume("US-FL");
			setRules(["jellybean", "gh"]);
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
		<div className="card p-5 space-y-4">
			<div className="flex items-center justify-between">
				<h2 className="text-lg font-medium">Single artifact analysis</h2>
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
        <div className="flex items-center gap-2 text-xs text-slate-200">
          <Badge>Auto mode</Badge>
          <span>no tags selected → auto‑detect rules</span>
        </div>
			<textarea
				className="input h-48"
				placeholder="e.g., Curfew login blocker with ASL and GH for Utah minors..."
				value={text}
				onChange={(e) => setText(e.target.value)}
			/>
				<div className="space-y-2">
					<div className="text-xs text-slate-200">Sample rule tags:</div>
					<div className="flex flex-wrap gap-2 items-center">
						{["legal_cue", "asl", "gh", "lcp", "nsp", "echotrace", "redline"].map(
							(t) => (
								<button
									key={t}
									onClick={() => onRuleToggle(t)}
									className={clsx("chip", rules.includes(t) ? "chip-active" : "chip-muted")}
								>
									{t}
								</button>
							)
						)}
					</div>
					<div className="card p-3">
						<div className="text-xs text-slate-100 mb-1">Quick fill examples</div>
						<div className="flex flex-wrap gap-3 text-xs">
							<button className="btn" onClick={() => setExample("utah")}>Utah minors (ASL + GH)</button>
							<button className="btn" onClick={() => setExample("dsa")}>EU DSA NSP</button>
							<button className="btn" onClick={() => setExample("fl")}>Florida Jellybean</button>
							<button className="btn" onClick={() => { setText(""); setRules([]); setAssume(null); setRes(null); }}>Reset</button>
						</div>
					</div>
				</div>

			<div className="flex gap-2">
				<button
					onClick={onAnalyze}
						disabled={!text.trim() || loading}
					className="btn-primary"
				>
					{loading ? "Analyzing..." : "Analyze"}
				</button>
            {res && (
                <button onClick={downloadJSON} className="btn-accent">
                    Download audit JSON
                </button>
            )}
			</div>

			{error && <div className="text-sm text-red-600">{error}</div>}
			{res && <DecisionSummary res={res} />}
		</div>
	);
}

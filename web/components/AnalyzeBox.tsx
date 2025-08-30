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
            setText(
                "Curfew login blocker with ASL and GH for Utah minors\n\n" +
                "To comply with the Utah Social Media Regulation Act, we are implementing a curfew-based login restriction for users under 18. " +
                "The system uses ASL to detect minor accounts and routes enforcement through GH to apply only within Utah boundaries. " +
                "The feature activates during restricted night hours and logs activity using EchoTrace for auditability. " +
                "This allows parental control to be enacted without user-facing alerts, operating in ShadowMode during initial rollout."
            );
            setAssume("US-UT");
            setRules(["asl", "gh"]);
        } else if (kind === "ca_pf") {
            setText(
                "PF default toggle with NR enforcement for California teens\n\n" +
                "As part of compliance with California’s SB976, the app will disable PF by default for users under 18 located in California. " +
                "This default setting is considered NR to override, unless explicit parental opt-in is provided. " +
                "Geo-detection is handled via GH, and rollout is monitored with FR logs. " +
                "The design ensures minimal disruption while meeting the strict personalization requirements imposed by the law."
            );
            setAssume("US-CA");
            setRules(["pf", "nr", "gh"]);
        } else if (kind === "story") {
            setText(
                "Story resharing with content expiry\n\n" +
                "Enable users to reshare stories from others, with auto-expiry after 48 hours. " +
                "This feature logs resharing attempts with EchoTrace and stores activity under BB."
            );
            setAssume(null);
            setRules([]);
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
                <h2 className="text-lg font-medium">Single Artifact Analysis</h2>
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
          <span>Leave rule_hits empty to auto‑detect.</span>
        </div>
			<textarea
				className="input h-48"
				placeholder="e.g., Curfew login blocker with ASL and GH for Utah minors..."
				value={text}
				onChange={(e) => setText(e.target.value)}
			/>
				<div className="space-y-2">
                    <div className="text-xs text-slate-200">Sample rule_hits tags:</div>
                    <div className="flex flex-wrap gap-2 items-center">
                        {["legal_cue",
                          "asl","gh","nsp","lcp","echotrace","redline",
                          "cds","drt","spanner","snowcap","jellybean","imt","fr",
                          "t5","pf","nr","softblock","shadowmode","glow","bb",
                          "utah","florida","california","eu","us_federal"
                        ].map(
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
                            <button className="btn" onClick={() => setExample("utah")}>Utah curfew (ASL + GH)</button>
                            <button className="btn" onClick={() => setExample("ca_pf")}>California SB976 PF (NR)</button>
                            <button className="btn" onClick={() => setExample("story")}>Story resharing + expiry</button>
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

import { LawChips } from "./LawChips";

export function ResultCard({ res }: { res: any }) {
	if (!res) return null;
	const badge =
		res.needs_geo_logic === "yes"
			? "bg-green-600"
			: res.needs_geo_logic === "no"
			? "bg-gray-600"
			: "bg-yellow-600";

	return (
		<div className="border rounded-xl p-4 bg-white shadow-sm">
			<div className="flex items-center gap-2">
				<span className={`text-white text-xs px-2 py-1 rounded ${badge}`}>
					{res.needs_geo_logic?.toUpperCase() || "UNCLEAR"}
				</span>
				<span className="text-xs text-gray-500">
					confidence: {Number(res.confidence ?? 0).toFixed(2)}
				</span>
				{res?.provenance?.regions_inferred?.length ? (
					<span className="text-xs text-gray-500">
						regions: {res.provenance.regions_inferred.join(", ")}
					</span>
				) : null}
				{typeof res?.provenance?.region_filter_used === "boolean" ? (
					<span className="text-xs px-2 py-0.5 rounded bg-gray-100">
						filter {res.provenance.region_filter_used ? "on" : "off"}
					</span>
				) : null}
			</div>
			<p className="mt-3 text-sm">{res.reasoning}</p>
			<LawChips laws={res.laws || []} />
			<details className="mt-3">
				<summary className="cursor-pointer text-sm text-gray-600">
					Provenance
				</summary>
				<pre className="text-xs bg-gray-50 p-2 rounded mt-2 overflow-auto">
					{JSON.stringify(res.provenance || {}, null, 2)}
				</pre>
			</details>
		</div>
	);
}

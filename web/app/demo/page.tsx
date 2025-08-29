"use client";
import AnalyzeBox from "@/components/AnalyzeBox";

export default function Page() {
	return (
		<main className="space-y-4">
			<h2 className="text-lg font-medium">What-if sandbox</h2>
			<p className="text-sm text-gray-600">
				Use the “Assume region” dropdown to simulate operating in a region.
			</p>
			<AnalyzeBox />
		</main>
	);
}

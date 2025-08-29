import AnalyzeBox from "@/components/AnalyzeBox";
import BatchPanel from "@/components/BatchPanel";

export default function Page() {
	return (
		<main className="space-y-8">
			<AnalyzeBox />
			<section>
				<h2 className="text-lg font-medium mb-2">Batch classify</h2>
				<BatchPanel />
			</section>
		</main>
	);
}

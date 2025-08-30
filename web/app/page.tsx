import AnalyzeBox from "@/components/AnalyzeBox";
import BatchPanel from "@/components/BatchPanel";
import FeatureGuide from "@/components/FeatureGuide";

export default function Page() {
    return (
        <main className="space-y-8">
            <div className="grid lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                    <section className="space-y-2">
                        <AnalyzeBox />
                    </section>
                    <section className="space-y-2">
                        <h2 className="text-lg font-medium">Batch classify</h2>
                        <BatchPanel />
                    </section>
                </div>
                <aside className="space-y-3">
                    <FeatureGuide />
                </aside>
            </div>
        </main>
    );
}

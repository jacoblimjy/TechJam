import "./globals.css";
export const metadata = {
	title: "Geo-Compliance Detector",
	description: "LLM-RAG + heuristics for geo regulations",
};
import ApiStatus from "@/components/ApiStatus";
import { Plus_Jakarta_Sans } from "next/font/google";

const jakarta = Plus_Jakarta_Sans({ subsets: ["latin"], weight: ["400","500","600","700"], variable: "--font-jakarta" });

export default function RootLayout({
	children,
}: {
	children: React.ReactNode;
}) {
	return (
		<html lang="en" className={jakarta.variable}>
			<body className="font-sans" style={{ fontFamily: "var(--font-jakarta)" }}>
				<div className="max-w-6xl mx-auto p-6">
					<header className="mb-6">
						<div className="rounded-2xl p-5 bg-white/70 border border-white/40 shadow-card backdrop-blur">
							<div className="flex items-center justify-between">
								<h1 className="text-2xl font-semibold bg-clip-text text-transparent bg-brand-gradient">Geo-Compliance Detector</h1>
								<ApiStatus />
							</div>
							<p className="text-sm text-gray-700 mt-1">
								Flag features needing geo‑specific logic. Clear reasoning, linked laws, and audit‑ready provenance.
							</p>
							<nav className="mt-3 flex flex-wrap gap-2 text-sm">
								<a className="px-3 py-1 rounded-full border bg-white/70 backdrop-blur hover:shadow" href="/">Analyze</a>
								<a className="px-3 py-1 rounded-full border bg-white/70 backdrop-blur hover:shadow" href="/search">Search</a>
								<a className="px-3 py-1 rounded-full border bg-white/70 backdrop-blur hover:shadow" href="/demo">What‑if</a>
								<a className="px-3 py-1 rounded-full border bg-white/70 backdrop-blur hover:shadow" href="/laws">Laws</a>
								<a className="px-3 py-1 rounded-full border bg-white/70 backdrop-blur hover:shadow" href="/docs">Docs</a>
							</nav>
						</div>
					</header>
					{children}
				</div>
			</body>
		</html>
	);
}

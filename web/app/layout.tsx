import "./globals.css";
export const metadata = {
	title: "Geo-Compliance Detector",
	description: "LLM-RAG + heuristics for geo regulations",
};

export default function RootLayout({
	children,
}: {
	children: React.ReactNode;
}) {
	return (
		<html lang="en">
			<body>
				<div className="max-w-5xl mx-auto p-6">
					<header className="mb-6">
						<h1 className="text-2xl font-semibold">Geo-Compliance Detector</h1>
						<p className="text-sm text-gray-600">
							Flag features needing geo-specific logic with reasoning & law
							links.
						</p>
						<nav className="mt-3 flex gap-4 text-sm">
							<a className="underline" href="/">
								Analyze
							</a>
							<a className="underline" href="/search">
								Search
							</a>
							<a className="underline" href="/demo">
								What-if sandbox
							</a>
						</nav>
					</header>
					{children}
				</div>
			</body>
		</html>
	);
}

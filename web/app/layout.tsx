import "./globals.css";
export const metadata = {
  title: "TriBit's Geo-Compliance Detector",
  description: "LLM‑RAG + heuristics for geo regulations",
};
import ApiStatus from "@/components/ApiStatus";
import NavBar from "@/components/NavBar";
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
            <div className="rounded-2xl p-5 bg-slate-900/60 border border-white/10 shadow-card backdrop-blur">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-amber-400/10 border border-amber-300/40 shadow-[0_0_24px_rgba(251,191,36,0.28)]">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M12 2l8 4v6c0 5-3.4 9.4-8 10-4.6-.6-8-5-8-10V6l8-4z" stroke="url(#gold)" strokeWidth="1.5" fill="rgba(251,191,36,0.10)"/>
                      <path d="M8 11l2.8 2.8L16 8.6" stroke="url(#gold)" strokeWidth="1.7" strokeLinecap="round"/>
                      <defs>
                        <linearGradient id="gold" x1="0" y1="0" x2="24" y2="24" gradientUnits="userSpaceOnUse">
                          <stop stopColor="#fbbf24"/>
                          <stop offset="0.55" stopColor="#f59e0b"/>
                          <stop offset="1" stopColor="#b45309"/>
                        </linearGradient>
                      </defs>
                    </svg>
                  </span>
                  <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-grand-title-dark drop-shadow-[0_0_16px_rgba(245,158,11,0.38)]">
                    TriBIT's Geo-Compliance Detector
                  </h1>
                </div>
                <ApiStatus />
              </div>
              <p className="text-sm text-slate-200 mt-2">
                Flag features needing geo‑specific logic. Clear reasoning, linked laws, and audit‑ready provenance.
              </p>
              <NavBar />
            </div>
          </header>
          {children}
        </div>
      </body>
    </html>
	);
}

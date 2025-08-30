"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const items = [
  { href: "/", label: "Analyze" },
  { href: "/search", label: "Search" },
  { href: "/demo", label: "What‑if" },
  { href: "/laws", label: "Laws" },
  { href: "/help", label: "Help" },
];

export default function NavBar() {
  const path = usePathname() || "/";
  return (
    <nav className="mt-4 flex flex-wrap gap-2 text-sm">
      {items.map((it) => {
        const active = path === it.href;
        const base = "inline-flex items-center justify-center h-9 px-4 rounded-xl text-center whitespace-nowrap leading-none";
        const cls = active
          ? `${base} bg-sky-500/20 text-sky-200 border border-sky-400/30 shadow ring-1 ring-sky-400/25`
          : `${base} border bg-slate-800/60 text-slate-100 border-white/10 backdrop-blur hover:bg-slate-700/60 hover:border-white/20 hover:shadow transition`;
        return (
          <Link key={it.href} href={it.href} className={cls}>
            {it.label}
          </Link>
        );
      })}
    </nav>
  );
}

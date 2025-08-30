export function LawChips({ laws }: { laws: any[] }) {
    if (!laws?.length) return null;
    return (
        <div className="flex flex-wrap gap-2 mt-2">
            {laws.map((l, i) => (
                <a
                    key={i}
                    href={l.source || "#"}
                    target="_blank"
                    className="text-xs px-2 py-1 rounded-full border bg-slate-800/60 text-slate-100 border-white/10 backdrop-blur hover:bg-slate-700/60"
                >
                    {l.name}
                    {l.region ? ` · ${l.region}` : ""}
                    {l.article_or_section ? ` · ${l.article_or_section}` : ""}
                </a>
            ))}
        </div>
    );
}

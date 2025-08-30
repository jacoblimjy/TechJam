"use client";
import { useEffect, useState } from "react";
import { API } from "./api";

export default function ApiStatus() {
  const [ok, setOk] = useState<boolean | null>(null);
  useEffect(() => {
    let cancelled = false;
    async function ping() {
      try {
        const r = await fetch(`${API}/health`);
        const j = await r.json();
        if (!cancelled) setOk(Boolean(j?.ok));
      } catch {
        if (!cancelled) setOk(false);
      }
    }
    ping();
    const id = setInterval(ping, 5000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);
  const color = ok == null ? "bg-gray-300" : ok ? "bg-green-500" : "bg-red-500";
  const label = ok == null ? "checking" : ok ? "API online" : "API offline";
  return (
    <span className="inline-flex items-center gap-1 text-xs text-slate-300" title={label}>
      <span className={`inline-block w-2 h-2 rounded-full ${color}`} />
      {label}
    </span>
  );
}

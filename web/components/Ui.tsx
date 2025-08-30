"use client";
import { useState } from "react";

export function InfoTip({ text }: { text: string }) {
  return (
    <span
      title={text}
      className="inline-flex items-center justify-center w-4 h-4 text-[10px] rounded-full bg-slate-700/70 text-slate-100 cursor-help align-middle border border-white/10"
    >
      i
    </span>
  );
}

export function Badge({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center text-xs px-2 py-0.5 rounded bg-slate-800/60 text-slate-100 border border-white/10">
      {children}
    </span>
  );
}

export function CopyButton({ text, label = "Copy" }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);
  async function onCopy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch {}
  }
  return (
    <button onClick={onCopy} className="btn-accent text-xs px-2 py-1">
      {copied ? "Copied" : label}
    </button>
  );
}

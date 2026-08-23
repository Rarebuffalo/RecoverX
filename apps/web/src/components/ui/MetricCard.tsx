import React from "react";
import clsx from "clsx";

interface MetricCardProps {
  label: string;
  value: string;
  subtext?: string;
  change?: string;
  changeType?: "positive" | "negative" | "neutral";
  isSynthetic?: boolean;
  icon?: React.ReactNode;
}

export function MetricCard({
  label,
  value,
  subtext,
  change,
  changeType = "neutral",
  isSynthetic = false,
  icon,
}: MetricCardProps) {
  return (
    <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-5 relative overflow-hidden transition-all hover:border-slate-700 shadow-sm">
      {isSynthetic && (
        <div className="absolute top-3 right-3 text-[9px] uppercase tracking-wider font-semibold px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
          Synthetic Benchmark
        </div>
      )}

      <div className="flex items-center justify-between text-slate-400 mb-3">
        <span className="text-xs font-semibold uppercase tracking-wider">{label}</span>
        {icon && <div className="text-slate-400">{icon}</div>}
      </div>

      <div className="text-2xl lg:text-3xl font-bold tracking-tight text-white mb-2 font-mono">
        {value}
      </div>

      {(subtext || change) && (
        <div className="flex items-center gap-2 text-xs">
          {change && (
            <span
              className={clsx(
                "font-semibold px-1.5 py-0.5 rounded text-[11px]",
                changeType === "positive" && "bg-emerald-500/10 text-emerald-400",
                changeType === "negative" && "bg-rose-500/10 text-rose-400",
                changeType === "neutral" && "bg-slate-700/50 text-slate-300"
              )}
            >
              {change}
            </span>
          )}
          {subtext && <span className="text-slate-400 truncate">{subtext}</span>}
        </div>
      )}
    </div>
  );
}

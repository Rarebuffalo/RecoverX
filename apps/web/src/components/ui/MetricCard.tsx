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
    <div className="bg-white border border-slate-200 rounded-xl p-5 relative overflow-hidden transition-all hover:border-slate-300 shadow-xs">
      {isSynthetic && (
        <div className="absolute top-3 right-3 text-[9px] uppercase tracking-wider font-semibold px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">
          Synthetic Benchmark
        </div>
      )}

      <div className="flex items-center justify-between text-slate-500 mb-3">
        <span className="text-xs font-semibold uppercase tracking-wider">{label}</span>
        {icon && <div className="text-slate-400">{icon}</div>}
      </div>

      <div className="text-2xl lg:text-3xl font-bold tracking-tight text-slate-900 mb-2 font-mono">
        {value}
      </div>

      {(subtext || change) && (
        <div className="flex items-center gap-2 text-xs">
          {change && (
            <span
              className={clsx(
                "font-semibold px-1.5 py-0.5 rounded text-[11px]",
                changeType === "positive" && "bg-emerald-50 text-emerald-700 border border-emerald-200",
                changeType === "negative" && "bg-rose-50 text-rose-700 border border-rose-200",
                changeType === "neutral" && "bg-slate-100 text-slate-700 border border-slate-200"
              )}
            >
              {change}
            </span>
          )}
          {subtext && <span className="text-slate-500 truncate">{subtext}</span>}
        </div>
      )}
    </div>
  );
}

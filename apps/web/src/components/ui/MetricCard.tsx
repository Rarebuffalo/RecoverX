import React from "react";
import clsx from "clsx";

interface MetricCardProps {
  label: string;
  value: string;
  subtext?: string;
  change?: string;
  changeType?: "positive" | "negative" | "neutral";
  badge?: string;
  isSynthetic?: boolean;
  icon?: React.ReactNode;
}

export function MetricCard({
  label,
  value,
  subtext,
  change,
  changeType = "neutral",
  badge,
  isSynthetic = false,
  icon,
}: MetricCardProps) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 flex flex-col justify-between transition-all hover:border-slate-300 shadow-xs space-y-3">
      {/* Header Row: Title & Optional Badge/Icon (Non-colliding flex layout) */}
      <div className="flex items-start justify-between gap-2 min-h-[26px]">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 leading-snug flex-1">
          {label}
        </span>
        {badge ? (
          <span className="shrink-0 text-[10px] font-mono uppercase font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
            {badge}
          </span>
        ) : isSynthetic ? (
          <span className="shrink-0 text-[9px] uppercase font-mono tracking-wider font-semibold px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">
            Synthetic
          </span>
        ) : icon ? (
          <div className="shrink-0 text-slate-400">{icon}</div>
        ) : null}
      </div>

      {/* Primary Value */}
      <div className="text-2xl lg:text-3xl font-bold tracking-tight text-slate-900 font-mono">
        {value}
      </div>

      {/* Supporting Context Row */}
      {(subtext || change) && (
        <div className="flex items-center gap-2 text-xs flex-wrap">
          {change && (
            <span
              className={clsx(
                "font-semibold px-1.5 py-0.5 rounded text-[11px] font-mono",
                changeType === "positive" && "bg-emerald-50 text-emerald-700 border border-emerald-200",
                changeType === "negative" && "bg-rose-50 text-rose-700 border border-rose-200",
                changeType === "neutral" && "bg-slate-100 text-slate-700 border border-slate-200"
              )}
            >
              {change}
            </span>
          )}
          {subtext && <span className="text-slate-500 text-[11px] truncate">{subtext}</span>}
        </div>
      )}
    </div>
  );
}


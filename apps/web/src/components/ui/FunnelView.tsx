import React from "react";
import { ArrowRight, CheckCircle, TrendingUp } from "lucide-react";

interface FunnelStage {
  label: string;
  count: string | number;
  amount?: string;
  rate?: string;
  color: string;
}

interface FunnelViewProps {
  stages: FunnelStage[];
}

export function FunnelView({ stages }: FunnelViewProps) {
  return (
    <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            End-to-End Recovery Funnel
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Causal conversion tracking across detection, policy gating, and settlement
          </p>
        </div>
        <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
          Deterministic Flow
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-3 relative">
        {stages.map((stage, idx) => (
          <div
            key={idx}
            className="bg-[#162032]/60 border border-[#1e293b] rounded-xl p-4 flex flex-col justify-between relative overflow-hidden transition-all hover:border-slate-700"
          >
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2">
              0{idx + 1}. {stage.label}
            </div>

            <div className="space-y-1">
              <div className="text-xl lg:text-2xl font-bold font-mono text-white">
                {typeof stage.count === "number" ? stage.count.toLocaleString() : stage.count}
              </div>
              {stage.amount && (
                <div className="text-xs font-semibold text-emerald-400 font-mono">
                  {stage.amount}
                </div>
              )}
            </div>

            {stage.rate && (
              <div className="mt-3 pt-2 border-t border-slate-700/40 text-[11px] text-slate-400 flex items-center justify-between">
                <span>Conversion</span>
                <span className="font-semibold text-slate-200">{stage.rate}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

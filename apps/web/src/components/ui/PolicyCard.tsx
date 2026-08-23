import React from "react";
import { ShieldCheck, ShieldAlert, Sparkles, CheckCircle2, AlertOctagon } from "lucide-react";
import clsx from "clsx";

interface PolicyCardProps {
  decision: "ALLOW" | "BLOCK" | "ESCALATE";
  effectiveAction: string;
  policyVersion: string;
  threshold: number;
  maxAmountCap: number;
  retryLimit: number;
  reasonCodes: string[];
  humanReadableSummary: string;
  aiRecommendation?: string;
  aiConfidence?: number;
  decisionFactors?: string[];
}

export function PolicyCard({
  decision,
  effectiveAction,
  policyVersion,
  threshold,
  maxAmountCap,
  retryLimit,
  reasonCodes,
  humanReadableSummary,
  aiRecommendation,
  aiConfidence,
  decisionFactors,
}: PolicyCardProps) {
  const isAllowed = decision === "ALLOW";
  const isBlocked = decision === "BLOCK";

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* 1. AI Recommendation Box (Untrusted Advisory Proposal) */}
      <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-5 relative overflow-hidden">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2 text-xs font-bold text-purple-400 uppercase tracking-wider">
            <Sparkles className="w-4 h-4" />
            <span>AI Diagnostic Proposal</span>
          </div>
          <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
            Advisory Only
          </span>
        </div>

        <div className="space-y-3">
          <div>
            <div className="text-[11px] text-slate-400">Proposed Action</div>
            <div className="text-sm font-semibold text-slate-200 font-mono">
              {aiRecommendation || "CREATE_RECOVERY_PAYMENT_LINK"}
            </div>
          </div>

          {aiConfidence !== undefined && (
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400">Model Diagnostic Confidence</span>
                <span className="font-mono text-purple-300 font-semibold">
                  {(aiConfidence * 100).toFixed(0)}%
                </span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-purple-500 h-1.5 rounded-full"
                  style={{ width: `${aiConfidence * 100}%` }}
                />
              </div>
            </div>
          )}

          {decisionFactors && decisionFactors.length > 0 && (
            <div>
              <div className="text-[11px] text-slate-400 mb-1.5">Observed Signals</div>
              <ul className="space-y-1">
                {decisionFactors.map((factor, idx) => (
                  <li key={idx} className="text-xs text-slate-300 flex items-center gap-2">
                    <span className="w-1 h-1 rounded-full bg-purple-400" />
                    <span>{factor}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* 2. Deterministic Policy Gate (Financial Authority) */}
      <div
        className={clsx(
          "border rounded-xl p-5 relative overflow-hidden",
          isAllowed && "bg-[#0c1f17] border-emerald-500/30",
          isBlocked && "bg-[#1f0e13] border-rose-500/30",
          decision === "ESCALATE" && "bg-[#1e1528] border-purple-500/30"
        )}
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-200 uppercase tracking-wider">
            {isAllowed ? (
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            ) : (
              <ShieldAlert className="w-4 h-4 text-rose-400" />
            )}
            <span>Deterministic Policy Gate</span>
          </div>
          <span
            className={clsx(
              "text-xs font-bold px-2.5 py-0.5 rounded font-mono border",
              isAllowed && "bg-emerald-500/15 text-emerald-300 border-emerald-500/40",
              isBlocked && "bg-rose-500/15 text-rose-300 border-rose-500/40",
              decision === "ESCALATE" && "bg-purple-500/15 text-purple-300 border-purple-500/40"
            )}
          >
            DECISION: {decision}
          </span>
        </div>

        <div className="space-y-2.5 text-xs">
          <div className="grid grid-cols-3 gap-2 py-2 border-y border-slate-700/40 font-mono text-[11px]">
            <div>
              <span className="text-slate-400 block text-[10px]">THRESHOLD</span>
              <span className="font-semibold text-slate-200">{threshold}/100</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">MAX CAP</span>
              <span className="font-semibold text-slate-200">₹{maxAmountCap.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">MAX RETRIES</span>
              <span className="font-semibold text-slate-200">{retryLimit} attempts</span>
            </div>
          </div>

          <div>
            <div className="text-[11px] text-slate-400">Enforced Action</div>
            <div className="text-xs font-bold text-slate-100 font-mono">{effectiveAction}</div>
          </div>

          <div className="p-2.5 rounded-lg bg-black/30 border border-white/5 text-slate-300 leading-relaxed text-xs">
            {humanReadableSummary}
          </div>
        </div>
      </div>
    </div>
  );
}

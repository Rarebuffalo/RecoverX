import React from "react";
import clsx from "clsx";
import { CheckCircle2, Clock, AlertTriangle, XCircle, ArrowRight } from "lucide-react";

interface StateMachineProps {
  currentStatus: string;
}

const states = [
  { key: "PENDING", label: "Pending" },
  { key: "AUTHORIZED", label: "Authorized" },
  { key: "EXECUTING", label: "Executing" },
  { key: "SUCCEEDED", label: "Succeeded" },
];

export function StateMachine({ currentStatus }: StateMachineProps) {
  const norm = currentStatus.toUpperCase();

  const isAmbiguous = norm === "AMBIGUOUS";
  const isFailed = norm === "FAILED" || norm === "ACTION_FAILED" || norm === "CANCELLED";

  const getStepIndex = () => {
    switch (norm) {
      case "PENDING":
      case "DETECTED":
        return 0;
      case "AUTHORIZED":
      case "EVALUATING":
      case "POLICY_GATING":
        return 1;
      case "EXECUTING":
      case "INTERVENED":
        return 2;
      case "SUCCEEDED":
      case "RECOVERED":
      case "PROVIDER_CONFIRMED":
        return 3;
      default:
        return 2;
    }
  };

  const activeIndex = getStepIndex();

  return (
    <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Financial Execution State Machine
        </span>
        <div className="flex items-center gap-2">
          {isAmbiguous ? (
            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 text-xs font-semibold border border-amber-500/30">
              <AlertTriangle className="w-3.5 h-3.5" />
              AMBIGUOUS: Verification Required
            </span>
          ) : isFailed ? (
            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 text-xs font-semibold border border-rose-500/30">
              <XCircle className="w-3.5 h-3.5" />
              EXECUTION TERMINATED
            </span>
          ) : (
            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-xs font-semibold border border-emerald-500/30">
              <CheckCircle2 className="w-3.5 h-3.5" />
              State Protected
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-4 gap-2 relative">
        {states.map((step, idx) => {
          const isPassed = idx < activeIndex;
          const isCurrent = idx === activeIndex && !isAmbiguous && !isFailed;
          const isPending = idx > activeIndex;

          return (
            <div
              key={step.key}
              className={clsx(
                "relative rounded-lg p-3 border text-center transition-all",
                isPassed && "bg-emerald-950/20 border-emerald-500/40 text-emerald-300",
                isCurrent && "bg-blue-950/30 border-blue-500 text-blue-200 ring-1 ring-blue-500 shadow-md",
                isPending && "bg-[#162032]/40 border-[#1f2937] text-slate-400 opacity-60"
              )}
            >
              <div className="text-[10px] font-mono uppercase text-slate-400 mb-1">
                Step 0{idx + 1}
              </div>
              <div className="text-xs font-bold">{step.label}</div>
            </div>
          );
        })}
      </div>

      {isAmbiguous && (
        <div className="mt-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-200 text-xs flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-amber-300">Bounded Execution Safety Guard: </span>
            The gateway encountered an unconfirmed network state. RecoverX has held the action in{" "}
            <code className="bg-amber-950/60 px-1 py-0.5 rounded font-mono">AMBIGUOUS</code> to
            prevent double charging. Automatic retries are paused until provider reconciliation.
          </div>
        </div>
      )}
    </div>
  );
}

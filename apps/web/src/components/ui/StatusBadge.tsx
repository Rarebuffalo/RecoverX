import React from "react";
import clsx from "clsx";

interface StatusBadgeProps {
  status: string;
  size?: "sm" | "md";
}

export function StatusBadge({ status, size = "sm" }: StatusBadgeProps) {
  const normalized = status.toUpperCase();

  const getStyle = () => {
    switch (normalized) {
      case "RECOVERED":
      case "SUCCEEDED":
      case "ALLOW":
      case "PAID":
      case "CAPTURED":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";

      case "INTERVENED":
      case "EXECUTING":
      case "EVALUATING":
      case "SCORING":
      case "AUTHORIZED":
      case "QUEUED":
        return "bg-blue-500/10 text-blue-400 border-blue-500/30";

      case "AMBIGUOUS":
      case "PENDING":
      case "RETRY_PENDING":
      case "DETECTED":
        return "bg-amber-500/10 text-amber-400 border-amber-500/30";

      case "ESCALATED":
      case "CUSTOMER_ACTION_REQUIRED":
        return "bg-purple-500/10 text-purple-400 border-purple-500/30";

      case "BLOCK":
      case "FAILED":
      case "ACTION_FAILED":
      case "CLOSED_UNRECOVERED":
      case "CANCELLED":
      case "EXPIRED":
        return "bg-rose-500/10 text-rose-400 border-rose-500/30";

      default:
        return "bg-slate-800 text-slate-300 border-slate-700";
    }
  };

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 font-semibold font-mono uppercase tracking-wider rounded-md border",
        size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs",
        getStyle()
      )}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-80" />
      {normalized.replace(/_/g, " ")}
    </span>
  );
}

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
        return "bg-emerald-50 text-emerald-700 border-emerald-200";

      case "INTERVENED":
      case "EXECUTING":
      case "EVALUATING":
      case "SCORING":
      case "AUTHORIZED":
      case "QUEUED":
        return "bg-blue-50 text-blue-700 border-blue-200";

      case "AMBIGUOUS":
      case "PENDING":
      case "RETRY_PENDING":
      case "DETECTED":
        return "bg-amber-50 text-amber-700 border-amber-200";

      case "ESCALATED":
      case "CUSTOMER_ACTION_REQUIRED":
        return "bg-purple-50 text-purple-700 border-purple-200";

      case "BLOCK":
      case "FAILED":
      case "ACTION_FAILED":
      case "CLOSED_UNRECOVERED":
      case "CANCELLED":
      case "EXPIRED":
        return "bg-rose-50 text-rose-700 border-rose-200";

      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
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
      <span>{normalized.replace("_", " ")}</span>
    </span>
  );
}

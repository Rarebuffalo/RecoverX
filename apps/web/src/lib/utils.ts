/**
 * RecoverX Financial Formatting & Utility Module
 */

export function formatINR(amount: number | string | null | undefined): string {
  if (amount === null || amount === undefined || isNaN(Number(amount))) {
    return "₹0";
  }
  const numericAmount = Math.round(Number(amount));
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
    minimumFractionDigits: 0,
  }).format(numericAmount);
}

export function formatCompactINR(amount: number | string | null | undefined): string {
  if (amount === null || amount === undefined || isNaN(Number(amount))) {
    return "₹0";
  }
  const num = Number(amount);
  if (num >= 10000000) {
    return `₹${(num / 10000000).toFixed(2)} Cr`;
  }
  if (num >= 100000) {
    return `₹${(num / 100000).toFixed(2)} Lakh`;
  }
  if (num >= 1000) {
    return `₹${(num / 1000).toFixed(1)}k`;
  }
  return formatINR(num);
}

export function formatDate(isoString: string | null | undefined): string {
  if (!isoString) return "—";
  try {
    const d = new Date(isoString);
    return new Intl.DateTimeFormat("en-IN", {
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    }).format(d);
  } catch {
    return isoString;
  }
}

export function formatRelativeTime(isoString: string | null | undefined): string {
  if (!isoString) return "just now";
  try {
    const diffMs = Date.now() - new Date(isoString).getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    if (diffMins < 1) return "just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  } catch {
    return "recently";
  }
}

export function getStatusBadgeConfig(status: string) {
  const s = (status || "").toUpperCase();
  switch (s) {
    case "RECOVERED":
    case "SUCCEEDED":
    case "PAID":
      return {
        label: "RECOVERED",
        className: "bg-emerald-50 text-emerald-700 border-emerald-200",
        dotClassName: "bg-emerald-500",
      };
    case "DETECTED":
    case "NEW":
      return {
        label: "DETECTED",
        className: "bg-blue-50 text-blue-700 border-blue-200",
        dotClassName: "bg-blue-500",
      };
    case "DIAGNOSED":
    case "POLICY APPROVED":
    case "APPROVED":
      return {
        label: "POLICY APPROVED",
        className: "bg-indigo-50 text-indigo-700 border-indigo-200",
        dotClassName: "bg-indigo-500",
      };
    case "INTERVENED":
    case "DISPATCHED":
    case "EXECUTING":
      return {
        label: "DISPATCHED",
        className: "bg-sky-50 text-sky-700 border-sky-200",
        dotClassName: "bg-sky-500",
      };
    case "ESCALATED":
    case "MANUAL_REVIEW":
      return {
        label: "ESCALATED",
        className: "bg-amber-50 text-amber-700 border-amber-200",
        dotClassName: "bg-amber-500",
      };
    case "AMBIGUOUS":
    case "HELD":
      return {
        label: "AMBIGUOUS / HELD",
        className: "bg-orange-50 text-orange-700 border-orange-200",
        dotClassName: "bg-orange-500",
      };
    case "CLOSED_UNRECOVERED":
    case "BLOCKED":
    case "FAILED":
      return {
        label: "BLOCKED",
        className: "bg-rose-50 text-rose-700 border-rose-200",
        dotClassName: "bg-rose-500",
      };
    default:
      return {
        label: s || "UNKNOWN",
        className: "bg-slate-50 text-slate-700 border-slate-200",
        dotClassName: "bg-slate-500",
      };
  }
}

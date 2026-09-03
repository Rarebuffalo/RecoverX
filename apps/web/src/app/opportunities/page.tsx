"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Zap,
  Search,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  HelpCircle,
  XCircle,
  Eye,
  ShieldCheck,
  BrainCircuit,
  Filter,
} from "lucide-react";
import { fetchOpportunities } from "@/lib/api";
import { RecoveryOpportunity } from "@/lib/types";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { formatINR } from "@/lib/utils";
import clsx from "clsx";

const tabs = [
  { id: "ALL", label: "All Cases" },
  { id: "AT_RISK", label: "At Risk" },
  { id: "NEEDS_REVIEW", label: "Needs Review" },
  { id: "APPROVED", label: "Approved" },
  { id: "RECOVERING", label: "Recovering" },
  { id: "RECOVERED", label: "Recovered" },
  { id: "BLOCKED", label: "Blocked" },
];

export default function OpportunitiesWorkQueuePage() {
  const [opportunities, setOpportunities] = useState<RecoveryOpportunity[]>([]);
  const [activeTab, setActiveTab] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchOpportunities();
        if (data) setOpportunities(data);
      } catch (e) {
        console.error("Failed to load opportunities queue", e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filtered = opportunities.filter((opp) => {
    const customer = opp.order?.customer?.name?.toLowerCase() || "";
    const email = opp.order?.customer?.email?.toLowerCase() || "";
    const reason = (opp.order?.payment_attempts?.[0]?.failure_reason || opp.failure_category || "").toLowerCase();
    const id = opp.id.toLowerCase();
    const q = searchQuery.toLowerCase();

    const matchesSearch = !q || customer.includes(q) || email.includes(q) || reason.includes(q) || id.includes(q);
    if (!matchesSearch) return false;

    if (activeTab === "ALL") return true;
    if (activeTab === "AT_RISK") return opp.status === "DETECTED" || !opp.status;
    if (activeTab === "NEEDS_REVIEW") return opp.status === "ESCALATED" || (opp.revenue_at_risk_inr ?? 0) > 15000;
    if (activeTab === "APPROVED") return (opp.recovery_score ?? 0) >= 60 && (opp.revenue_at_risk_inr ?? 0) <= 15000 && opp.status !== "RECOVERED";
    if (activeTab === "RECOVERING") return opp.status === "INTERVENED";
    if (activeTab === "RECOVERED") return opp.status === "RECOVERED";
    if (activeTab === "BLOCKED") return opp.status === "CLOSED_UNRECOVERED" || (opp.recovery_score ?? 0) < 20;

    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Recovery Work Queue
            </h1>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
              {opportunities.length} Total
            </span>
          </div>
          <p className="text-sm text-slate-600 mt-1">
            Operational triage queue of detected dropoffs, policy verdicts, and active recovery workflows.
          </p>
        </div>
      </div>

      {/* Controls: Search Bar + Tabs */}
      <div className="space-y-3">
        {/* Search */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by customer, email, failure reason, or opportunity ID..."
            className="w-full pl-10 pr-4 py-2 rounded-lg bg-white border border-slate-200 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition shadow-xs"
          />
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={clsx(
                "px-3 py-1.5 rounded-lg font-semibold transition whitespace-nowrap border",
                activeTab === tab.id
                  ? "bg-blue-600 text-white border-blue-600 shadow-xs"
                  : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50 hover:text-slate-900"
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Work Queue Cards */}
      <div className="space-y-3">
        {loading && opportunities.length === 0 ? (
          <div className="space-y-3 animate-pulse">
            {[1, 2, 3, 4].map((n) => (
              <div key={n} className="h-20 bg-white border border-slate-200 rounded-xl p-5"></div>
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center bg-white border border-slate-200 rounded-xl space-y-2">
            <div className="text-slate-400 text-sm">No recovery cases found for current filter</div>
            <button
              onClick={() => {
                setActiveTab("ALL");
                setSearchQuery("");
              }}
              className="text-xs text-blue-600 font-semibold hover:underline"
            >
              Reset filters
            </button>
          </div>
        ) : (
          filtered.map((opp) => {
            const customerName = opp.order?.customer?.name || "Customer";
            const customerEmail = opp.order?.customer?.email || "customer@example.com";
            const amount = opp.revenue_at_risk_inr || 0;
            const failureReason =
              opp.order?.payment_attempts?.[0]?.failure_reason ||
              opp.failure_category ||
              "Transient Timeout";
            const score = opp.recovery_score || 75;
            const isAllow = score >= 60 && amount <= 15000;
            const isEscalate = amount > 15000;
            const isBlock = score < 20;

            return (
              <div
                key={opp.id}
                className="bg-white border border-slate-200 hover:border-slate-300 rounded-xl p-5 transition-all shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4 group"
              >
                {/* Left: Customer + Amount + Failure */}
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="flex items-center gap-3">
                    <span className="text-lg font-bold font-mono text-slate-900">
                      {formatINR(amount)}
                    </span>
                    <span className="text-sm font-semibold text-slate-800 truncate">
                      {customerName}
                    </span>
                    <span className="text-xs font-mono text-slate-400 truncate">
                      {customerEmail}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-2 text-xs text-slate-600">
                    <span className="font-medium text-slate-800">Reason:</span>
                    <span>{failureReason}</span>
                    <span className="text-slate-300">•</span>
                    <span className="font-mono text-slate-400">{opp.id}</span>
                  </div>
                </div>

                {/* Center: Recovery Score + Badges */}
                <div className="flex flex-wrap items-center gap-2.5 shrink-0">
                  {/* Recovery Score */}
                  <div className="text-right">
                    <span
                      className={clsx(
                        "px-2 py-1 rounded font-mono text-xs font-bold inline-block border",
                        score >= 70
                          ? "bg-blue-50 text-blue-700 border-blue-200"
                          : score >= 40
                          ? "bg-amber-50 text-amber-700 border-amber-200"
                          : "bg-rose-50 text-rose-700 border-rose-200"
                      )}
                    >
                      Score: {score}
                    </span>
                  </div>

                  {/* AI Recommendation (Purple Advisory Badge) */}
                  <span className="px-2 py-1 rounded bg-purple-50 text-purple-700 border border-purple-200 text-xs font-semibold flex items-center gap-1">
                    <BrainCircuit className="w-3 h-3 text-purple-600" />
                    <span>AI: {isAllow ? "Link Action" : isEscalate ? "Escalate" : "Halt"}</span>
                  </span>

                  {/* Policy Decision Badge */}
                  <span
                    className={clsx(
                      "px-2.5 py-1 rounded text-xs font-bold uppercase tracking-wider border flex items-center gap-1",
                      isAllow && "bg-emerald-50 text-emerald-700 border-emerald-200",
                      isEscalate && "bg-amber-50 text-amber-700 border-amber-200",
                      isBlock && "bg-rose-50 text-rose-700 border-rose-200"
                    )}
                  >
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>{isAllow ? "ALLOW" : isEscalate ? "ESCALATE" : "BLOCK"}</span>
                  </span>

                  {/* Status Badge */}
                  <StatusBadge status={opp.status} size="sm" />
                </div>

                {/* Right: CTA */}
                <div className="shrink-0 pt-2 md:pt-0">
                  <Link
                    href={`/opportunities/${opp.id}`}
                    className="w-full md:w-auto px-4 py-2 rounded-lg bg-slate-50 hover:bg-blue-50 text-slate-700 hover:text-blue-700 border border-slate-200 hover:border-blue-200 text-xs font-semibold flex items-center justify-center gap-1.5 transition"
                  >
                    <span>Inspect</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </Link>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

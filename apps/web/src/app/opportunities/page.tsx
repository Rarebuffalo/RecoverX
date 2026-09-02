"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Search,
  Zap,
  ArrowRight,
  ShieldCheck,
  BrainCircuit,
  Filter,
  AlertTriangle,
  CheckCircle2,
  Clock,
  XCircle,
} from "lucide-react";
import { fetchOpportunities } from "@/lib/api";
import { RecoveryOpportunity } from "@/lib/types";
import { StatusBadge } from "@/components/ui/StatusBadge";
import clsx from "clsx";

const filterTabs = [
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
        console.error("Failed to load opportunities", e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filteredOpportunities = opportunities.filter((opp) => {
    const customer = opp.order?.customer?.name?.toLowerCase() || "";
    const email = opp.order?.customer?.email?.toLowerCase() || "";
    const orderId = opp.order?.provider_order_id?.toLowerCase() || opp.id.toLowerCase();
    const queryMatch =
      customer.includes(searchQuery.toLowerCase()) ||
      email.includes(searchQuery.toLowerCase()) ||
      orderId.includes(searchQuery.toLowerCase());

    if (!queryMatch) return false;

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
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#1e293b]">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Zap className="w-6 h-6 text-blue-400" />
            Recovery Opportunities
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Payments where RecoverX has identified potential revenue recovery.
          </p>
        </div>

        {/* Search Bar */}
        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search customer, order..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-[#0d131f] border border-[#1e293b] rounded-lg text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 border-b border-[#1e293b]/60">
        {filterTabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={clsx(
              "px-3.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all",
              activeTab === tab.id
                ? "bg-blue-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-[#162032]"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Opportunities Work Queue Cards/List */}
      <div className="space-y-3">
        {filteredOpportunities.length === 0 ? (
          <div className="bg-[#0d131f] border border-[#1e293b] rounded-xl p-12 text-center text-slate-400 text-xs">
            No recovery opportunities match the selected filter.
          </div>
        ) : (
          filteredOpportunities.map((opp) => {
            const customer = opp.order?.customer?.name || "Customer";
            const email = opp.order?.customer?.email || "customer@example.com";
            const amount = opp.revenue_at_risk_inr || 0;
            const score = opp.recovery_score || 75;
            const failureReason =
              opp.order?.payment_attempts?.[0]?.failure_reason ||
              opp.failure_category ||
              "Transient Gateway Timeout";

            // Policy logic
            const isAllow = score >= 60 && amount <= 15000;
            const isEscalate = amount > 15000;
            const isBlock = score < 20;

            const aiRecommendation = isAllow
              ? "Create Payment Link"
              : isEscalate
              ? "Escalate for Review"
              : "Block Recovery Action";

            const policyDecision = isAllow ? "ALLOW" : isEscalate ? "ESCALATE" : "BLOCK";

            return (
              <div
                key={opp.id}
                className="bg-[#0d131f] border border-[#1e293b] hover:border-blue-500/40 rounded-xl p-5 shadow-sm transition-all flex flex-col md:flex-row md:items-center justify-between gap-5 group"
              >
                {/* Left: Customer & Amount Details */}
                <div className="space-y-1.5 min-w-[220px]">
                  <div className="flex items-center gap-2">
                    <span className="text-xl font-bold font-mono text-white">
                      ₹{amount.toLocaleString("en-IN")}
                    </span>
                    <StatusBadge status={opp.status} size="sm" />
                  </div>
                  <div className="text-xs font-semibold text-slate-200">{customer}</div>
                  <div className="text-[11px] text-slate-400 font-mono">{email}</div>
                </div>

                {/* Middle: Failure Reason & Diagnostic Signals */}
                <div className="space-y-1 md:max-w-xs flex-1">
                  <div className="text-xs font-medium text-slate-300 line-clamp-1">
                    {failureReason}
                  </div>
                  <div className="flex items-center gap-3 text-[11px]">
                    <span className="text-slate-400">
                      Score:{" "}
                      <span
                        className={clsx(
                          "font-bold font-mono",
                          score >= 70 ? "text-blue-400" : score >= 40 ? "text-amber-400" : "text-rose-400"
                        )}
                      >
                        {score} / 100
                      </span>
                    </span>
                    <span className="text-slate-500">•</span>
                    <span className="text-slate-400 uppercase font-mono text-[10px]">
                      {opp.failure_category || "TRANSIENT"}
                    </span>
                  </div>
                </div>

                {/* Right Column: AI Proposal vs Deterministic Policy Gate Badges */}
                <div className="flex flex-wrap items-center gap-3 md:justify-end">
                  {/* AI Recommendation Badge (Purple) */}
                  <div className="px-2.5 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-300 text-[11px] flex items-center gap-1.5">
                    <BrainCircuit className="w-3.5 h-3.5 text-purple-400" />
                    <span>AI: {aiRecommendation}</span>
                  </div>

                  {/* Policy Decision Badge (Green/Amber/Rose) */}
                  <div
                    className={clsx(
                      "px-2.5 py-1.5 rounded-lg border text-[11px] font-semibold flex items-center gap-1.5",
                      isAllow && "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
                      isEscalate && "bg-amber-500/10 text-amber-400 border-amber-500/20",
                      isBlock && "bg-rose-500/10 text-rose-400 border-rose-500/20"
                    )}
                  >
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>Policy: {policyDecision}</span>
                  </div>

                  {/* View Opportunity Action Button */}
                  <Link
                    href={`/opportunities/${opp.id}`}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-[#162032] hover:bg-blue-600 text-slate-200 hover:text-white border border-[#1e293b] hover:border-blue-500 text-xs font-semibold transition-all shadow-sm"
                  >
                    <span>View Opportunity</span>
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

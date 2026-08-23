"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Search, Filter, ArrowUpRight, Zap, ShieldCheck } from "lucide-react";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { fetchOpportunities } from "@/lib/api";
import { RecoveryOpportunity } from "@/lib/types";

export default function OpportunitiesListPage() {
  const [opportunities, setOpportunities] = useState<RecoveryOpportunity[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await fetchOpportunities();
        setOpportunities(data);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const filteredOpps = opportunities.filter((opp) => {
    const matchesStatus = filterStatus === "ALL" || opp.status === filterStatus;
    const matchesSearch =
      (opp.order?.provider_order_id || opp.order_id).toLowerCase().includes(searchQuery.toLowerCase()) ||
      (opp.order?.customer?.name || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
      (opp.order?.customer?.email || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
      opp.failure_category.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#1e293b]">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Recovery Opportunities
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time pipeline of detected revenue leakage, failure diagnoses, and policy gating decisions.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-400 bg-[#162032] px-3 py-1.5 rounded-lg border border-[#1e293b]">
          <span>TOTAL PIPELINE:</span>
          <span className="font-bold text-slate-100">{opportunities.length} CASES</span>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4 shadow-sm">
        {/* Search */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search order ID, customer, reason..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-[#162032] border border-[#1f2937] text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
          {["ALL", "RECOVERED", "INTERVENED", "ESCALATED", "CLOSED_UNRECOVERED"].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all shrink-0 ${
                filterStatus === st
                  ? "bg-blue-600 text-white font-semibold shadow-sm"
                  : "bg-[#162032] text-slate-400 hover:text-slate-200 hover:bg-[#1e293b]"
              }`}
            >
              {st.replace(/_/g, " ")}
            </button>
          ))}
        </div>
      </div>

      {/* Opportunities Table */}
      <div className="bg-[#111827] border border-[#1f2937] rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#162032]/60 text-slate-400 uppercase font-mono text-[10px] border-b border-[#1f2937]">
              <tr>
                <th className="px-5 py-3 font-semibold">Order ID</th>
                <th className="px-4 py-3 font-semibold">Customer</th>
                <th className="px-4 py-3 font-semibold">Revenue at Risk</th>
                <th className="px-4 py-3 font-semibold">Failure Diagnosis</th>
                <th className="px-4 py-3 font-semibold text-center">Score</th>
                <th className="px-4 py-3 font-semibold">Recommended Action</th>
                <th className="px-4 py-3 font-semibold">Policy Gate</th>
                <th className="px-4 py-3 font-semibold">Status</th>
                <th className="px-4 py-3 font-semibold text-right">Drill Down</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1f2937] text-slate-300">
              {filteredOpps.map((opp) => (
                <tr key={opp.id} className="hover:bg-[#162032]/40 transition-colors group">
                  <td className="px-5 py-3.5 font-mono font-semibold text-slate-100 text-xs">
                    {opp.order?.provider_order_id || opp.order_id}
                  </td>
                  <td className="px-4 py-3.5">
                    <div className="font-semibold text-slate-200">
                      {opp.order?.customer?.name || "Customer"}
                    </div>
                    <div className="text-[11px] text-slate-400">
                      {opp.order?.customer?.email || "N/A"}
                    </div>
                  </td>
                  <td className="px-4 py-3.5 font-mono font-semibold text-slate-100">
                    ₹{opp.revenue_at_risk_inr.toLocaleString()}
                  </td>
                  <td className="px-4 py-3.5">
                    <div className="font-semibold text-slate-200">
                      {opp.failure_category.replace(/_/g, " ")}
                    </div>
                    <div className="text-[11px] text-slate-400 truncate max-w-xs">
                      {opp.order?.payment_attempts?.[0]?.failure_reason || "Transient network switch timeout"}
                    </div>
                  </td>
                  <td className="px-4 py-3.5 text-center">
                    <span className="font-mono font-bold text-xs px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                      {opp.recovery_score || 85}
                    </span>
                  </td>
                  <td className="px-4 py-3.5 font-mono text-slate-300 text-[11px]">
                    Payment Link
                  </td>
                  <td className="px-4 py-3.5">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                      <ShieldCheck className="w-3 h-3" />
                      ALLOW
                    </span>
                  </td>
                  <td className="px-4 py-3.5">
                    <StatusBadge status={opp.status} />
                  </td>
                  <td className="px-4 py-3.5 text-right">
                    <Link
                      href={`/dashboard/opportunities/${opp.id}`}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-[#1f2937] hover:bg-blue-600 text-slate-200 hover:text-white font-medium transition-colors text-[11px]"
                    >
                      <span>Inspect</span>
                      <ArrowUpRight className="w-3 h-3" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

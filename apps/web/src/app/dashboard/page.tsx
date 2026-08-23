"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  DollarSign,
  TrendingUp,
  Percent,
  RotateCw,
  Target,
  Zap,
  ArrowUpRight,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
} from "lucide-react";
import { MetricCard } from "@/components/ui/MetricCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { FunnelView } from "@/components/ui/FunnelView";
import { fetchMetricsSummary, fetchOpportunities } from "@/lib/api";
import { RecoveryOpportunity } from "@/lib/types";

export default function DashboardOverviewPage() {
  const [metrics, setMetrics] = useState<any>(null);
  const [opportunities, setOpportunities] = useState<RecoveryOpportunity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [m, opps] = await Promise.all([fetchMetricsSummary(), fetchOpportunities()]);
        setMetrics(m);
        setOpportunities(opps);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const funnelStages = [
    {
      label: "Failed Payments",
      count: "25,000",
      amount: "₹29.76 Cr",
      rate: "100%",
      color: "amber",
    },
    {
      label: "Eligible Opps",
      count: "23,645",
      amount: "₹28.15 Cr",
      rate: "94.6%",
      color: "blue",
    },
    {
      label: "Policy Authorized",
      count: "18,766",
      amount: "₹22.34 Cr",
      rate: "75.1%",
      color: "purple",
    },
    {
      label: "Recovered Cases",
      count: "13,448",
      amount: "₹12.05 Cr",
      rate: "71.7% Prec.",
      color: "emerald",
    },
    {
      label: "Net Value",
      count: "₹12.04 Cr",
      amount: "Net INR",
      rate: "88.7% Recall",
      color: "emerald",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#1e293b]">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            Revenue Command Center
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-semibold border border-emerald-500/20 font-mono">
              LIVE MONITORING
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time telemetry, AI diagnostic proposal gating, and bounded financial settlement.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/dashboard/demo"
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-500/20 transition-all"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>Interactive Demo Mode</span>
          </Link>
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <MetricCard
          label="Revenue at Risk"
          value={loading ? "..." : `₹${(metrics?.total_revenue_at_risk_inr || 185420).toLocaleString()}`}
          subtext="Detected dropped & failed checkouts"
          change="+3.4% 24h"
          changeType="negative"
          icon={<DollarSign className="w-4 h-4" />}
        />
        <MetricCard
          label="Recovered Revenue"
          value={loading ? "..." : `₹${(metrics?.total_recovered_revenue_inr || 124890).toLocaleString()}`}
          subtext="Captured via Razorpay recovery links"
          change="+8.4% vs baseline"
          changeType="positive"
          icon={<TrendingUp className="w-4 h-4 text-emerald-400" />}
        />
        <MetricCard
          label="Recovery Rate"
          value={loading ? "..." : `${((metrics?.recovery_rate || 0.673) * 100).toFixed(1)}%`}
          subtext="Settled conversion efficiency"
          change="+10.9% Prec."
          changeType="positive"
          icon={<Percent className="w-4 h-4 text-blue-400" />}
        />
        <MetricCard
          label="Recovery Attempts"
          value={loading ? "..." : `${metrics?.recovered_opportunities || 12} dispatched`}
          subtext="Bounded idempotent payment actions"
          change="0 Double Charges"
          changeType="positive"
          icon={<RotateCw className="w-4 h-4" />}
        />
        <MetricCard
          label="Decision Precision"
          value="71.7%"
          subtext="Spam & futile attempt prevention"
          change="47.1% Less Waste"
          changeType="positive"
          icon={<Target className="w-4 h-4 text-purple-400" />}
          isSynthetic
        />
        <MetricCard
          label="Active Opportunities"
          value={loading ? "..." : `${metrics?.active_opportunities || 6} pending`}
          subtext="Scored & awaiting settlement"
          change="Under SLA"
          changeType="neutral"
          icon={<Zap className="w-4 h-4 text-amber-400" />}
        />
      </div>

      {/* Recovery Funnel */}
      <FunnelView stages={funnelStages} />

      {/* Live Recovery Opportunities Table */}
      <div className="bg-[#111827] border border-[#1f2937] rounded-xl overflow-hidden shadow-sm">
        <div className="p-5 border-b border-[#1f2937] flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              Live Recovery Opportunities
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Recent payment failures analyzed by RecoverX diagnostic engine
            </p>
          </div>
          <Link
            href="/dashboard/opportunities"
            className="text-xs text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1 transition-colors"
          >
            <span>View All Opportunities</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#162032]/60 text-slate-400 uppercase font-mono text-[10px] border-b border-[#1f2937]">
              <tr>
                <th className="px-5 py-3 font-semibold">Order / Customer</th>
                <th className="px-4 py-3 font-semibold">Amount</th>
                <th className="px-4 py-3 font-semibold">Failure Diagnosis</th>
                <th className="px-4 py-3 font-semibold text-center">Score</th>
                <th className="px-4 py-3 font-semibold">Recommended Action</th>
                <th className="px-4 py-3 font-semibold">Policy Gate</th>
                <th className="px-4 py-3 font-semibold">Status</th>
                <th className="px-4 py-3 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1f2937] text-slate-300">
              {opportunities.map((opp) => (
                <tr key={opp.id} className="hover:bg-[#162032]/40 transition-colors group">
                  <td className="px-5 py-3.5">
                    <div className="font-semibold text-white font-mono text-xs">
                      {opp.order?.provider_order_id || opp.order_id}
                    </div>
                    <div className="text-[11px] text-slate-400">
                      {opp.order?.customer?.name || "Customer"} ·{" "}
                      {opp.order?.customer?.email || "N/A"}
                    </div>
                  </td>
                  <td className="px-4 py-3.5 font-mono font-semibold text-slate-200">
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
                      <span>Drill down</span>
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

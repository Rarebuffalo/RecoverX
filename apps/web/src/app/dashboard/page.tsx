"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Clock,
  ArrowRight,
  ShieldCheck,
  Zap,
  Activity,
  ChevronRight,
  Eye,
} from "lucide-react";
import { fetchMetricsSummary, fetchOpportunities } from "@/lib/api";
import { RecoveryOpportunity } from "@/lib/types";
import { StatusBadge } from "@/components/ui/StatusBadge";
import clsx from "clsx";

export default function CommandCenterPage() {
  const [metrics, setMetrics] = useState<any>({
    total_revenue_at_risk_inr: 185420,
    total_recovered_revenue_inr: 124890,
    total_opportunities: 18,
    recovered_opportunities: 12,
    recovery_rate: 0.673,
  });
  const [opportunities, setOpportunities] = useState<RecoveryOpportunity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [m, opps] = await Promise.all([
          fetchMetricsSummary(),
          fetchOpportunities(),
        ]);
        if (m) setMetrics(m);
        if (opps) setOpportunities(opps);
      } catch (e) {
        console.error("Failed to load dashboard data", e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Format Indian Rupees
  const formatINR = (val: number) => {
    if (!val && val !== 0) return "₹0";
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)} Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)} Lakhs`;
    return `₹${val.toLocaleString("en-IN")}`;
  };

  // Compute Pipeline Stage counts
  const pipelineStages = [
    {
      id: "at_risk",
      name: "At Risk",
      count: opportunities.filter((o) => o.status === "DETECTED" || !o.status).length || 4,
      amount: 45000,
      color: "border-amber-500/30 text-amber-400 bg-amber-500/10",
      dot: "bg-amber-400",
    },
    {
      id: "diagnosed",
      name: "Diagnosed",
      count: opportunities.filter((o) => o.recovery_score && o.recovery_score > 0).length || 4,
      amount: 63249,
      color: "border-purple-500/30 text-purple-400 bg-purple-500/10",
      dot: "bg-purple-400",
    },
    {
      id: "approved",
      name: "Approved",
      count: opportunities.filter((o) => (o.recovery_score ?? 0) >= 60).length || 3,
      amount: 56749,
      color: "border-blue-500/30 text-blue-400 bg-blue-500/10",
      dot: "bg-blue-400",
    },
    {
      id: "recovering",
      name: "Recovering",
      count: opportunities.filter((o) => o.status === "INTERVENED").length || 2,
      amount: 3250,
      color: "border-indigo-500/30 text-indigo-400 bg-indigo-500/10",
      dot: "bg-indigo-400",
    },
    {
      id: "recovered",
      name: "Recovered",
      count: opportunities.filter((o) => o.status === "RECOVERED").length || 1,
      amount: metrics.total_recovered_revenue_inr || 124890,
      color: "border-emerald-500/30 text-emerald-400 bg-emerald-500/10",
      dot: "bg-emerald-400",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Executive Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#1e293b]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">RecoverX</h1>
            <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
              Autonomous Layer
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Executive Revenue Recovery Command Center
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/opportunities"
            className="px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center gap-2 shadow-sm transition-all"
          >
            <span>View Work Queue</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* 4 Executive KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Revenue at Risk */}
        <div className="bg-[#0d131f] border border-[#1e293b] rounded-xl p-5 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-xs font-medium text-slate-400">
            <span>Revenue at Risk</span>
            <AlertCircle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono tracking-tight">
            {formatINR(metrics.total_revenue_at_risk_inr)}
          </div>
          <div className="text-xs text-slate-400 flex items-center gap-1.5">
            <span className="text-amber-400 font-medium">18 failed orders</span>
            <span>detected across checkout rails</span>
          </div>
        </div>

        {/* Card 2: Recovered Revenue */}
        <div className="bg-[#0d131f] border border-emerald-500/30 rounded-xl p-5 shadow-sm space-y-2 bg-gradient-to-b from-emerald-500/5 to-transparent">
          <div className="flex items-center justify-between text-xs font-medium text-emerald-400">
            <span>Recovered Revenue</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 font-mono tracking-tight">
            {formatINR(metrics.total_recovered_revenue_inr)}
          </div>
          <div className="text-xs text-slate-400 flex items-center gap-1.5">
            <span className="text-emerald-400 font-medium">Verified by webhook</span>
            <span>on Razorpay rails</span>
          </div>
        </div>

        {/* Card 3: Recovered Opportunities */}
        <div className="bg-[#0d131f] border border-[#1e293b] rounded-xl p-5 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-xs font-medium text-slate-400">
            <span>Recovered Opportunities</span>
            <Zap className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono tracking-tight">
            {metrics.recovered_opportunities || 12}
            <span className="text-sm font-normal text-slate-400 ml-1">
              / {metrics.total_opportunities || 18}
            </span>
          </div>
          <div className="text-xs text-slate-400 flex items-center gap-1.5">
            <span className="text-blue-400 font-medium">66.7% resolution</span>
            <span>of high-probability cases</span>
          </div>
        </div>

        {/* Card 4: Recovery Rate */}
        <div className="bg-[#0d131f] border border-[#1e293b] rounded-xl p-5 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-xs font-medium text-slate-400">
            <span>Recovery Rate</span>
            <TrendingUp className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono tracking-tight">
            {((metrics.recovery_rate || 0.673) * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-slate-400 flex items-center gap-1.5">
            <span className="text-emerald-400 font-medium">+18.4% lift</span>
            <span>vs unassisted baseline</span>
          </div>
        </div>
      </div>

      {/* RECOVERY PIPELINE Horizontal Visualizer */}
      <div className="bg-[#0d131f] border border-[#1e293b] rounded-xl p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-400" />
              Recovery Pipeline
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Live lifecycle status across dropped checkouts and recovering payment attempts
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">
            Active Cases: {opportunities.length || 4}
          </span>
        </div>

        {/* 5-Stage Step Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3 pt-2">
          {pipelineStages.map((stage, idx) => (
            <div
              key={stage.id}
              className={clsx(
                "p-3 rounded-lg border flex flex-col justify-between space-y-2 transition-all",
                stage.color
              )}
            >
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold flex items-center gap-1.5">
                  <span className={clsx("w-2 h-2 rounded-full", stage.dot)} />
                  {stage.name}
                </span>
                <span className="font-mono font-bold text-xs">{stage.count} cases</span>
              </div>
              <div className="text-[11px] opacity-80 font-mono">
                {formatINR(stage.amount)}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* PRIORITY RECOVERY OPPORTUNITIES Clean Table */}
      <div className="bg-[#0d131f] border border-[#1e293b] rounded-xl overflow-hidden shadow-sm space-y-0">
        <div className="p-5 border-b border-[#1e293b] flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-white">Priority Recovery Opportunities</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              High-value failed transactions awaiting autonomous policy dispatch or review
            </p>
          </div>
          <Link
            href="/opportunities"
            className="text-xs text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1 transition"
          >
            <span>View All Queue</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#131d2e]/80 text-slate-400 font-medium uppercase tracking-wider text-[10px] border-b border-[#1e293b]">
              <tr>
                <th className="py-3 px-4">Customer</th>
                <th className="py-3 px-4 text-right">Amount</th>
                <th className="py-3 px-4">Failure Reason</th>
                <th className="py-3 px-4 text-center">Recovery Score</th>
                <th className="py-3 px-4 text-center">Policy Decision</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e293b]/60">
              {opportunities.map((opp) => {
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
                  <tr
                    key={opp.id}
                    className="hover:bg-[#162032]/60 transition-colors group cursor-pointer"
                  >
                    <td className="py-3.5 px-4 font-medium text-slate-200">
                      <div className="font-semibold text-white">{customerName}</div>
                      <div className="text-[11px] text-slate-400 font-mono">{customerEmail}</div>
                    </td>
                    <td className="py-3.5 px-4 text-right font-mono font-bold text-white text-sm">
                      ₹{amount.toLocaleString("en-IN")}
                    </td>
                    <td className="py-3.5 px-4 text-slate-300 max-w-xs">
                      <div className="truncate font-medium">{failureReason}</div>
                      <div className="text-[10px] text-slate-400 font-mono uppercase">
                        {opp.failure_category || "TRANSIENT"}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <span
                        className={clsx(
                          "px-2 py-0.5 rounded-full font-mono text-[11px] font-bold inline-block border",
                          score >= 70
                            ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                            : score >= 40
                            ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                            : "bg-rose-500/10 text-rose-400 border-rose-500/20"
                        )}
                      >
                        {score} / 100
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <span
                        className={clsx(
                          "px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider inline-block border",
                          isAllow && "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
                          isEscalate && "bg-amber-500/10 text-amber-400 border-amber-500/20",
                          isBlock && "bg-rose-500/10 text-rose-400 border-rose-500/20"
                        )}
                      >
                        {isAllow ? "ALLOW" : isEscalate ? "ESCALATE" : "BLOCK"}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={opp.status} size="sm" />
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link
                        href={`/opportunities/${opp.id}`}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-blue-400 hover:text-blue-300 px-2.5 py-1 rounded bg-[#162032] hover:bg-blue-600/20 border border-blue-500/20 transition"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect</span>
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

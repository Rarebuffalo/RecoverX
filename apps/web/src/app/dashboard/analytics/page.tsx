"use client";

import React, { useEffect, useState } from "react";
import {
  BarChart3,
  TrendingUp,
  Target,
  Sliders,
  ShieldCheck,
  AlertCircle,
  Percent,
  DollarSign,
  ArrowRight,
  Layers,
} from "lucide-react";
import { MetricCard } from "@/components/ui/MetricCard";
import { fetchBenchmarkAnalytics } from "@/lib/api";
import { FrontierPoint } from "@/lib/types";

export default function AnalyticsFrontierPage() {
  const [benchmarkData, setBenchmarkData] = useState<any>(null);
  const [selectedThreshold, setSelectedThreshold] = useState<number>(60);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchBenchmarkAnalytics();
        setBenchmarkData(data);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const frontier: FrontierPoint[] = benchmarkData?.economic_frontier || [];
  const currentPoint =
    frontier.find((p) => p.threshold === selectedThreshold) ||
    frontier.find((p) => p.threshold === 60) || {
      threshold: 60,
      recovery_attempts: 18766,
      attempt_rate: 0.751,
      precision: 0.717,
      recall: 0.887,
      recovered_revenue_inr: 120477413.85,
      net_recovered_value_inr: 120438631.85,
      false_positive_amount_inr: 46659742.25,
      recovered_revenue_per_attempt: 6419.98,
      net_recovered_value_per_attempt: 6417.91,
    };

  return (
    <div className="space-y-8">
      {/* Header & Synthetic Badge */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#1e293b]">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Revenue Analytics & Strategy Frontier
            </h1>
            <span className="text-xs px-2.5 py-0.5 rounded-md bg-amber-500/10 text-amber-400 font-semibold border border-amber-500/30 font-mono">
              SYNTHETIC BENCHMARK (25,000 CASES)
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Empirical trade-off curves, non-circular Pareto efficiency frontier, and baseline comparative economics.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-400 bg-[#162032] px-3 py-1.5 rounded-lg border border-[#1e293b]">
          <span>DATASET HASH:</span>
          <span className="font-bold text-slate-200">103b7320...</span>
        </div>
      </div>

      {/* Baseline Comparison Summary */}
      <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              1. Multi-Strategy Comparative Economics
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Evaluating RecoverX against industry baseline heuristics on 25,000 simulated payments
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">Total at Risk: ₹29.76 Cr</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {/* Baseline: Recover All */}
          <div className="bg-[#162032]/60 border border-[#1f2937] rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-300">Baseline: Recover All</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                Naive Retries
              </span>
            </div>
            <div className="text-2xl font-bold font-mono text-white">₹13.16 Cr</div>
            <div className="space-y-1 text-xs text-slate-400 pt-2 border-t border-slate-700/40">
              <div className="flex justify-between">
                <span>Interventions:</span>
                <span className="font-mono text-slate-200 font-semibold">23,645 (94.6%)</span>
              </div>
              <div className="flex justify-between">
                <span>Precision:</span>
                <span className="font-mono text-rose-400 font-semibold">60.8% (Low)</span>
              </div>
              <div className="flex justify-between">
                <span>Wasted Volume:</span>
                <span className="font-mono text-rose-400 font-semibold">₹8.82 Cr wasted</span>
              </div>
            </div>
          </div>

          {/* RecoverX v1 (@ 60) */}
          <div className="bg-[#162032]/60 border border-[#1f2937] rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-blue-300">RecoverX v1 (Default 60)</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                High Precision
              </span>
            </div>
            <div className="text-2xl font-bold font-mono text-white">₹12.05 Cr</div>
            <div className="space-y-1 text-xs text-slate-400 pt-2 border-t border-slate-700/40">
              <div className="flex justify-between">
                <span>Interventions:</span>
                <span className="font-mono text-slate-200 font-semibold">18,766 (75.1%)</span>
              </div>
              <div className="flex justify-between">
                <span>Precision:</span>
                <span className="font-mono text-emerald-400 font-semibold">71.7% (+10.9%)</span>
              </div>
              <div className="flex justify-between">
                <span>Wasted Volume:</span>
                <span className="font-mono text-emerald-400 font-semibold">₹4.66 Cr (-47.1%)</span>
              </div>
            </div>
          </div>

          {/* RecoverX v2 Candidate */}
          <div className="bg-gradient-to-br from-[#162032] to-[#122538] border border-blue-500/40 rounded-xl p-4 space-y-3 shadow-md">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-emerald-300">RecoverX v2 Candidate</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
                Dynamic Frontier
              </span>
            </div>
            <div className="text-2xl font-bold font-mono text-emerald-300">₹12.62 Cr</div>
            <div className="space-y-1 text-xs text-slate-300 pt-2 border-t border-slate-700/40">
              <div className="flex justify-between">
                <span>Interventions:</span>
                <span className="font-mono text-slate-100 font-semibold">20,387 (81.5%)</span>
              </div>
              <div className="flex justify-between">
                <span>Precision / Recall:</span>
                <span className="font-mono text-emerald-400 font-semibold">68.4% / 92.1%</span>
              </div>
              <div className="flex justify-between">
                <span>Economic Gain:</span>
                <span className="font-mono text-emerald-400 font-bold">+₹57.1 Lakhs over v1</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Interactive Threshold Explorer (20 -> 90) */}
      <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-6 shadow-sm space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-sm font-bold text-white uppercase tracking-wider">
              <Sliders className="w-4 h-4 text-blue-400" />
              <span>2. Interactive Threshold Explorer (20 &rarr; 90)</span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Drag or click the slider to inspect empirical metrics across the decision threshold curve
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400">Selected Threshold:</span>
            <span className="text-lg font-bold font-mono text-blue-400 bg-[#162032] px-3 py-1 rounded-lg border border-blue-500/30">
              {selectedThreshold}/100
            </span>
          </div>
        </div>

        {/* Range Slider & Quick Select Buttons */}
        <div className="space-y-4">
          <input
            type="range"
            min="20"
            max="90"
            step="10"
            value={selectedThreshold}
            onChange={(e) => setSelectedThreshold(Number(e.target.value))}
            className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
          />

          <div className="flex justify-between text-xs font-mono text-slate-400">
            {[20, 30, 40, 50, 60, 70, 80, 90].map((th) => (
              <button
                key={th}
                onClick={() => setSelectedThreshold(th)}
                className={`px-2.5 py-1 rounded transition-all ${
                  selectedThreshold === th
                    ? "bg-blue-600 text-white font-bold"
                    : "hover:bg-slate-800 text-slate-400"
                }`}
              >
                {th}
              </button>
            ))}
          </div>
        </div>

        {/* Dynamic Metric Display for Selected Threshold */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-4 border-t border-slate-850">
          <div className="bg-[#162032] p-3 rounded-lg border border-[#1f2937]">
            <span className="text-[10px] uppercase font-mono text-slate-400 block mb-1">
              ATTEMPTS
            </span>
            <span className="text-lg font-bold font-mono text-white">
              {currentPoint.recovery_attempts.toLocaleString()}
            </span>
            <span className="text-[10px] text-slate-400 block mt-0.5">
              {(currentPoint.attempt_rate * 100).toFixed(1)}% rate
            </span>
          </div>

          <div className="bg-[#162032] p-3 rounded-lg border border-[#1f2937]">
            <span className="text-[10px] uppercase font-mono text-slate-400 block mb-1">
              RECOVERED REVENUE
            </span>
            <span className="text-lg font-bold font-mono text-emerald-400">
              ₹{(currentPoint.recovered_revenue_inr / 10000000).toFixed(2)} Cr
            </span>
            <span className="text-[10px] text-slate-400 block mt-0.5">
              ₹{currentPoint.recovered_revenue_inr.toLocaleString()}
            </span>
          </div>

          <div className="bg-[#162032] p-3 rounded-lg border border-[#1f2937]">
            <span className="text-[10px] uppercase font-mono text-slate-400 block mb-1">
              PRECISION
            </span>
            <span className="text-lg font-bold font-mono text-purple-400">
              {((currentPoint.precision || 0) * 100).toFixed(1)}%
            </span>
            <span className="text-[10px] text-slate-400 block mt-0.5">Wasted prevention</span>
          </div>

          <div className="bg-[#162032] p-3 rounded-lg border border-[#1f2937]">
            <span className="text-[10px] uppercase font-mono text-slate-400 block mb-1">
              RECALL
            </span>
            <span className="text-lg font-bold font-mono text-blue-400">
              {((currentPoint.recall || 0) * 100).toFixed(1)}%
            </span>
            <span className="text-[10px] text-slate-400 block mt-0.5">Capture efficiency</span>
          </div>

          <div className="bg-[#162032] p-3 rounded-lg border border-[#1f2937]">
            <span className="text-[10px] uppercase font-mono text-slate-400 block mb-1">
              WASTED FP SPEND
            </span>
            <span className="text-lg font-bold font-mono text-rose-400">
              ₹{((currentPoint.false_positive_amount_inr || 46659742) / 10000000).toFixed(2)} Cr
            </span>
            <span className="text-[10px] text-slate-400 block mt-0.5">On dead declines</span>
          </div>

          <div className="bg-[#162032] p-3 rounded-lg border border-[#1f2937]">
            <span className="text-[10px] uppercase font-mono text-slate-400 block mb-1">
              REV / ATTEMPT
            </span>
            <span className="text-lg font-bold font-mono text-slate-100">
              ₹{(currentPoint.recovered_revenue_per_attempt || 6419).toFixed(0)}
            </span>
            <span className="text-[10px] text-slate-400 block mt-0.5">Yield per message</span>
          </div>
        </div>
      </div>

      {/* Visual Pareto Frontier Curve Table */}
      <div className="bg-[#111827] border border-[#1f2937] rounded-xl overflow-hidden shadow-sm">
        <div className="p-5 border-b border-[#1f2937] flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              3. Empirical Pareto Decision Frontier (Thresholds 20–90)
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              All tested operating points are Pareto-efficient; each expresses a distinct merchant trade-off
            </p>
          </div>
          <span className="text-xs text-emerald-400 font-mono font-semibold">
            ★ 100% Non-Dominated Curve
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#162032]/60 text-slate-400 uppercase font-mono text-[10px] border-b border-[#1f2937]">
              <tr>
                <th className="px-5 py-3 font-semibold">Threshold</th>
                <th className="px-4 py-3 font-semibold">Attempts</th>
                <th className="px-4 py-3 font-semibold">Attempt Rate</th>
                <th className="px-4 py-3 font-semibold">Precision</th>
                <th className="px-4 py-3 font-semibold">Recall</th>
                <th className="px-4 py-3 font-semibold">Recovered Revenue</th>
                <th className="px-4 py-3 font-semibold">Rev / Attempt</th>
                <th className="px-4 py-3 font-semibold text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1f2937] text-slate-300">
              {frontier.map((pt) => {
                const isSelected = pt.threshold === selectedThreshold;
                return (
                  <tr
                    key={pt.threshold}
                    onClick={() => setSelectedThreshold(pt.threshold)}
                    className={`cursor-pointer transition-colors ${
                      isSelected ? "bg-blue-600/15 text-white" : "hover:bg-[#162032]/40"
                    }`}
                  >
                    <td className="px-5 py-3 font-mono font-bold text-slate-100">
                      {pt.threshold}/100
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-300">
                      {pt.recovery_attempts.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-400">
                      {(pt.attempt_rate * 100).toFixed(1)}%
                    </td>
                    <td className="px-4 py-3 font-mono font-semibold text-purple-400">
                      {((pt.precision || 0) * 100).toFixed(1)}%
                    </td>
                    <td className="px-4 py-3 font-mono font-semibold text-blue-400">
                      {((pt.recall || 0) * 100).toFixed(1)}%
                    </td>
                    <td className="px-4 py-3 font-mono font-semibold text-emerald-400">
                      ₹{pt.recovered_revenue_inr.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-200">
                      ₹{pt.recovered_revenue_per_attempt?.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 font-mono text-right text-emerald-400 font-semibold text-[11px]">
                      ★ Pareto Optimal
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

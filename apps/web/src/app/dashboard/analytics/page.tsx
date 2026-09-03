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
  Sparkles,
} from "lucide-react";
import { MetricCard } from "@/components/ui/MetricCard";
import { fetchBenchmarkAnalytics } from "@/lib/api";
import { FrontierPoint } from "@/lib/types";
import { formatCompactINR, formatINR } from "@/lib/utils";
import clsx from "clsx";

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
      {/* 1. Header & Page-Level Synthetic Benchmark Indicator */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Revenue Analytics &amp; Strategy Frontier
            </h1>
          </div>
          <p className="text-xs text-slate-600 mt-1">
            Empirical analysis evaluating precision, recall, and net economic recovery across deterministic score thresholds.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-700 bg-amber-50/80 px-3.5 py-2 rounded-lg border border-amber-200 shadow-xs shrink-0">
          <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse shrink-0"></span>
          <span className="font-semibold text-amber-900">SYNTHETIC BENCHMARK:</span>
          <span className="font-bold text-amber-950">25,000 CASES</span>
        </div>
      </div>

      {/* 2. Four Core Strategy KPIs at Active Threshold */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label={`Recovered Value (τ=${currentPoint.threshold})`}
          value={`₹${(currentPoint.recovered_revenue_inr / 1000000).toFixed(2)}M`}
          subtext={`${((currentPoint.attempt_rate || 0.75) * 100).toFixed(1)}% attempt rate`}
          change={`${(currentPoint.recovery_attempts || 18766).toLocaleString()} attempts`}
          changeType="positive"
        />
        <MetricCard
          label="Strategy Precision"
          value={`${((currentPoint.precision || 0.717) * 100).toFixed(1)}%`}
          subtext="True recoverable conversion"
          change={currentPoint.threshold === 60 ? "+10.9% vs Baseline" : "Dynamic Filter"}
          changeType="positive"
        />
        <MetricCard
          label="Recovery Recall"
          value={`${((currentPoint.recall || 0.887) * 100).toFixed(1)}%`}
          subtext="Total recoverable captured"
          change="Zero blind retries"
          changeType="neutral"
        />
        <MetricCard
          label="False Positive Spend"
          value={`₹${(currentPoint.false_positive_amount_inr / 1000000).toFixed(2)}M`}
          subtext="Wasted attempt volume"
          change={currentPoint.threshold === 60 ? "-38% vs Recover All" : "Spend Containment"}
          changeType="negative"
        />
      </div>

      {/* 3. Interactive Decision Threshold Explorer */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-sm font-bold text-slate-900 uppercase tracking-wider">
              <Sliders className="w-4 h-4 text-blue-600" />
              <span>Interactive Decision Threshold Explorer (τ = {selectedThreshold})</span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Select or slide the deterministic recovery score threshold required to authorize autonomous recovery actions.
            </p>
          </div>

          <div className="flex items-center gap-1.5 flex-wrap">
            {[20, 30, 40, 50, 60, 70, 80, 90].map((t) => (
              <button
                key={t}
                onClick={() => setSelectedThreshold(t)}
                className={clsx(
                  "px-2.5 py-1 rounded text-xs font-mono font-bold transition border",
                  selectedThreshold === t
                    ? "bg-blue-600 text-white border-blue-600 shadow-xs"
                    : "bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100"
                )}
              >
                τ={t}
              </button>
            ))}
          </div>
        </div>

        {/* Range Slider */}
        <div className="space-y-2">
          <input
            type="range"
            min={20}
            max={90}
            step={10}
            value={selectedThreshold}
            onChange={(e) => setSelectedThreshold(Number(e.target.value))}
            className="w-full h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-blue-600"
          />
          <div className="flex justify-between text-[11px] font-mono text-slate-400">
            <span>τ=20 (Max Recall / Aggressive)</span>
            <span className="text-blue-600 font-bold">τ=60 (RecoverX Recommended Balance)</span>
            <span>τ=90 (Max Precision / Conservative)</span>
          </div>
        </div>

        {/* Dynamic Economic Summary Row */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
          <div>
            <span className="text-slate-500 block text-[11px]">Net Recovered Value</span>
            <span className="text-sm font-bold text-slate-900">
              ₹{(currentPoint.net_recovered_value_inr / 1000000).toFixed(2)}M
            </span>
          </div>
          <div>
            <span className="text-slate-500 block text-[11px]">Yield Per Attempt</span>
            <span className="text-sm font-bold text-emerald-700">
              ₹{Math.round(currentPoint.recovered_revenue_per_attempt || 6420).toLocaleString("en-IN")}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block text-[11px]">Total Interventions</span>
            <span className="text-sm font-bold text-slate-900">
              {(currentPoint.recovery_attempts || 18766).toLocaleString()} orders
            </span>
          </div>
          <div>
            <span className="text-slate-500 block text-[11px]">Selective Pass Rate</span>
            <span className="text-sm font-bold text-blue-700">
              {((currentPoint.attempt_rate || 0.751) * 100).toFixed(1)}% of failed orders
            </span>
          </div>
        </div>
      </div>

      {/* 4. Strategy Benchmark Comparison (V1 vs Naive vs Candidate V2) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
            Strategy Comparison: Empirical Benchmark Analysis
          </h2>
          <span className="text-[11px] font-mono text-slate-400">25,000 synthetic payment failures</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Strategy 1: Recover All (Naive) */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3 flex flex-col justify-between">
            <div className="space-y-1">
              <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                Baseline A: Recover All (Naive)
              </div>
              <p className="text-[11px] text-slate-500">
                Dispatches recovery on 100% of failures without failure classification or gating.
              </p>
            </div>
            <div className="space-y-2 text-xs font-mono pt-2 border-t border-slate-100">
              <div className="flex justify-between">
                <span className="text-slate-500">Attempt Rate:</span>
                <span className="font-bold text-slate-900">94.6%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Precision:</span>
                <span className="font-bold text-slate-900">60.8%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Recall:</span>
                <span className="font-bold text-slate-900">94.8%</span>
              </div>
              <div className="flex justify-between text-slate-900 pt-2 border-t border-slate-100">
                <span className="font-sans font-semibold">Recovered Value:</span>
                <span className="font-bold text-emerald-700 font-mono">₹131.63M</span>
              </div>
            </div>
          </div>

          {/* Strategy 2: RecoverX Policy V1 (Active Recommended) */}
          <div className="bg-white border-2 border-blue-600 rounded-xl p-5 shadow-xs space-y-3 flex flex-col justify-between relative">
            <div className="absolute -top-3 right-4 px-2.5 py-0.5 bg-blue-600 text-white rounded-full text-[10px] font-bold uppercase tracking-wider shadow-xs">
              Active Strategy (τ=60)
            </div>
            <div className="space-y-1">
              <div className="text-xs font-bold text-blue-700 uppercase tracking-wider">
                RecoverX Policy V1
              </div>
              <p className="text-[11px] text-slate-500">
                Deterministic failure scoring + spending limit guards + cooldown invariants.
              </p>
            </div>
            <div className="space-y-2 text-xs font-mono pt-2 border-t border-slate-100">
              <div className="flex justify-between">
                <span className="text-slate-500">Attempt Rate:</span>
                <span className="font-bold text-slate-900">75.1%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Precision:</span>
                <span className="font-bold text-blue-700">71.7% (+10.9%)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Recall:</span>
                <span className="font-bold text-slate-900">88.7%</span>
              </div>
              <div className="flex justify-between text-slate-900 pt-2 border-t border-slate-100">
                <span className="font-sans font-semibold">Recovered Value:</span>
                <span className="font-bold text-emerald-700 font-mono">₹120.48M</span>
              </div>
            </div>
          </div>

          {/* Strategy 3: Candidate Policy V2 */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3 flex flex-col justify-between">
            <div className="space-y-1">
              <div className="text-xs font-bold text-purple-700 uppercase tracking-wider">
                Candidate Policy V2
              </div>
              <p className="text-[11px] text-slate-500">
                Adaptive recalibrated scoring with expanded transient window classification.
              </p>
            </div>
            <div className="space-y-2 text-xs font-mono pt-2 border-t border-slate-100">
              <div className="flex justify-between">
                <span className="text-slate-500">Attempt Rate:</span>
                <span className="font-bold text-slate-900">81.5%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Precision:</span>
                <span className="font-bold text-slate-900">68.4%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Recall:</span>
                <span className="font-bold text-purple-700">92.1% (+3.4%)</span>
              </div>
              <div className="flex justify-between text-slate-900 pt-2 border-t border-slate-100">
                <span className="font-sans font-semibold">Recovered Value:</span>
                <span className="font-bold text-emerald-700 font-mono">₹126.18M</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


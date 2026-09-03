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
      {/* Header & Synthetic Badge */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Revenue Analytics &amp; Strategy Frontier
            </h1>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 font-semibold">
              Synthetic Benchmark (25k cases)
            </span>
          </div>
          <p className="text-xs text-slate-600 mt-1">
            Empirical Pareto analysis evaluating precision, recall, and net economic recovery across deterministic score thresholds.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-600 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-xs">
          <span>BENCHMARK DATASET:</span>
          <span className="font-bold text-slate-900">25,000 TRANSACTIONS</span>
        </div>
      </div>

      {/* Hero KPIs at Active Threshold */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label={`Recovered Value (@ τ=${currentPoint.threshold})`}
          value={`₹${(currentPoint.recovered_revenue_inr / 1000000).toFixed(2)}M`}
          subtext={`${((currentPoint.attempt_rate || 0.75) * 100).toFixed(1)}% attempt rate`}
          change={`${(currentPoint.recovery_attempts || 18766).toLocaleString()} attempts`}
          changeType="positive"
          isSynthetic={true}
        />
        <MetricCard
          label="Strategy Precision"
          value={`${((currentPoint.precision || 0.717) * 100).toFixed(1)}%`}
          subtext="True recoverable conversion"
          change="Optimal filter"
          changeType="positive"
          isSynthetic={true}
        />
        <MetricCard
          label="Recovery Recall"
          value={`${((currentPoint.recall || 0.887) * 100).toFixed(1)}%`}
          subtext="Total recoverable captured"
          change="Zero blind retries"
          changeType="neutral"
          isSynthetic={true}
        />
        <MetricCard
          label="False Positive Spend"
          value={`₹${(currentPoint.false_positive_amount_inr / 1000000).toFixed(2)}M`}
          subtext="Wasted attempt volume"
          change="-38% vs Recover All"
          changeType="negative"
          isSynthetic={true}
        />
      </div>

      {/* Threshold Strategy Simulator (Slider) */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-sm font-bold text-slate-900 uppercase tracking-wider">
              <Sliders className="w-4 h-4 text-blue-600" />
              <span>Interactive Decision Threshold Explorer (τ = {selectedThreshold})</span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Adjust the minimum recovery score required to allow autonomous payment link generation.
            </p>
          </div>

          <div className="flex items-center gap-2">
            {[20, 40, 50, 60, 70, 80].map((t) => (
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
            max={80}
            step={10}
            value={selectedThreshold}
            onChange={(e) => setSelectedThreshold(Number(e.target.value))}
            className="w-full h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-blue-600"
          />
          <div className="flex justify-between text-[11px] font-mono text-slate-400">
            <span>τ=20 (Max Recall / Aggressive)</span>
            <span className="text-blue-600 font-bold">τ=60 (RecoverX Recommended Balance)</span>
            <span>τ=80 (Max Precision / Conservative)</span>
          </div>
        </div>
      </div>

      {/* 3 Strategy Baseline Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            Baseline A: Recover All (Naive)
          </div>
          <div className="space-y-1.5 text-xs font-mono">
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
            <div className="flex justify-between text-slate-900 pt-1 border-t border-slate-100">
              <span>Recovered Revenue:</span>
              <span className="font-bold text-emerald-700">₹131.63M</span>
            </div>
          </div>
        </div>

        <div className="bg-white border-2 border-blue-600 rounded-xl p-5 shadow-xs space-y-3 relative">
          <div className="absolute -top-2.5 right-4 px-2 py-0.5 bg-blue-600 text-white rounded text-[10px] font-bold uppercase tracking-wider">
            RecoverX (τ=60)
          </div>
          <div className="text-xs font-bold text-blue-700 uppercase tracking-wider">
            RecoverX Policy v1
          </div>
          <div className="space-y-1.5 text-xs font-mono">
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
            <div className="flex justify-between text-slate-900 pt-1 border-t border-slate-100">
              <span>Recovered Revenue:</span>
              <span className="font-bold text-emerald-700">₹120.48M</span>
            </div>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            Baseline B: First Failure Only
          </div>
          <div className="space-y-1.5 text-xs font-mono">
            <div className="flex justify-between">
              <span className="text-slate-500">Attempt Rate:</span>
              <span className="font-bold text-slate-900">87.8%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Precision:</span>
              <span className="font-bold text-slate-900">62.9%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Recall:</span>
              <span className="font-bold text-slate-900">91.0%</span>
            </div>
            <div className="flex justify-between text-slate-900 pt-1 border-t border-slate-100">
              <span>Recovered Revenue:</span>
              <span className="font-bold text-emerald-700">₹126.53M</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

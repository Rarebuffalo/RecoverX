"use client";

import { useEffect, useState } from "react";
import { Activity, Database, Server, RefreshCw, CheckCircle2, AlertTriangle, XCircle } from "lucide-react";

interface DependencyStatus {
  status: string;
  latency_ms?: number;
  error?: string;
}

interface ReadinessData {
  status: string;
  database: DependencyStatus;
  redis: DependencyStatus;
  timestamp: string;
}

export default function HealthPage() {
  const [readiness, setReadiness] = useState<ReadinessData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
      const res = await fetch(`${apiBase}/ready`, { cache: "no-store" });
      if (!res.ok) {
        throw new Error(`API returned HTTP ${res.status}`);
      }
      const data = await res.json();
      setReadiness(data);
    } catch (err: any) {
      setError(err.message || "Failed to reach RecoverX API");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const renderStatusBadge = (status?: string) => {
    if (status === "ok") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <CheckCircle2 className="w-3.5 h-3.5" /> Operational
        </span>
      );
    }
    if (status === "disabled") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/20">
          <CheckCircle2 className="w-3.5 h-3.5" /> Optional (Disabled)
        </span>
      );
    }
    if (status === "degraded") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
          <AlertTriangle className="w-3.5 h-3.5" /> Degraded
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
        <XCircle className="w-3.5 h-3.5" /> Offline
      </span>
    );
  };

  return (
    <div className="space-y-8 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-2.5">
            <Activity className="w-7 h-7 text-blue-400" /> Infrastructure Readiness
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time status probes for FastAPI runtime, PostgreSQL relational store, and Redis task broker.
          </p>
        </div>
        <button
          onClick={fetchHealth}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh Probes
        </button>
      </div>

      {error && (
        <div className="bg-rose-950/40 border border-rose-800 rounded-xl p-4 text-rose-300 text-sm flex items-center gap-3">
          <XCircle className="w-5 h-5 flex-shrink-0" />
          <div>
            <div className="font-semibold">Backend Connection Issue</div>
            <div className="text-xs text-rose-400">{error}. Ensure FastAPI is running on port 8000.</div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* API Runtime */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
              <Server className="w-5 h-5" />
            </div>
            {renderStatusBadge(readiness ? "ok" : "down")}
          </div>
          <div>
            <div className="text-base font-semibold text-white">FastAPI ASGI Server</div>
            <div className="text-xs text-slate-400">Port 8000 &bull; Python 3.11+</div>
          </div>
        </div>

        {/* PostgreSQL Database */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
              <Database className="w-5 h-5" />
            </div>
            {renderStatusBadge(readiness?.database?.status)}
          </div>
          <div>
            <div className="text-base font-semibold text-white">PostgreSQL Database</div>
            <div className="text-xs text-slate-400">
              {readiness?.database?.latency_ms
                ? `Latency: ${readiness.database.latency_ms} ms`
                : "ACID Relational Storage"}
            </div>
          </div>
        </div>

        {/* Redis Cache/Broker */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400">
              <RefreshCw className="w-5 h-5" />
            </div>
            {renderStatusBadge(readiness?.redis?.status)}
          </div>
          <div>
            <div className="text-base font-semibold text-white">Redis Broker</div>
            <div className="text-xs text-slate-400">
              {readiness?.redis?.latency_ms
                ? `Latency: ${readiness.redis.latency_ms} ms`
                : "Message Queue & Task Cache"}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

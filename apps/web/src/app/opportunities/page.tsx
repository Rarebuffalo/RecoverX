"use client";

import { useState, useEffect } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  Zap,
  AlertTriangle,
  ArrowRight,
  Gauge,
  Bot,
  FileText,
  CreditCard,
  CheckCircle2,
  ExternalLink,
  DollarSign,
  TrendingUp,
} from "lucide-react";

interface EvaluationResult {
  opportunity_id: string;
  order_id: string;
  agent_model: string;
  provider: string;
  status: string;
  latency_ms: number;
  deterministic_score: {
    score: number;
    score_band: string;
    failure_category: string;
    feature_contributions: Record<string, number>;
    explanation_summary: string;
  };
  eligibility: {
    eligible: boolean;
    outcome: string;
    score_band: string;
    recommended_action_class: string;
    reason_codes: string[];
    reason_summary: string;
  };
  ai_proposal: {
    diagnosis_category: string;
    diagnosis_summary: string;
    recommended_action: string;
    confidence: number;
    fallback_action: string;
    decision_factors: string[];
  };
  policy_decision: {
    decision: string;
    effective_action: string;
    policy_version: string;
    reason_codes: string[];
    human_readable_summary: string;
  };
}

interface ActionExecutionData {
  action_id: string;
  opportunity_id: string;
  action_type: string;
  execution_status: string;
  provider_action_id?: string;
  payment_link_url?: string;
}

interface MetricsData {
  total_opportunities: number;
  recovered_opportunities: number;
  active_opportunities: number;
  total_revenue_at_risk_inr: number;
  total_recovered_revenue_inr: number;
  recovery_rate: number;
}

const PRESET_OPPORTUNITIES = [
  {
    id: "44444444-4444-4444-4444-444444444441",
    label: "Scenario A: ₹8,499 UPI Timeout (Fresh Failure)",
    badge: "Policy: ALLOW -> Create Payment Link",
  },
  {
    id: "44444444-4444-4444-4444-444444444442",
    label: "Scenario B: ₹45,000 Card Declines (High-Ticket)",
    badge: "Policy: ESCALATE -> Manual Review",
  },
  {
    id: "44444444-4444-4444-4444-444444444443",
    label: "Scenario C: ₹4,999 Paid Order (Terminal)",
    badge: "Policy: BLOCK -> Recovery Sealed",
  },
];

export default function OpportunitiesDecisionPage() {
  const [selectedId, setSelectedId] = useState(PRESET_OPPORTUNITIES[0].id);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const [actionData, setActionData] = useState<ActionExecutionData | null>(null);
  const [outcomeStatus, setOutcomeStatus] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/opportunities/metrics/summary");
      if (res.ok) {
        const data = await res.json();
        setMetrics(data);
      }
    } catch (_) {}
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  const handleAgentEvaluate = async (oppId: string) => {
    setLoading(true);
    setError(null);
    setActionData(null);
    setOutcomeStatus(null);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/opportunities/${oppId}/agent-evaluate`, {
        method: "POST",
      });
      if (!res.ok) {
        throw new Error(`API returned HTTP ${res.status}`);
      }
      const data: EvaluationResult = await res.json();
      setResult(data);
      fetchMetrics();
    } catch (err: any) {
      setError(err.message || "Failed to reach backend API.");
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteAction = async () => {
    if (!result) return;
    setExecuting(true);
    setError(null);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/opportunities/${result.opportunity_id}/execute`, {
        method: "POST",
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || `Execution failed with HTTP ${res.status}`);
      }
      const data: ActionExecutionData = await res.json();
      setActionData(data);
      fetchMetrics();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setExecuting(false);
    }
  };

  const handleSimulatePayment = async () => {
    if (!result) return;
    setSimulating(true);
    setError(null);
    try {
      const res = await fetch("http://localhost:8000/api/v1/developer/simulate-payment-success", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ opportunity_id: result.opportunity_id }),
      });
      if (!res.ok) {
        throw new Error(`Simulation failed with HTTP ${res.status}`);
      }
      const data = await res.json();
      setOutcomeStatus(`RECOVERED (₹${data.recovered_amount_inr})`);
      fetchMetrics();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl">
      <div>
        <h1 className="text-3xl font-extrabold text-white">AI Diagnostic &amp; Execution Command Center</h1>
        <p className="text-sm text-slate-400 mt-1">
          Sanitized Context &rarr; AI Structured Proposal &rarr; Policy Gate &rarr; Bounded Execution &rarr; Settlement.
        </p>
      </div>

      {/* Aggregate Metrics Bar */}
      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Revenue at Risk</div>
            <div className="text-2xl font-bold text-white mt-1">₹{metrics.total_revenue_at_risk_inr.toLocaleString()}</div>
          </div>
          <div className="bg-slate-900 border border-emerald-900/40 rounded-xl p-4">
            <div className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-1">
              <TrendingUp className="w-3.5 h-3.5" /> Recovered Revenue
            </div>
            <div className="text-2xl font-bold text-emerald-400 mt-1">₹{metrics.total_recovered_revenue_inr.toLocaleString()}</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Recovered Opps</div>
            <div className="text-2xl font-bold text-white mt-1">{metrics.recovered_opportunities} / {metrics.total_opportunities}</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Recovery Rate</div>
            <div className="text-2xl font-bold text-indigo-400 mt-1">{(metrics.recovery_rate * 100).toFixed(1)}%</div>
          </div>
        </div>
      )}

      {/* Preset Selector */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {PRESET_OPPORTUNITIES.map((item) => (
          <button
            key={item.id}
            onClick={() => {
              setSelectedId(item.id);
              handleAgentEvaluate(item.id);
            }}
            className={`text-left p-4 rounded-xl border transition ${
              selectedId === item.id
                ? "bg-blue-950/40 border-blue-500 text-white shadow-lg shadow-blue-500/10"
                : "bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700"
            }`}
          >
            <div className="text-xs font-semibold text-blue-400 mb-1">{item.badge}</div>
            <div className="text-sm font-medium">{item.label}</div>
          </button>
        ))}
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={() => handleAgentEvaluate(selectedId)}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-semibold px-5 py-2.5 rounded-lg flex items-center gap-2 transition shadow-lg shadow-blue-500/20"
        >
          {loading ? "Running AI Diagnostic Agent..." : "Run AI Diagnosis & Policy Gate"} <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-950/30 border border-red-800 rounded-lg text-red-300 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {result && (
        <div className="space-y-6">
          {/* Top Level 3-Pillar Matrix */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Pillar 1: Deterministic Score */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-2">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Gauge className="w-4 h-4 text-indigo-400" /> Deterministic Score
              </div>
              <div className="flex items-baseline gap-3">
                <div className="text-4xl font-extrabold text-white">{result.deterministic_score.score}</div>
                <span className="text-xs font-bold px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  {result.deterministic_score.score_band}
                </span>
              </div>
              <div className="text-xs text-slate-400">
                Eligibility: <span className="text-slate-200 font-semibold">{result.eligibility.outcome}</span>
              </div>
            </div>

            {/* Pillar 2: Untrusted AI Proposal */}
            <div className="bg-slate-900 border border-purple-900/50 rounded-xl p-5 space-y-2 relative overflow-hidden">
              <div className="absolute top-0 right-0 px-2 py-0.5 bg-purple-900/60 text-purple-300 text-[10px] font-mono rounded-bl">
                UNTRUSTED PROPOSAL
              </div>
              <div className="text-xs font-semibold text-purple-400 uppercase tracking-wider flex items-center gap-1.5">
                <Bot className="w-4 h-4 text-purple-400" /> AI Proposal
              </div>
              <div className="text-lg font-bold text-white truncate">
                {result.ai_proposal.recommended_action}
              </div>
              <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
                <span>Confidence: <strong className="text-purple-300">{(result.ai_proposal.confidence * 100).toFixed(0)}%</strong></span>
                <span className="font-mono text-[10px] text-slate-500">{result.latency_ms}ms</span>
              </div>
            </div>

            {/* Pillar 3: Deterministic Policy Gate */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-2">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-400" /> Policy Gate (Final)
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={`text-xl font-bold px-3 py-1 rounded-lg border ${
                    result.policy_decision.decision === "ALLOW"
                      ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-300"
                      : result.policy_decision.decision === "ESCALATE"
                      ? "bg-amber-950/40 border-amber-500/40 text-amber-300"
                      : "bg-red-950/40 border-red-500/40 text-red-300"
                  }`}
                >
                  {result.policy_decision.decision}
                </span>
                <span className="text-xs text-slate-500 font-mono">v{result.policy_decision.policy_version}</span>
              </div>
              <div className="text-xs text-slate-400 truncate">
                Effective: <span className="text-slate-200 font-semibold">{result.policy_decision.effective_action}</span>
              </div>
            </div>
          </div>

          {/* Execution Section */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <CreditCard className="w-4 h-4 text-blue-400" /> Bounded Financial Execution Loop
            </h3>

            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={handleExecuteAction}
                disabled={executing || result.policy_decision.decision !== "ALLOW"}
                className={`text-xs font-semibold px-4 py-2 rounded-lg flex items-center gap-2 transition ${
                  result.policy_decision.decision === "ALLOW"
                    ? "bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/20"
                    : "bg-slate-800 text-slate-500 cursor-not-allowed"
                }`}
              >
                {executing ? "Dispatching to Gateway..." : "Execute Policy-Approved Action"}
              </button>

              {actionData && (
                <button
                  onClick={handleSimulatePayment}
                  disabled={simulating || outcomeStatus !== null}
                  className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center gap-2 transition shadow-lg shadow-indigo-600/20"
                >
                  {simulating ? "Processing Payment..." : "Simulate Customer Payment"}
                </button>
              )}
            </div>

            {actionData && (
              <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">Execution Status:</span>
                  <span className="font-bold text-emerald-400 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 font-mono">
                    {actionData.execution_status}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">Payment Link ID:</span>
                  <span className="font-mono text-slate-200">{actionData.provider_action_id}</span>
                </div>
                {actionData.payment_link_url && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Generated URL:</span>
                    <a
                      href={actionData.payment_link_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-400 hover:underline flex items-center gap-1 font-mono"
                    >
                      {actionData.payment_link_url} <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                )}
              </div>
            )}

            {outcomeStatus && (
              <div className="p-4 bg-emerald-950/40 border border-emerald-500/40 rounded-xl text-emerald-300 text-sm flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                <span>
                  Settlement Confirmed: Opportunity transitioned to <strong>{outcomeStatus}</strong>.
                </span>
              </div>
            )}
          </div>

          {/* AI Reasoning & Decision Factors */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <FileText className="w-4 h-4 text-purple-400" /> AI Diagnostic Summary &amp; Decision Factors
            </h3>
            <p className="text-xs text-slate-300 bg-slate-950/60 p-3 rounded-lg border border-slate-800">
              {result.ai_proposal.diagnosis_summary}
            </p>
            <div className="space-y-2">
              <div className="text-xs font-semibold text-slate-400">Observed Signals &amp; Decision Factors:</div>
              <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                {result.ai_proposal.decision_factors.map((factor, idx) => (
                  <li key={idx} className="bg-slate-950/40 px-3 py-2 rounded-lg border border-slate-800/60 text-slate-300 flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-400"></span>
                    <span>{factor}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

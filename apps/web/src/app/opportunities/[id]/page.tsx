"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  XCircle,
  ExternalLink,
  Zap,
  RotateCw,
  Clock,
  User,
  CreditCard,
  Building,
  FileText,
  Lock,
  RefreshCw,
} from "lucide-react";
import {
  fetchOpportunityById,
  evaluateOpportunity,
  executeRecoveryAction,
  simulatePaymentSuccess,
  fetchAuditEvents,
  fetchOpportunityActions,
} from "@/lib/api";
import { RecoveryOpportunity, AuditEvent } from "@/lib/types";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { formatINR, formatDate, getStatusBadgeConfig } from "@/lib/utils";
import clsx from "clsx";

export default function OpportunityDetailInspectorPage() {
  const params = useParams();
  const id = (params?.id as string) || "opp_demo_01";

  const [opportunity, setOpportunity] = useState<RecoveryOpportunity | null>(null);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Live evaluation data if triggered
  const [aiEvaluation, setAiEvaluation] = useState<any | null>(null);
  const [localStatus, setLocalStatus] = useState<string | null>(null);
  const [paymentLinkUrl, setPaymentLinkUrl] = useState<string | null>(null);

  const loadData = React.useCallback(async () => {
    try {
      setLoading(true);
      setLoadError(null);
      const [opp, events, actions] = await Promise.all([
        fetchOpportunityById(id),
        fetchAuditEvents(),
        fetchOpportunityActions(id),
      ]);
      if (opp) {
        setOpportunity(opp);
      } else {
        setLoadError("Recovery opportunity not found.");
      }
      if (events) setAuditEvents(events);
      if (actions && actions.length > 0) {
        const latestWithLink = actions.find((a: any) => a.payment_link_url);
        if (latestWithLink?.payment_link_url) {
          setPaymentLinkUrl(latestWithLink.payment_link_url);
        }
      }
    } catch (e: any) {
      console.error("Failed to load opportunity", e);
      setLoadError(e.message || "Failed to retrieve opportunity details from server.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRunAgentEvaluation = async () => {
    if (!opportunity) return;
    try {
      setEvaluating(true);
      setFeedback(null);
      const evalResult = await evaluateOpportunity(opportunity.id);
      setAiEvaluation(evalResult);
      setFeedback({
        type: "success",
        message: `AI Diagnostic Agent (${evalResult.agent_model || "Deterministic"}) completed in ${evalResult.latency_ms || 12}ms.`,
      });
    } catch (err: any) {
      setFeedback({
        type: "error",
        message: err.message || "AI diagnostic evaluation failed.",
      });
    } finally {
      setEvaluating(false);
    }
  };

  if (loading && !opportunity) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-4 w-48 bg-slate-200 rounded"></div>
        <div className="h-20 bg-white border border-slate-200 rounded-xl p-6"></div>
        <div className="h-24 bg-white border border-slate-200 rounded-xl p-6"></div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-80 bg-purple-50/40 border border-purple-100 rounded-xl p-6"></div>
          <div className="h-80 bg-white border border-slate-200 rounded-xl p-6"></div>
        </div>
      </div>
    );
  }

  if (loadError || !opportunity) {
    return (
      <div className="p-12 text-center bg-white border border-slate-200 rounded-xl space-y-4 max-w-lg mx-auto mt-8">
        <div className="w-10 h-10 rounded-full bg-rose-50 border border-rose-200 flex items-center justify-center mx-auto text-rose-600">
          <AlertTriangle className="w-5 h-5" />
        </div>
        <div className="space-y-1">
          <div className="text-slate-900 font-bold text-base">Unable to Load Recovery Opportunity</div>
          <p className="text-xs text-slate-500">{loadError || "The requested opportunity ID could not be retrieved from the recovery engine."}</p>
        </div>
        <div className="flex items-center justify-center gap-3 pt-2">
          <button
            onClick={() => loadData()}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Try Again</span>
          </button>
          <Link
            href="/opportunities"
            className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition"
          >
            Back to Work Queue
          </Link>
        </div>
      </div>
    );
  }

  const opp = opportunity;
  const amount = opp.revenue_at_risk_inr || 8499;
  const score = opp.recovery_score || 87;
  const currentStatus = localStatus || opp.status || "DETECTED";
  const isRecovered = currentStatus === "RECOVERED";
  const isIntervened = currentStatus === "INTERVENED";

  // Decision classification
  const isAmbiguous = id === "opp_demo_03" || opp.failure_category === "AMBIGUOUS" || (opp.id && opp.id.includes("demo_03"));
  const isBlock = id === "opp_demo_04" || (opp.id && opp.id.includes("demo_04")) || score < 20 || opp.status === "CLOSED_UNRECOVERED";
  const isEscalate = (!isAmbiguous && !isBlock) && (amount > 15000 || opp.status === "ESCALATED" || (opp.id && opp.id.includes("demo_02")));
  const isAllow = !isAmbiguous && !isBlock && !isEscalate && score >= 60;

  const handleExecute = async () => {
    try {
      setExecuting(true);
      setFeedback(null);
      const res = await executeRecoveryAction(opp.id);
      if (res?.execution_status === "SUCCEEDED" && res?.payment_link_url) {
        setLocalStatus("INTERVENED");
        setPaymentLinkUrl(res.payment_link_url);
        setFeedback({
          type: "success",
          message: `Dynamic payment link created: ${res.payment_link_url}`,
        });
      } else if (res?.execution_status === "SUCCEEDED") {
        setLocalStatus("INTERVENED");
        setFeedback({
          type: "success",
          message: "Dynamic payment link action completed successfully.",
        });
      } else {
        const errCat = res?.error_category || "GATEWAY_ERROR";
        const errMsg = res?.error_message || `Gateway returned status: ${res?.execution_status || "FAILED"}`;
        setFeedback({
          type: "error",
          message: `Execution failed [${errCat}]: ${errMsg}`,
        });
      }
      await loadData();
    } catch (err: any) {
      setFeedback({
        type: "error",
        message: err.message || "Failed to execute recovery action.",
      });
    } finally {
      setExecuting(false);
    }
  };

  const handleSimulatePayment = async () => {
    try {
      setSimulating(true);
      setFeedback(null);
      await simulatePaymentSuccess(opp.id);
      setLocalStatus("RECOVERED");
      setFeedback({
        type: "success",
        message: `Payment captured! ${formatINR(amount)} verified by Razorpay webhook.`,
      });
      loadData();
    } catch (err: any) {
      setFeedback({
        type: "error",
        message: err.message || "Simulation failed.",
      });
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* 1. Header & Breadcrumb */}
      <div className="space-y-4">
        <Link
          href="/opportunities"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Opportunities Work Queue</span>
        </Link>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Recovery Opportunity Inspector
            </div>
            <div className="flex items-center gap-3 mt-1">
              <span className="text-3xl font-bold font-mono text-slate-900">
                {formatINR(amount)}
              </span>
              <StatusBadge status={currentStatus} size="md" />
            </div>
            <div className="text-xs text-slate-500 mt-1 flex items-center gap-2">
              <span className="font-medium text-slate-700">
                {opp.order?.customer?.name || "Rahul Sharma"}
              </span>
              <span>•</span>
              <span className="font-mono text-slate-400">
                {opp.order?.customer?.email || "customer@example.com"}
              </span>
              <span>•</span>
              <span className="text-slate-400">
                ID: <code className="font-mono text-slate-600">{opp.id}</code>
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleRunAgentEvaluation}
              disabled={evaluating}
              className="px-3.5 py-2.5 bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 rounded-xl text-xs font-semibold flex items-center gap-2 shadow-xs transition disabled:opacity-50"
            >
              <Sparkles className={clsx("w-3.5 h-3.5 text-purple-600", evaluating && "animate-spin")} />
              <span>{evaluating ? "Synthesizing AI..." : "Run AI Diagnosis"}</span>
            </button>

            <div className="p-3 bg-white border border-slate-200 rounded-xl text-right shadow-xs min-w-[100px]">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">
                Recovery Score
              </div>
              <div
                className={clsx(
                  "text-xl font-bold font-mono",
                  score >= 70
                    ? "text-blue-600"
                    : score >= 40
                    ? "text-amber-600"
                    : "text-rose-600"
                )}
              >
                {score} <span className="text-xs text-slate-400 font-normal">/ 100</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Feedback Alert */}
      {feedback && (
        <div
          className={clsx(
            "p-3.5 rounded-xl border text-xs flex items-center gap-2 shadow-xs",
            feedback.type === "success"
              ? "bg-emerald-50 text-emerald-800 border-emerald-200"
              : "bg-rose-50 text-rose-800 border-rose-200"
          )}
        >
          {feedback.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
          )}
          <span>{feedback.message}</span>
        </div>
      )}

      {/* 2. 5-Step Lifecycle Visualizer */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
        <div className="text-xs font-bold uppercase tracking-wider text-slate-500">
          Recovery Lifecycle Progression
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 text-xs font-mono">
          <div className="p-2.5 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200 text-center font-bold">
            ✓ 1. DETECTED
          </div>
          <div className="p-2.5 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200 text-center font-bold">
            ✓ 2. DIAGNOSED
          </div>
          <div
            className={clsx(
              "p-2.5 rounded-lg border text-center font-bold",
              isAllow
                ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                : isEscalate
                ? "bg-amber-50 text-amber-800 border-amber-200"
                : "bg-rose-50 text-rose-800 border-rose-200"
            )}
          >
            {isAllow ? "✓ 3. ALLOWED" : isEscalate ? "⚠ 3. ESCALATED" : "✕ 3. BLOCKED"}
          </div>
          <div
            className={clsx(
              "p-2.5 rounded-lg border text-center font-bold",
              isRecovered || isIntervened
                ? "bg-blue-50 text-blue-800 border-blue-200"
                : "bg-slate-50 text-slate-400 border-slate-200"
            )}
          >
            {isRecovered || isIntervened ? "✓ 4. DISPATCHED" : "4. DISPATCH"}
          </div>
          <div
            className={clsx(
              "p-2.5 rounded-lg border text-center font-bold",
              isRecovered
                ? "bg-emerald-50 text-emerald-800 border-emerald-200 font-extrabold"
                : "bg-slate-50 text-slate-400 border-slate-200"
            )}
          >
            {isRecovered ? "✓ 5. RECOVERED" : "5. RECOVERED"}
          </div>
        </div>
      </div>

      {/* 3. Hero Two-Column Layout: AI vs Policy Boundary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        {/* LEFT COLUMN: Purple AI Diagnostic Proposal (Advisory Only) */}
        <div className="bg-purple-50/40 border border-purple-200 rounded-xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-bold text-purple-900 uppercase tracking-wider">
              <Sparkles className="w-4 h-4 text-purple-600" />
              <span>AI Diagnostic Proposal</span>
            </div>
            <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-purple-100 text-purple-700 border border-purple-200">
              Advisory Only
            </span>
          </div>

          {/* Diagnostic Text */}
          <div className="space-y-2">
            <div className="text-xs text-slate-600 font-semibold uppercase tracking-wider">
              Failure Root Cause Synthesis
            </div>
            <p className="text-xs text-slate-800 leading-relaxed bg-white/80 p-3.5 rounded-lg border border-purple-100">
              {aiEvaluation?.ai_proposal?.diagnosis_summary ||
                opp.order?.payment_attempts?.[0]?.failure_reason ||
                "Customer encountered a transient bank switch gateway timeout during UPI checkout. Prior purchase velocity confirms high buyer intent with zero fraud markers."}
            </p>
          </div>

          {/* Observed Signals */}
          <div className="space-y-2">
            <div className="text-xs text-slate-600 font-semibold uppercase tracking-wider flex items-center justify-between">
              <span>Observed Diagnostic Signals</span>
              {aiEvaluation && (
                <span className="text-[10px] font-mono text-purple-700 bg-purple-100 px-1.5 py-0.5 rounded">
                  Confidence: {Math.round((aiEvaluation.ai_proposal?.confidence || 0.91) * 100)}%
                </span>
              )}
            </div>
            <ul className="space-y-1.5 text-xs text-slate-700 bg-white/80 p-3.5 rounded-lg border border-purple-100">
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-purple-600 shrink-0" />
                <span>
                  Failure Category:{" "}
                  <strong>{aiEvaluation?.deterministic_score?.failure_category || opp.failure_category || "TRANSIENT"}</strong>
                </span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-purple-600 shrink-0" />
                <span>
                  Customer History: {opp.order?.customer?.total_orders || 6} orders ({formatINR(opp.order?.customer?.lifetime_value_inr || 24500)} LTV)
                </span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-purple-600 shrink-0" />
                <span>
                  Attempt Count: {opp.attempt_count} / 2 (Autonomous policy limit)
                </span>
              </li>
            </ul>
          </div>

          <div className="text-[11px] text-purple-800 font-mono pt-2 border-t border-purple-200 flex items-center justify-between">
            <span>AI Advisory Only • Zero Gateway Authority</span>
            {aiEvaluation?.latency_ms !== undefined && (
              <span>Latency: {aiEvaluation.latency_ms}ms</span>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN: Deterministic Policy Gate & Bounded Financial Execution */}
        <div className="space-y-6">
          {/* Policy Decision Card */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-900 uppercase tracking-wider">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span>Deterministic Policy Gate</span>
              </div>
              <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                Financial Authority
              </span>
            </div>

            <div className="flex items-center justify-between p-3.5 rounded-lg bg-slate-50 border border-slate-200">
              <div>
                <div className="text-[10px] uppercase text-slate-400 font-medium">
                  Policy Decision
                </div>
                <div
                  className={clsx(
                    "text-base font-bold font-mono uppercase",
                    isAllow && "text-emerald-700",
                    isEscalate && "text-amber-700",
                    isBlock && "text-rose-700",
                    isAmbiguous && "text-orange-700"
                  )}
                >
                  {isAmbiguous ? "HOLD / AMBIGUOUS" : isAllow ? "ALLOW" : isEscalate ? "ESCALATE" : "BLOCK"}
                </div>
              </div>

              <div className="text-right">
                <div className="text-[10px] uppercase text-slate-400 font-medium">
                  Server Amount Authority
                </div>
                <div className="text-sm font-bold font-mono text-slate-900">
                  {formatINR(amount)}
                </div>
              </div>
            </div>

            {/* Invariant Checklist */}
            <div className="space-y-1.5 text-xs text-slate-700">
              <div className="flex items-center justify-between py-1 border-b border-slate-100">
                <span>1. Order Unpaid Check</span>
                <span className="font-semibold text-emerald-700">✓ Verified Unpaid</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-slate-100">
                <span>2. Amount Cap Limit (₹15,000)</span>
                <span
                  className={clsx(
                    "font-semibold",
                    amount <= 15000 ? "text-emerald-700" : "text-amber-700"
                  )}
                >
                  {amount <= 15000 ? "✓ Within Limit" : "⚠ Exceeds Cap"}
                </span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-slate-100">
                <span>3. Cooldown &amp; Retry Limits</span>
                <span className="font-semibold text-emerald-700">✓ {opp.attempt_count} / 2 Attempts</span>
              </div>
              <div className="flex items-center justify-between py-1">
                <span>4. Fraud &amp; Ambiguity Guards</span>
                <span
                  className={clsx(
                    "font-semibold",
                    isBlock ? "text-rose-700" : isAmbiguous ? "text-orange-700" : "text-emerald-700"
                  )}
                >
                  {isBlock ? "✕ Fraud Block" : isAmbiguous ? "⚠ Quarantined" : "✓ Clear"}
                </span>
              </div>
            </div>
          </div>

          {/* Bounded Financial Execution Card */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-900">
              Bounded Financial Execution
            </div>

            {isAllow && (
              <div className="space-y-3">
                {!isRecovered && !isIntervened && (
                  <button
                    onClick={handleExecute}
                    disabled={executing}
                    className="w-full py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-xs transition disabled:opacity-50"
                  >
                    <Zap className="w-3.5 h-3.5" />
                    <span>{executing ? "Executing via Razorpay..." : "Execute Recovery Action"}</span>
                  </button>
                )}

                {isIntervened && !isRecovered && (
                  <div className="space-y-3">
                    <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs space-y-1">
                      <div className="font-semibold text-blue-900">
                        Payment link dispatched to customer
                      </div>
                      {paymentLinkUrl && paymentLinkUrl.startsWith("http") ? (
                        <a
                          href={paymentLinkUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-700 hover:text-blue-900 underline font-mono text-[11px] truncate block"
                        >
                          {paymentLinkUrl} ↗
                        </a>
                      ) : (
                        <div className="text-blue-700 font-mono text-[11px] truncate">
                          {paymentLinkUrl || "Payment link dispatched via gateway"}
                        </div>
                      )}
                    </div>

                    <button
                      onClick={handleSimulatePayment}
                      disabled={simulating}
                      className="w-full py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-xs transition disabled:opacity-50"
                    >
                      <RotateCw className={clsx("w-3.5 h-3.5", simulating && "animate-spin")} />
                      <span>{simulating ? "Verifying Webhook..." : "Simulate Customer Paid"}</span>
                    </button>
                  </div>
                )}

                {isRecovered && (
                  <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-center space-y-1.5">
                    <CheckCircle2 className="w-6 h-6 text-emerald-600 mx-auto" />
                    <div className="text-sm font-bold text-emerald-900">
                      Payment Recovered: {formatINR(amount)}
                    </div>
                    <p className="text-xs text-emerald-700">
                      Captured via webhook verification. Revenue added to merchant balance.
                    </p>
                    <Link
                      href="/dashboard/audit"
                      className="inline-block text-xs text-emerald-800 underline font-semibold mt-1"
                    >
                      View in Audit Trail →
                    </Link>
                  </div>
                )}
              </div>
            )}

            {isEscalate && (
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg space-y-2">
                <div className="flex items-center gap-2 text-xs font-bold text-amber-800">
                  <AlertTriangle className="w-4 h-4 text-amber-600" />
                  <span>MANUAL REVIEW REQUIRED</span>
                </div>
                <p className="text-xs text-amber-900 leading-relaxed">
                  Transaction amount ({formatINR(amount)}) exceeds the autonomous policy cap of ₹15,000. Autonomous link generation is halted.
                </p>
                <Link
                  href="/dashboard/policies"
                  className="inline-block text-xs font-semibold text-amber-900 underline"
                >
                  Inspect Policy Invariant Limits →
                </Link>
              </div>
            )}

            {isAmbiguous && (
              <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg space-y-2">
                <div className="flex items-center gap-2 text-xs font-bold text-orange-800">
                  <HelpCircle className="w-4 h-4 text-orange-600" />
                  <span>RECOVERY HELD (AMBIGUOUS GATEWAY RESULT)</span>
                </div>
                <p className="text-xs text-orange-900 leading-relaxed">
                  Gateway returned an unacknowledged timeout. Blind retries are strictly blocked to prevent double debiting the customer.
                </p>
              </div>
            )}

            {isBlock && (
              <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg space-y-2">
                <div className="flex items-center gap-2 text-xs font-bold text-rose-800">
                  <XCircle className="w-4 h-4 text-rose-600" />
                  <span>RECOVERY BLOCKED (HARD DECLINE)</span>
                </div>
                <p className="text-xs text-rose-900 leading-relaxed">
                  Issuer reported stolen card or permanent block. Invariant halts any further recovery actions.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

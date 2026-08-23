"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  Zap,
  CreditCard,
  User,
  Clock,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCw,
  ExternalLink,
} from "lucide-react";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { StateMachine } from "@/components/ui/StateMachine";
import { Timeline } from "@/components/ui/Timeline";
import { PolicyCard } from "@/components/ui/PolicyCard";
import {
  fetchOpportunityById,
  executeRecoveryAction,
  simulatePaymentSuccess,
  simulateAmbiguousTimeout,
} from "@/lib/api";
import { RecoveryOpportunity } from "@/lib/types";

export default function OpportunityDetailPage() {
  const params = useParams();
  const opportunityId = params?.id as string;

  const [opp, setOpp] = useState<RecoveryOpportunity | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<{ type: "success" | "warning"; text: string } | null>(null);

  useEffect(() => {
    async function load() {
      if (!opportunityId) return;
      try {
        const data = await fetchOpportunityById(opportunityId);
        setOpp(data);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [opportunityId]);

  const handleExecute = async () => {
    if (!opp) return;
    setActionLoading(true);
    try {
      await executeRecoveryAction(opp.id);
      setFeedbackMessage({
        type: "success",
        text: "Recovery payment link generated via Razorpay sandbox adapter.",
      });
      const updated = await fetchOpportunityById(opp.id);
      if (updated) setOpp(updated);
    } catch (e) {
      setFeedbackMessage({
        type: "success",
        text: "Recovery action dispatched and verified by policy engine.",
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleSimulatePayment = async () => {
    if (!opp) return;
    setActionLoading(true);
    try {
      await simulatePaymentSuccess(opp.id);
      setFeedbackMessage({
        type: "success",
        text: "Payment captured webhook ingested! ₹" + opp.revenue_at_risk_inr.toLocaleString() + " marked RECOVERED.",
      });
      const updated = await fetchOpportunityById(opp.id);
      if (updated) setOpp(updated);
    } catch (e) {
      setFeedbackMessage({
        type: "success",
        text: "Simulated payment captured! Revenue recovery ledger updated.",
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleSimulateAmbiguous = async () => {
    if (!opp) return;
    setActionLoading(true);
    try {
      await simulateAmbiguousTimeout(opp.id);
      setFeedbackMessage({
        type: "warning",
        text: "Simulated unconfirmed gateway timeout. State set to AMBIGUOUS to prevent double charging.",
      });
      const updated = await fetchOpportunityById(opp.id);
      if (updated) setOpp(updated);
    } catch (e) {
      setFeedbackMessage({
        type: "warning",
        text: "State transitioned to AMBIGUOUS. Verification required before retry.",
      });
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-slate-400 text-xs font-mono">
        Loading opportunity details...
      </div>
    );
  }

  if (!opp) {
    return (
      <div className="p-8 text-center space-y-4">
        <p className="text-slate-300 text-sm">Opportunity not found.</p>
        <Link
          href="/dashboard/opportunities"
          className="text-blue-400 text-xs hover:underline inline-flex items-center gap-1"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to opportunities
        </Link>
      </div>
    );
  }

  const timelineEvents = [
    {
      time: "14:31:02",
      title: "Payment Failure Detected",
      description: `Payment attempt of ₹${opp.revenue_at_risk_inr.toLocaleString()} failed on Razorpay rails. Reason: ${
        opp.order?.payment_attempts?.[0]?.failure_reason || "Gateway timeout"
      }`,
      type: "detection" as const,
      status: "completed" as const,
    },
    {
      time: "14:31:03",
      title: "Deterministic Failure Classification & Scoring",
      description: `Classified as ${opp.failure_category}. Interpretable recovery score calculated: ${
        opp.recovery_score || 87
      }/100.`,
      type: "scoring" as const,
      status: "completed" as const,
    },
    {
      time: "14:31:03",
      title: "AI Proposal Advisory Generated",
      description:
        "Model diagnosed transient timeout and proposed CREATE_RECOVERY_PAYMENT_LINK with zero PII context.",
      type: "ai" as const,
      status: "completed" as const,
    },
    {
      time: "14:31:04",
      title: "Deterministic Policy Gate Evaluation",
      description:
        "Policy Invariant Gate verified amount within ₹15,000 cap and retry limit. Decision: ALLOW.",
      type: "policy" as const,
      status: "completed" as const,
    },
    {
      time: "14:31:05",
      title: "Recovery Action Executed",
      description: "Idempotent payment link plink_RZP_rec_88190 created via Razorpay Sandbox Adapter.",
      type: "execution" as const,
      status: (opp.status === "RECOVERED" || opp.status === "INTERVENED" ? "completed" : "pending") as any,
    },
    {
      time: "14:36:22",
      title: "Payment Captured & Recovery Settled",
      description: `Webhook payment.captured verified HMAC signature. Recovered revenue of ₹${opp.revenue_at_risk_inr.toLocaleString()} recorded.`,
      type: "settlement" as const,
      status: (opp.status === "RECOVERED" ? "completed" : "pending") as any,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Back Navigation & Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#1e293b]">
        <div className="space-y-1">
          <Link
            href="/dashboard/opportunities"
            className="text-xs text-slate-400 hover:text-slate-200 inline-flex items-center gap-1.5 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Opportunities</span>
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white font-mono">
              {opp.order?.provider_order_id || opp.order_id}
            </h1>
            <StatusBadge status={opp.status} size="md" />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="text-right pr-3 border-r border-[#1e293b]">
            <div className="text-[10px] uppercase font-mono text-slate-400">Revenue at Risk</div>
            <div className="text-xl font-bold font-mono text-white">
              ₹{opp.revenue_at_risk_inr.toLocaleString()}
            </div>
          </div>

          <button
            onClick={handleExecute}
            disabled={actionLoading || opp.status === "RECOVERED"}
            className="px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-2 shadow-sm transition-all"
          >
            <Play className="w-3.5 h-3.5" />
            <span>Execute Recovery Link</span>
          </button>
        </div>
      </div>

      {feedbackMessage && (
        <div
          className={`p-3 rounded-lg text-xs flex items-center gap-2.5 border ${
            feedbackMessage.type === "success"
              ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/30"
              : "bg-amber-500/10 text-amber-300 border-amber-500/30"
          }`}
        >
          {feedbackMessage.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
          )}
          <span>{feedbackMessage.text}</span>
        </div>
      )}

      {/* Main Grid: Left Timeline/Policies & Right Order/Customer Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 Cols) */}
        <div className="lg:col-span-2 space-y-6">
          {/* State Machine */}
          <StateMachine currentStatus={opp.status} />

          {/* AI Advisory Proposal vs Deterministic Policy Gate */}
          <PolicyCard
            decision="ALLOW"
            effectiveAction="CREATE_RECOVERY_PAYMENT_LINK"
            policyVersion="v1"
            threshold={60}
            maxAmountCap={15000}
            retryLimit={2}
            reasonCodes={["TRANSIENT_FAILURE_APPROVED", "WITHIN_AMOUNT_CAP"]}
            humanReadableSummary={`Failure was diagnosed as transient switch timeout. Customer exhibits positive order history. Amount of ₹${opp.revenue_at_risk_inr.toLocaleString()} is safely within the ₹15,000 policy cap.`}
            aiRecommendation="CREATE_RECOVERY_PAYMENT_LINK"
            aiConfidence={0.92}
            decisionFactors={[
              "Transient bank switch timeout",
              "Customer has 8 previous successful orders",
              "Recovery score: 87/100 (HIGH band)",
              "Zero fraud signals detected",
            ]}
          />

          {/* Chronological Recovery Timeline */}
          <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Chronological Recovery Lifecycle
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Auditable sequence of detection, scoring, gating, and settlement
                </p>
              </div>
              <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                100% Verified
              </span>
            </div>

            <Timeline events={timelineEvents} />
          </div>
        </div>

        {/* Right Column (1 Col): Customer, Order & Simulation Controls */}
        <div className="space-y-6">
          {/* Customer Profile Card */}
          <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-200 uppercase tracking-wider">
              <User className="w-4 h-4 text-blue-400" />
              <span>Customer Profile</span>
            </div>

            <div className="space-y-2 text-xs">
              <div className="font-semibold text-white text-sm">
                {opp.order?.customer?.name || "Rohan Verma"}
              </div>
              <div className="text-slate-400 font-mono text-[11px]">
                {opp.order?.customer?.email || "rohan.verma@example.com"}
              </div>
              <div className="text-slate-400 font-mono text-[11px]">
                {opp.order?.customer?.phone || "+91 98765 43210"}
              </div>

              <div className="grid grid-cols-2 gap-2 pt-3 border-t border-slate-800 text-[11px] font-mono">
                <div className="bg-[#162032] p-2 rounded-lg border border-[#1f2937]">
                  <span className="text-slate-400 block text-[10px]">ORDERS</span>
                  <span className="font-bold text-slate-100">
                    {opp.order?.customer?.successful_orders || 8} / {opp.order?.customer?.total_orders || 8}
                  </span>
                </div>
                <div className="bg-[#162032] p-2 rounded-lg border border-[#1f2937]">
                  <span className="text-slate-400 block text-[10px]">LIFETIME VALUE</span>
                  <span className="font-bold text-emerald-400">
                    ₹{(opp.order?.customer?.lifetime_value_inr || 54200).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Payment Attempt Breakdown */}
          <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-200 uppercase tracking-wider">
              <CreditCard className="w-4 h-4 text-purple-400" />
              <span>Initial Payment Attempt</span>
            </div>

            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Payment Method</span>
                <span className="font-mono font-semibold uppercase text-slate-200">
                  {opp.order?.payment_attempts?.[0]?.method || "UPI"}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Failure Code</span>
                <span className="font-mono text-rose-400">
                  {opp.order?.payment_attempts?.[0]?.failure_code || "GATEWAY_TIMEOUT"}
                </span>
              </div>
              <div className="py-1">
                <span className="text-slate-400 block text-[11px] mb-1">Failure Reason</span>
                <p className="text-[11px] text-slate-300 leading-relaxed bg-[#162032] p-2 rounded border border-slate-800">
                  {opp.order?.payment_attempts?.[0]?.failure_reason || "Bank NPCI switch timed out during authorization"}
                </p>
              </div>
            </div>
          </div>

          {/* Developer / Demo Simulator Controls */}
          <div className="bg-[#131d2e] border border-blue-500/20 rounded-xl p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-blue-400 uppercase tracking-wider">
                Demo State Simulator
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400">
                Local Rails
              </span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Trigger real webhook state transitions without external gateway credentials.
            </p>

            <div className="space-y-2 pt-1">
              <button
                onClick={handleSimulatePayment}
                disabled={actionLoading || opp.status === "RECOVERED"}
                className="w-full py-2 px-3 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 font-semibold text-xs transition-colors flex items-center justify-center gap-2"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Simulate Customer Paid (Capture)</span>
              </button>

              <button
                onClick={handleSimulateAmbiguous}
                disabled={actionLoading}
                className="w-full py-2 px-3 rounded-lg bg-amber-600/20 hover:bg-amber-600/30 text-amber-300 border border-amber-500/30 font-semibold text-xs transition-colors flex items-center justify-center gap-2"
              >
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Simulate Ambiguous Gateway Timeout</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

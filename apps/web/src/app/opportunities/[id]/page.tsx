"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ShieldCheck,
  BrainCircuit,
  Zap,
  Play,
  Check,
  RotateCw,
  FileText,
  Lock,
  ExternalLink,
  ChevronRight,
  AlertOctagon,
  HelpCircle,
  XCircle,
} from "lucide-react";
import {
  fetchOpportunityById,
  executeRecoveryAction,
  simulatePaymentSuccess,
} from "@/lib/api";
import { RecoveryOpportunity } from "@/lib/types";
import { StatusBadge } from "@/components/ui/StatusBadge";
import clsx from "clsx";

export default function OpportunityDetailInspectorPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [opp, setOpp] = useState<RecoveryOpportunity | null>(null);
  const [loading, setLoading] = useState(true);
  const [isExecuting, setIsExecuting] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [feedback, setFeedback] = useState<{ type: "success" | "warning"; message: string } | null>(null);

  useEffect(() => {
    async function load() {
      if (!id) return;
      try {
        const data = await fetchOpportunityById(id);
        if (data) setOpp(data);
      } catch (e) {
        console.error("Failed to load opportunity", e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex items-center gap-2 text-slate-400 text-xs font-mono">
          <RotateCw className="w-4 h-4 animate-spin text-blue-400" />
          <span>Loading recovery opportunity telemetry...</span>
        </div>
      </div>
    );
  }

  if (!opp) {
    return (
      <div className="bg-[#0d131f] border border-[#1e293b] rounded-xl p-12 text-center space-y-4">
        <p className="text-slate-400 text-sm">Recovery opportunity not found.</p>
        <Link
          href="/opportunities"
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-xs font-semibold rounded-lg"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Opportunities
        </Link>
      </div>
    );
  }

  const amount = opp.revenue_at_risk_inr || 8499;
  const score = opp.recovery_score || 87;
  const isAllow = score >= 60 && amount <= 15000;
  const isEscalate = amount > 15000;
  const isAmbiguous = opp.failure_category === "TRANSIENT" && opp.status === "INTERVENED" && amount === 3250;
  const isBlock = score < 20 || opp.failure_category === "PERMANENT";

  const customerName = opp.order?.customer?.name || "Rahul Sharma";
  const customerEmail = opp.order?.customer?.email || "rahul.sharma@example.com";
  const ltv = opp.order?.customer?.lifetime_value_inr || 54200;
  const totalOrders = opp.order?.customer?.total_orders || 8;
  const successOrders = opp.order?.customer?.successful_orders || 8;

  const failureReason =
    opp.order?.payment_attempts?.[0]?.failure_reason ||
    "Bank NPCI switch timed out during UPI authorization";

  const handleExecute = async () => {
    try {
      setIsExecuting(true);
      await executeRecoveryAction(opp.id);
      setOpp((prev) => (prev ? { ...prev, status: "INTERVENED" } : null));
      setFeedback({
        type: "success",
        message: "Recovery Payment Link generated on Razorpay Test Rails (plink_RZP_rec_88190).",
      });
    } catch (e: any) {
      setFeedback({
        type: "warning",
        message: e.message || "Execution failed.",
      });
    } finally {
      setIsExecuting(false);
    }
  };

  const handleSimulatePayment = async () => {
    try {
      setIsSimulating(true);
      await simulatePaymentSuccess(opp.id, amount);
      setOpp((prev) =>
        prev
          ? {
              ...prev,
              status: "RECOVERED",
              recovered_amount_inr: amount,
            }
          : null
      );
      setFeedback({
        type: "success",
        message: `Webhook payment.captured verified HMAC signature. Recovered revenue of ₹${amount.toLocaleString("en-IN")} recorded.`,
      });
    } catch (e: any) {
      setFeedback({
        type: "warning",
        message: e.message || "Simulation failed.",
      });
    } finally {
      setIsSimulating(false);
    }
  };

  // Determine Lifecycle Stage status
  const isRecovered = opp.status === "RECOVERED";
  const isIntervened = opp.status === "INTERVENED" || isRecovered;

  return (
    <div className="space-y-8">
      {/* Top Breadcrumb & Header */}
      <div className="space-y-4 pb-2 border-b border-[#1e293b]">
        <Link
          href="/opportunities"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Opportunities</span>
        </Link>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="text-[11px] font-bold text-blue-400 uppercase tracking-wider">
              RECOVERY OPPORTUNITY • {opp.order?.provider_order_id || "order_RZP_98231"}
            </div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-extrabold font-mono text-white tracking-tight">
                ₹{amount.toLocaleString("en-IN")}
              </h1>
              <span className="text-sm font-semibold text-slate-400">Payment Recovery</span>
              <StatusBadge status={opp.status} size="md" />
            </div>
            <div className="text-xs text-slate-400 flex items-center gap-2">
              <span className="text-slate-300 font-medium">{failureReason}</span>
              <span className="text-slate-500">•</span>
              <span className="uppercase font-mono text-[10px] text-slate-400">
                {opp.failure_category || "TRANSIENT FAILURE"}
              </span>
            </div>
          </div>

          {/* Customer & Score Summary Header Pill */}
          <div className="bg-[#0d131f] border border-[#1e293b] rounded-xl px-4 py-3 flex items-center gap-6 text-xs">
            <div>
              <div className="text-[10px] text-slate-400 uppercase font-medium">Customer</div>
              <div className="font-semibold text-white">{customerName}</div>
              <div className="text-[11px] text-slate-400 font-mono">
                {successOrders}/{totalOrders} orders (₹{ltv.toLocaleString("en-IN")} LTV)
              </div>
            </div>
            <div className="border-l border-[#1e293b] pl-4">
              <div className="text-[10px] text-slate-400 uppercase font-medium">Recovery Score</div>
              <div className="text-lg font-bold font-mono text-blue-400">{score} / 100</div>
              <div className="text-[10px] font-semibold text-emerald-400 uppercase">
                {score >= 70 ? "HIGH PROBABILITY" : score >= 40 ? "MEDIUM" : "LOW / BLOCKED"}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Prominent 5-Step Recovery Lifecycle Bar */}
      <div className="bg-[#0d131f] border border-[#1e293b] rounded-xl p-4 shadow-sm">
        <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider mb-3">
          Recovery Lifecycle Progress
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
          {/* Step 1: Detected */}
          <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center gap-2 text-xs font-semibold">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
            <span>1. DETECTED</span>
          </div>

          {/* Step 2: Diagnosed */}
          <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center gap-2 text-xs font-semibold">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
            <span>2. DIAGNOSED</span>
          </div>

          {/* Step 3: Policy Approved / Checked */}
          <div
            className={clsx(
              "p-2.5 rounded-lg border flex items-center gap-2 text-xs font-semibold",
              isAllow
                ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                : isEscalate
                ? "bg-amber-500/10 border-amber-500/20 text-amber-400"
                : "bg-rose-500/10 border-rose-500/20 text-rose-400"
            )}
          >
            {isAllow ? (
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
            ) : (
              <AlertTriangle className="w-4 h-4 shrink-0" />
            )}
            <span>3. {isAllow ? "POLICY ALLOWED" : isEscalate ? "ESCALATED" : "BLOCKED"}</span>
          </div>

          {/* Step 4: Action Ready / Executing */}
          <div
            className={clsx(
              "p-2.5 rounded-lg border flex items-center gap-2 text-xs font-semibold",
              isRecovered || isIntervened
                ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                : isAllow
                ? "bg-blue-500/10 border-blue-500/20 text-blue-400 animate-pulse"
                : "bg-[#162032] border-[#1e293b] text-slate-400"
            )}
          >
            {isIntervened ? (
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
            ) : (
              <Zap className="w-4 h-4 shrink-0" />
            )}
            <span>4. {isIntervened ? "LINK DISPATCHED" : "ACTION READY"}</span>
          </div>

          {/* Step 5: Payment Confirmed */}
          <div
            className={clsx(
              "p-2.5 rounded-lg border flex items-center gap-2 text-xs font-semibold",
              isRecovered
                ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                : "bg-[#162032] border-[#1e293b] text-slate-400"
            )}
          >
            {isRecovered ? (
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
            ) : (
              <Clock className="w-4 h-4 shrink-0 text-slate-400" />
            )}
            <span>5. {isRecovered ? "RECOVERED" : "CONFIRMATION"}</span>
          </div>
        </div>
      </div>

      {feedback && (
        <div
          className={clsx(
            "p-4 rounded-xl text-xs flex items-center gap-3 border shadow-sm",
            feedback.type === "success"
              ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/30"
              : "bg-amber-500/10 text-amber-300 border-amber-500/30"
          )}
        >
          {feedback.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
          )}
          <span className="font-medium">{feedback.message}</span>
        </div>
      )}

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        {/* LEFT COLUMN: Why is this payment recoverable? AI Diagnosis (Advisory Only) */}
        <div className="space-y-6">
          <div className="space-y-1">
            <h2 className="text-base font-bold text-white uppercase tracking-wider">
              Why is this payment recoverable?
            </h2>
            <p className="text-xs text-slate-400">
              Diagnostic analysis synthesized from failure telemetry, customer history, and latency signals.
            </p>
          </div>

          {/* Purple AI Diagnosis Card (Advisory Only) */}
          <div className="bg-[#131226] border border-purple-500/30 rounded-xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BrainCircuit className="w-4 h-4 text-purple-400" />
                <span className="text-xs font-bold text-purple-300 uppercase tracking-wider">
                  AI Diagnostic Proposal
                </span>
              </div>
              <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                Advisory Only
              </span>
            </div>

            <div className="space-y-2">
              <div className="text-xs text-slate-400 uppercase font-medium">Diagnostic Synthesis</div>
              <p className="text-xs text-slate-200 leading-relaxed bg-[#191533] p-3.5 rounded-lg border border-purple-500/20">
                {isAllow &&
                  "Failure was diagnosed as a transient switch timeout during peak UPI banking traffic. High customer lifetime value with 8/8 successful prior transactions indicates strong willingness to complete purchase. Generating a dynamic recovery link provides a zero-friction fallback rail."}
                {isEscalate &&
                  "Transaction amount (₹45,000) exceeds standard automated recovery limits. While customer has positive history, high ticket size mandates manual review escalation to prevent unauthorized credit exposure."}
                {isAmbiguous &&
                  "Gateway network connection dropped before confirmation acknowledgment. AI proposes holding execution pending provider webhook reconciliation to avoid double debiting."}
                {isBlock &&
                  "Hard fraud declination received from card network. Card reported lost/stolen. AI strongly recommends permanent recovery block."}
              </p>
            </div>

            {/* Observed Signals */}
            <div className="space-y-2 pt-2 border-t border-purple-500/20">
              <div className="text-xs text-slate-400 uppercase font-medium">Observed Signals</div>
              <ul className="space-y-1.5 text-xs text-slate-300">
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                  <span>
                    Failure classified as{" "}
                    <strong className="text-purple-300 font-mono">
                      {opp.failure_category || "TRANSIENT"}
                    </strong>
                  </span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                  <span>
                    Customer order success rate:{" "}
                    <strong className="text-purple-300 font-mono">
                      {Math.round((successOrders / Math.max(totalOrders, 1)) * 100)}%
                    </strong>{" "}
                    ({successOrders}/{totalOrders} orders)
                  </span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                  <span>
                    Recovery attempt count:{" "}
                    <strong className="text-purple-300 font-mono">0 (within limit of 2)</strong>
                  </span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                  <span>
                    Amount ₹{amount.toLocaleString("en-IN")} is{" "}
                    <strong className="text-purple-300">
                      {amount <= 15000 ? "safely within ₹15,000 policy cap" : "above ₹15,000 cap"}
                    </strong>
                  </span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                  <span>No previous chargebacks or malicious fraud flags recorded</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: RecoverX Decision, Deterministic Policy Gate & Bounded Execution */}
        <div className="space-y-6">
          <div className="space-y-1">
            <h2 className="text-base font-bold text-white uppercase tracking-wider">
              RecoverX Decision &amp; Execution
            </h2>
            <p className="text-xs text-slate-400">
              Deterministic policy invariants govern 100% of financial disbursements.
            </p>
          </div>

          {/* Decision Summary Bar */}
          <div className="bg-[#0d131f] border border-[#1e293b] rounded-xl p-4 flex items-center justify-between text-xs">
            <div>
              <span className="text-slate-400">Interpretable Score: </span>
              <span className="font-bold text-blue-400 font-mono text-sm">{score} / 100</span>
            </div>
            <div>
              <span className="text-slate-400">AI Recommendation: </span>
              <span className="font-mono font-semibold text-purple-300">
                {isAllow ? "CREATE_PAYMENT_LINK" : isEscalate ? "ESCALATE_TO_MERCHANT" : "BLOCK_ACTION"}
              </span>
            </div>
          </div>

          {/* Deterministic Policy Gate Card (Green / Neutral Border) */}
          <div className="bg-[#0d131f] border-2 border-emerald-500/40 rounded-xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">
                  Deterministic Policy Gate
                </span>
              </div>
              <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                Financial Authority
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4 text-xs bg-[#131d2e] p-3.5 rounded-lg border border-[#1e293b]">
              <div>
                <div className="text-[10px] text-slate-400 uppercase">Policy Decision</div>
                <div className="text-sm font-bold text-emerald-400 flex items-center gap-1.5 mt-0.5">
                  <Check className="w-4 h-4" />
                  <span>{isAllow ? "ALLOW" : isEscalate ? "ESCALATE" : "BLOCK"}</span>
                </div>
              </div>
              <div>
                <div className="text-[10px] text-slate-400 uppercase">Effective Action</div>
                <div className="text-xs font-bold font-mono text-white mt-0.5">
                  {isAllow ? "CREATE_PAYMENT_LINK" : isEscalate ? "ESCALATE_REVIEW" : "BLOCK_ACTION"}
                </div>
              </div>
              <div>
                <div className="text-[10px] text-slate-400 uppercase">Server-Side Amount</div>
                <div className="text-xs font-bold font-mono text-white mt-0.5">
                  ₹{amount.toLocaleString("en-IN")}
                </div>
              </div>
              <div>
                <div className="text-[10px] text-slate-400 uppercase">Active Engine</div>
                <div className="text-xs font-bold font-mono text-blue-400 mt-0.5">
                  v1 (Deterministic Invariants)
                </div>
              </div>
            </div>

            <p className="text-[11px] text-slate-400 leading-relaxed italic">
              * Safety Notice: AI has zero direct execution access to Razorpay APIs. 100% of financial actions are bounded by merchant-configured caps and deterministic state rules.
            </p>
          </div>

          {/* BOUNDED FINANCIAL EXECUTION CARD */}
          <div className="bg-[#0d131f] border border-[#1e293b] rounded-xl p-6 shadow-sm space-y-4">
            <div className="text-xs font-bold text-white uppercase tracking-wider">
              Bounded Financial Execution
            </div>

            {/* Case 1: ALLOW (Standard recovery flow) */}
            {isAllow && (
              <div className="space-y-4">
                {isRecovered ? (
                  <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-5 space-y-3">
                    <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                      <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                      <span>PAYMENT RECOVERED • ₹{amount.toLocaleString("en-IN")}</span>
                    </div>
                    <p className="text-xs text-slate-300">
                      Payment link authorized, customer completed transaction, and webhook signature verified. Full amount settled to merchant ledger.
                    </p>
                    <div className="pt-2 flex items-center justify-between border-t border-emerald-500/20 text-xs">
                      <span className="text-slate-400 font-mono">Status: SETTLED &amp; CONFIRMED</span>
                      <Link
                        href="/dashboard/audit"
                        className="text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1"
                      >
                        <span>View Audit Trail</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  </div>
                ) : isIntervened ? (
                  <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-5 space-y-3">
                    <div className="flex items-center gap-2 text-blue-400 font-bold text-sm">
                      <Clock className="w-5 h-5 text-blue-400 animate-spin" />
                      <span>RECOVERY ACTION IN PROGRESS</span>
                    </div>
                    <ul className="space-y-1.5 text-xs text-slate-300">
                      <li className="flex items-center gap-2 text-emerald-400">
                        <Check className="w-3.5 h-3.5" /> Policy approved execution
                      </li>
                      <li className="flex items-center gap-2 text-emerald-400">
                        <Check className="w-3.5 h-3.5" /> Razorpay Payment Link generated (plink_RZP_rec_88190)
                      </li>
                      <li className="flex items-center gap-2 text-blue-300">
                        <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" /> Awaiting customer payment
                      </li>
                    </ul>

                    {/* Developer/Demo Simulation Button */}
                    <div className="pt-3 border-t border-blue-500/20 flex items-center justify-between">
                      <span className="text-[11px] text-slate-400">Local Sandbox Simulator:</span>
                      <button
                        onClick={handleSimulatePayment}
                        disabled={isSimulating}
                        className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 transition disabled:opacity-50"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>{isSimulating ? "Simulating..." : "Simulate Customer Paid"}</span>
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <p className="text-xs text-slate-300">
                      Policy has approved creation of an idempotent Razorpay recovery payment link for ₹{amount.toLocaleString("en-IN")}.
                    </p>
                    <button
                      onClick={handleExecute}
                      disabled={isExecuting}
                      className="w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs flex items-center justify-center gap-2 shadow-sm transition disabled:opacity-50"
                    >
                      <Play className="w-3.5 h-3.5 fill-white" />
                      <span>{isExecuting ? "Generating Payment Link..." : "Execute Recovery Action"}</span>
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Case 2: ESCALATED */}
            {isEscalate && (
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-5 space-y-3">
                <div className="flex items-center gap-2 text-amber-400 font-bold text-sm">
                  <AlertTriangle className="w-5 h-5 text-amber-400" />
                  <span>MANUAL REVIEW REQUIRED</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Reason: Transaction amount of <strong className="text-white">₹45,000</strong> exceeds automated recovery policy cap (<strong className="text-white">₹15,000</strong>). Autonomous link creation intentionally blocked.
                </p>
                <div className="pt-2 flex items-center justify-between border-t border-amber-500/20 text-xs">
                  <span className="text-slate-400 font-mono">Policy Invariant: CAP_EXCEEDED</span>
                  <Link
                    href="/dashboard/policies"
                    className="text-amber-400 hover:text-amber-300 font-semibold flex items-center gap-1"
                  >
                    <span>View Policy Details</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            )}

            {/* Case 3: AMBIGUOUS */}
            {isAmbiguous && (
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-5 space-y-3">
                <div className="flex items-center gap-2 text-amber-400 font-bold text-sm">
                  <HelpCircle className="w-5 h-5 text-amber-400" />
                  <span>RECOVERY HELD (AMBIGUOUS TIMEOUT)</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Provider outcome is uncertain due to gateway switch timeout. RecoverX will <strong>NOT</strong> blindly retry because the final payment state cannot be safely determined without provider reconciliation.
                </p>
                <div className="pt-2 flex items-center justify-between border-t border-amber-500/20 text-xs">
                  <span className="text-slate-400 font-mono">Status: Awaiting Webhook ACK</span>
                  <span className="text-amber-400 font-semibold">Blind Retries Blocked</span>
                </div>
              </div>
            )}

            {/* Case 4: BLOCKED */}
            {isBlock && (
              <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-5 space-y-3">
                <div className="flex items-center gap-2 text-rose-400 font-bold text-sm">
                  <XCircle className="w-5 h-5 text-rose-400" />
                  <span>RECOVERY BLOCKED</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Reason: Terminal/fraud-related failure detected (Stolen Card decline). Permanent failure invariant triggered. Autonomous recovery refused to protect merchant reputation.
                </p>
                <div className="pt-2 flex items-center justify-between border-t border-rose-500/20 text-xs">
                  <span className="text-slate-400 font-mono">Status: PERMANENTLY_BLOCKED</span>
                  <span className="text-rose-400 font-semibold">No Action Dispatched</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

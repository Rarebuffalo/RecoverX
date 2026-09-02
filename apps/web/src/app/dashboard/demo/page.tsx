"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  PlayCircle,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  XCircle,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  Zap,
  RotateCw,
} from "lucide-react";
import { resetDemoState } from "@/lib/api";
import clsx from "clsx";

const scenarios = [
  {
    id: "opp_demo_01",
    scenarioNumber: 1,
    title: "1. SAFE RECOVERY",
    amount: "₹8,499",
    failureReason: "UPI Timeout / Bank Switch Delay",
    category: "TRANSIENT FAILURE",
    customer: "Rahul Sharma (8/8 orders, ₹54,200 LTV)",
    expectedDecision: "ALLOW",
    expectedAction: "CREATE_PAYMENT_LINK",
    expectedOutcome: "Link created, simulated capture verified, ₹8,499 recovered.",
    decisionColor: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
    badgeIcon: CheckCircle2,
  },
  {
    id: "opp_demo_02",
    scenarioNumber: 2,
    title: "2. POLICY ESCALATION",
    amount: "₹45,000",
    failureReason: "Card Decline / High Ticket Size",
    category: "CUSTOMER ACTION REQUIRED",
    customer: "Priya Patel (12 orders, ₹1.80L LTV)",
    expectedDecision: "ESCALATE",
    expectedAction: "MANUAL_REVIEW_REQUIRED",
    expectedOutcome: "Amount exceeds ₹15,000 policy cap. Autonomous link creation blocked.",
    decisionColor: "text-amber-400 bg-amber-500/10 border-amber-500/30",
    badgeIcon: AlertTriangle,
  },
  {
    id: "opp_demo_03",
    scenarioNumber: 3,
    title: "3. AMBIGUOUS PROVIDER RESULT",
    amount: "₹3,250",
    failureReason: "Gateway Switch Timeout (No ACK)",
    category: "TRANSIENT FAILURE",
    customer: "Vikram Malhotra (3 orders, ₹14,500 LTV)",
    expectedDecision: "HOLD / AMBIGUOUS",
    expectedAction: "AWAIT_RECONCILIATION",
    expectedOutcome: "Gateway state unconfirmed. Blind retries blocked to prevent double debit.",
    decisionColor: "text-amber-400 bg-amber-500/10 border-amber-500/30",
    badgeIcon: HelpCircle,
  },
  {
    id: "opp_demo_04",
    scenarioNumber: 4,
    title: "4. HARD FRAUD DECLINE",
    amount: "₹6,500",
    failureReason: "Stolen Card / High Risk Issuer Block",
    category: "PERMANENT DECLINE",
    customer: "Unknown Shopper (0 prior history)",
    expectedDecision: "BLOCK",
    expectedAction: "PERMANENTLY_BLOCKED",
    expectedOutcome: "Hard fraud signal detected. Policy invariant halts recovery execution.",
    decisionColor: "text-rose-400 bg-rose-500/10 border-rose-500/30",
    badgeIcon: XCircle,
  },
];

export default function DemoCenterPage() {
  const [isResetting, setIsResetting] = useState(false);
  const [resetMessage, setResetMessage] = useState<string | null>(null);

  const handleReset = async () => {
    try {
      setIsResetting(true);
      await resetDemoState();
      setResetMessage("Demo environment reset to clean baseline state successfully.");
      setTimeout(() => setResetMessage(null), 3000);
    } catch (e: any) {
      setResetMessage("Reset failed: " + e.message);
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Demo Center Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#1e293b]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <PlayCircle className="w-6 h-6 text-purple-400" />
              Interactive Recovery Demo Center
            </h1>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20">
              Sandbox Testing
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Test RecoverX autonomous recovery, policy gating, and edge-case behaviors on deterministic rails.
          </p>
        </div>

        <button
          onClick={handleReset}
          disabled={isResetting}
          className="px-4 py-2 rounded-lg bg-[#162032] hover:bg-[#1f2d47] border border-[#1e293b] text-slate-200 hover:text-white text-xs font-semibold flex items-center gap-2 transition disabled:opacity-50"
        >
          <RefreshCw className={clsx("w-3.5 h-3.5 text-blue-400", isResetting && "animate-spin")} />
          <span>{isResetting ? "Resetting State..." : "Reset Demo State"}</span>
        </button>
      </div>

      {resetMessage && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{resetMessage}</span>
        </div>
      )}

      {/* 4 Prominent Scenario Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {scenarios.map((sc) => {
          const Icon = sc.badgeIcon;
          return (
            <div
              key={sc.id}
              className="bg-[#0d131f] border border-[#1e293b] hover:border-blue-500/40 rounded-xl p-6 shadow-sm space-y-4 flex flex-col justify-between transition-all group"
            >
              <div className="space-y-3">
                {/* Top Title & Expected Decision */}
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-base font-bold text-white group-hover:text-blue-400 transition-colors">
                      {sc.title}
                    </h3>
                    <div className="text-xl font-bold font-mono text-white mt-1">
                      {sc.amount}
                    </div>
                  </div>

                  <span
                    className={clsx(
                      "px-2.5 py-1 rounded-lg text-xs font-bold uppercase tracking-wider border flex items-center gap-1.5",
                      sc.decisionColor
                    )}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    <span>{sc.expectedDecision}</span>
                  </span>
                </div>

                {/* Scenario Context */}
                <div className="bg-[#131d2e] rounded-lg p-3 border border-[#1e293b] space-y-1.5 text-xs">
                  <div className="text-slate-300">
                    <span className="text-slate-400">Trigger: </span>
                    <span className="font-medium text-white">{sc.failureReason}</span>
                  </div>
                  <div className="text-slate-300">
                    <span className="text-slate-400">Customer: </span>
                    <span>{sc.customer}</span>
                  </div>
                  <div className="text-slate-300">
                    <span className="text-slate-400">Expected Flow: </span>
                    <span className="text-slate-200">{sc.expectedOutcome}</span>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <Link
                href={`/opportunities/${sc.id}`}
                className="w-full py-2.5 rounded-lg bg-[#162032] hover:bg-blue-600 text-slate-200 hover:text-white border border-[#1e293b] hover:border-blue-500 text-xs font-semibold flex items-center justify-center gap-2 transition-all shadow-sm"
              >
                <span>Run &amp; Inspect Scenario</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </div>
          );
        })}
      </div>

      {/* Safety & Invariant Guarantees */}
      <div className="bg-[#0d131f] border border-[#1e293b] rounded-xl p-6 shadow-sm space-y-3">
        <div className="flex items-center gap-2 text-xs font-bold text-white uppercase tracking-wider">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Deterministic Safety Invariants Verified Across Scenarios</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 text-xs text-slate-400 pt-1">
          <div className="p-3 bg-[#131d2e] rounded-lg border border-[#1e293b]/60">
            <strong className="text-slate-200 block mb-1">1. Zero Blind Retries</strong>
            Ambiguous timeouts are quarantined until provider confirmation.
          </div>
          <div className="p-3 bg-[#131d2e] rounded-lg border border-[#1e293b]/60">
            <strong className="text-slate-200 block mb-1">2. Amount Cap Authority</strong>
            Orders exceeding ₹15,000 cap always escalate to human review.
          </div>
          <div className="p-3 bg-[#131d2e] rounded-lg border border-[#1e293b]/60">
            <strong className="text-slate-200 block mb-1">3. Untrusted AI Boundary</strong>
            AI proposals can never bypass deterministic policy checks.
          </div>
        </div>
      </div>
    </div>
  );
}

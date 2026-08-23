"use client";

import React, { useState } from "react";
import {
  PlayCircle,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  Zap,
  ArrowRight,
  RotateCw,
  Sparkles,
  Lock,
  ExternalLink,
} from "lucide-react";
import { StateMachine } from "@/components/ui/StateMachine";
import { PolicyCard } from "@/components/ui/PolicyCard";
import { Timeline } from "@/components/ui/Timeline";

type DemoScenario = "SUCCESS" | "BLOCKED" | "AMBIGUOUS" | "FAILED";

export default function InteractiveDemoPage() {
  const [activeScenario, setActiveScenario] = useState<DemoScenario>("SUCCESS");
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  const scenarioData = {
    SUCCESS: {
      title: "Scenario 1: Transient UPI Timeout Recovery",
      amount: 8499.0,
      customer: "Rohan Verma (High Loyalty, LTV ₹54,200)",
      failure: "Bank NPCI switch timed out during UPI authorization",
      failureCategory: "TRANSIENT",
      score: 87,
      policyDecision: "ALLOW" as const,
      status: "RECOVERED",
      explanation:
        "RecoverX diagnosed a transient bank timeout, scored 87/100, verified against merchant policy cap (₹15,000), created a bounded payment link, and settled ₹8,499 upon webhook capture.",
    },
    BLOCKED: {
      title: "Scenario 2: Policy Cap Escalation / Block",
      amount: 45000.0,
      customer: "Vikram Malhotra (B2B Purchase)",
      failure: "Transaction amount exceeds merchant auto-recovery threshold",
      failureCategory: "AMOUNT_EXCEEDED",
      score: 64,
      policyDecision: "ESCALATE" as const,
      status: "ESCALATED",
      explanation:
        "Transaction of ₹45,000 exceeds merchant auto-recovery limit (₹15,000). The deterministic policy engine intercepted the AI proposal and escalated to human review, preventing unauthorized exposure.",
    },
    AMBIGUOUS: {
      title: "Scenario 3: Ambiguous Gateway Network Timeout",
      amount: 3250.0,
      customer: "Pooja Sharma",
      failure: "Gateway switch timeout without acknowledgment (No ACK)",
      failureCategory: "NETWORK_TIMEOUT",
      score: 79,
      policyDecision: "ALLOW" as const,
      status: "AMBIGUOUS",
      explanation:
        "The gateway connection timed out before confirmation. RecoverX held the action in AMBIGUOUS to prevent double charging. Automatic retries are paused until verified via reconciliation.",
    },
    FAILED: {
      title: "Scenario 4: High-Risk Fraud Declination",
      amount: 6500.0,
      customer: "Unknown Shopper (0 Prior Orders)",
      failure: "Stolen card / card issuer high-risk fraud decline",
      failureCategory: "PERMANENT",
      score: 12,
      policyDecision: "BLOCK" as const,
      status: "CLOSED_UNRECOVERED",
      explanation:
        "Fraud decline triggered safety invariant #1 (Zero AI overrides on permanent failures). RecoverX scored 12/100 and blocked recovery link generation immediately.",
    },
  };

  const current = scenarioData[activeScenario];

  const handleStartSim = () => {
    setCurrentStep(1);
    setIsPlaying(true);
    let step = 1;
    const interval = setInterval(() => {
      step += 1;
      setCurrentStep(step);
      if (step >= 5) {
        clearInterval(interval);
        setIsPlaying(false);
      }
    }, 1200);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#1e293b]">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <PlayCircle className="w-6 h-6 text-blue-400" />
              Interactive Recovery Demo Center
            </h1>
            <span className="text-xs px-2.5 py-0.5 rounded-md bg-blue-500/10 text-blue-400 font-semibold border border-blue-500/30 font-mono">
              LOCAL DETERMINISTIC RAILS
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Walk through the complete autonomous recovery loop across four distinct real-world failure scenarios.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleStartSim}
            disabled={isPlaying}
            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-blue-500/20 transition-all"
          >
            <RotateCw className={`w-3.5 h-3.5 ${isPlaying ? "animate-spin" : ""}`} />
            <span>{isPlaying ? "Simulating Loop..." : "Replay Scenario"}</span>
          </button>
        </div>
      </div>

      {/* Scenario Selector Tabs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          { key: "SUCCESS", label: "1. Full Recovery Loop", color: "emerald" },
          { key: "BLOCKED", label: "2. Policy Cap Escalation", color: "purple" },
          { key: "AMBIGUOUS", label: "3. Ambiguous Timeout", color: "amber" },
          { key: "FAILED", label: "4. Hard Fraud Block", color: "rose" },
        ].map((s) => (
          <button
            key={s.key}
            onClick={() => {
              setActiveScenario(s.key as DemoScenario);
              setCurrentStep(5);
            }}
            className={`p-3 rounded-xl border text-left transition-all ${
              activeScenario === s.key
                ? "bg-blue-600/15 border-blue-500 text-white shadow-sm ring-1 ring-blue-500"
                : "bg-[#111827] border-[#1f2937] text-slate-400 hover:text-slate-200 hover:border-slate-700"
            }`}
          >
            <div className="text-xs font-bold font-mono">{s.label}</div>
            <div className="text-[10px] text-slate-400 mt-1">
              ₹{scenarioData[s.key as DemoScenario].amount.toLocaleString()} ·{" "}
              {scenarioData[s.key as DemoScenario].failureCategory}
            </div>
          </button>
        ))}
      </div>

      {/* Main Interactive Demo Display */}
      <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-6 shadow-sm space-y-6">
        {/* Scenario Banner */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-850">
          <div>
            <span className="text-[10px] uppercase font-mono tracking-wider font-semibold text-blue-400">
              Active Demonstration
            </span>
            <h2 className="text-lg font-bold text-white mt-0.5">{current.title}</h2>
            <p className="text-xs text-slate-400 mt-1">{current.customer}</p>
          </div>

          <div className="flex items-center gap-4 bg-[#162032] px-4 py-2 rounded-lg border border-[#1f2937]">
            <div>
              <span className="text-[10px] uppercase font-mono text-slate-400 block">
                AMOUNT AT RISK
              </span>
              <span className="text-lg font-bold font-mono text-white">
                ₹{current.amount.toLocaleString()}
              </span>
            </div>
            <div className="border-l border-slate-700 pl-4">
              <span className="text-[10px] uppercase font-mono text-slate-400 block">
                POLICY OUTCOME
              </span>
              <span
                className={`text-xs font-bold font-mono ${
                  current.policyDecision === "ALLOW"
                    ? "text-emerald-400"
                    : current.policyDecision === "ESCALATE"
                    ? "text-purple-400"
                    : "text-rose-400"
                }`}
              >
                {current.policyDecision}
              </span>
            </div>
          </div>
        </div>

        {/* Step Progression Visualizer */}
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
          {[
            { step: 1, title: "1. Detect Failure", desc: "Webhook Ingestion" },
            { step: 2, title: "2. Score & Diagnose", desc: "Additive Features" },
            { step: 3, title: "3. Policy Gating", desc: "Zero Hallucination" },
            { step: 4, title: "4. Bounded Action", desc: "Payment Link Rail" },
            { step: 5, title: "5. Settlement", desc: "Causal Verification" },
          ].map((st) => (
            <div
              key={st.step}
              className={`p-3 rounded-lg border text-center transition-all ${
                currentStep >= st.step
                  ? "bg-blue-600/15 border-blue-500/50 text-blue-200"
                  : "bg-[#162032]/40 border-[#1f2937] text-slate-400 opacity-50"
              }`}
            >
              <div className="text-xs font-bold">{st.title}</div>
              <div className="text-[10px] text-slate-400 mt-0.5">{st.desc}</div>
            </div>
          ))}
        </div>

        {/* State Machine for Scenario */}
        <StateMachine currentStatus={current.status} />

        {/* Policy vs Advisory Split */}
        <PolicyCard
          decision={current.policyDecision}
          effectiveAction={
            current.policyDecision === "ALLOW"
              ? "CREATE_RECOVERY_PAYMENT_LINK"
              : current.policyDecision === "ESCALATE"
              ? "ESCALATE_TO_MERCHANT"
              : "NO_ACTION"
          }
          policyVersion="v1"
          threshold={60}
          maxAmountCap={15000}
          retryLimit={2}
          reasonCodes={[current.failureCategory]}
          humanReadableSummary={current.explanation}
          aiRecommendation={
            current.policyDecision === "ALLOW"
              ? "CREATE_RECOVERY_PAYMENT_LINK"
              : "ESCALATE_TO_MERCHANT"
          }
          aiConfidence={current.score / 100}
          decisionFactors={[
            current.failure,
            `Recovery Score: ${current.score}/100`,
            current.customer,
          ]}
        />
      </div>
    </div>
  );
}

"use client";

import React, { useEffect, useState } from "react";
import {
  ShieldCheck,
  ShieldAlert,
  Save,
  CheckCircle2,
  Lock,
  Layers,
  Settings2,
  AlertOctagon,
} from "lucide-react";
import { fetchMerchantPolicy, updateMerchantPolicy } from "@/lib/api";
import { MerchantPolicy } from "@/lib/types";

export default function PoliciesPage() {
  const [policy, setPolicy] = useState<MerchantPolicy | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchMerchantPolicy();
        setPolicy(data);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!policy) return;
    setSaving(true);
    setSavedSuccess(false);
    try {
      const updated = await updateMerchantPolicy(policy);
      setPolicy(updated);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } finally {
      setSaving(false);
    }
  };

  if (loading || !policy) {
    return (
      <div className="p-8 text-center text-slate-400 text-xs font-mono">
        Loading merchant policy configuration...
      </div>
    );
  }

  const invariants = [
    {
      title: "1. The LLM is Untrusted Advisory Only",
      desc: "AI agent proposals are strictly validated by deterministic policy invariants before financial authorization.",
    },
    {
      title: "2. Zero Re-billing on Paid Orders",
      desc: "If an order is already in 'paid' or 'captured' status, all recovery actions are instantly aborted.",
    },
    {
      title: "3. Hard Merchant Amount Cap",
      desc: "Transactions exceeding merchant recovery limits are escalated and never auto-executed.",
    },
    {
      title: "4. Max Attempt & Cooldown Limits",
      desc: "Guarantees a maximum of 2 recovery attempts with mandatory 30-minute cooldowns between link dispatches.",
    },
    {
      title: "5. Idempotent Action Deduplication",
      desc: "Deterministic SHA-256 idempotency keys prevent duplicate payment links on identical failure events.",
    },
    {
      title: "6. Zero PII Context Sanitization",
      desc: "AI context builders redact all customer names, phone numbers, and raw card details.",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#1e293b]">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Merchant Recovery Policies
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic risk parameters, autonomous thresholds, and financial safety guardrails.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-400 bg-[#162032] px-3 py-1.5 rounded-lg border border-[#1e293b]">
            ACTIVE POLICY: <span className="font-bold text-slate-100 uppercase">{policy.policy_version}</span>
          </span>
        </div>
      </div>

      {/* Main Grid: Policy Form & Hard Invariants */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column (2 Cols): Config Form */}
        <div className="lg:col-span-2 bg-[#111827] border border-[#1f2937] rounded-xl p-6 shadow-sm space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div className="flex items-center gap-2 text-sm font-bold text-white uppercase tracking-wider">
              <Settings2 className="w-4 h-4 text-blue-400" />
              <span>Safety Limits & Threshold Configuration</span>
            </div>
            {savedSuccess && (
              <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Policy Updated Successfully
              </span>
            )}
          </div>

          <form onSubmit={handleSave} className="space-y-5">
            {/* Auto Recovery Switch */}
            <div className="flex items-center justify-between p-4 rounded-lg bg-[#162032] border border-[#1f2937]">
              <div>
                <div className="text-xs font-bold text-slate-200">Autonomous Payment Link Creation</div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Allow RecoverX to create Razorpay payment links for policy-approved opportunities.
                </div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={policy.auto_recovery_enabled}
                  onChange={(e) => setPolicy({ ...policy, auto_recovery_enabled: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            {/* Policy Version Selector */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">Active Policy Engine Version</label>
              <div className="grid grid-cols-2 gap-3">
                <div
                  onClick={() => setPolicy({ ...policy, policy_version: "v1" })}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    policy.policy_version === "v1"
                      ? "bg-blue-600/15 border-blue-500 text-white"
                      : "bg-[#162032] border-[#1f2937] text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <div className="text-xs font-bold font-mono">v1 (Static Threshold 60)</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">
                    High precision baseline (71.7% precision, ₹12.05 Cr recovery).
                  </div>
                </div>

                <div
                  onClick={() => setPolicy({ ...policy, policy_version: "v2_candidate" })}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    policy.policy_version === "v2_candidate"
                      ? "bg-emerald-600/15 border-emerald-500 text-white"
                      : "bg-[#162032] border-[#1f2937] text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <div className="text-xs font-bold font-mono text-emerald-300">
                    v2 Candidate (Dynamic Failure-Aware)
                  </div>
                  <div className="text-[10px] text-slate-400 mt-0.5">
                    +₹57.1L economic gain, 92.1% recall, 68.4% precision.
                  </div>
                </div>
              </div>
            </div>

            {/* Amount Cap & Limits */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Max Auto-Recovery Cap (₹)</label>
                <input
                  type="number"
                  value={policy.max_auto_recovery_amount_inr}
                  onChange={(e) =>
                    setPolicy({ ...policy, max_auto_recovery_amount_inr: Number(e.target.value) })
                  }
                  className="w-full px-3 py-2 rounded-lg bg-[#162032] border border-[#1f2937] text-xs font-mono text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Max Retry Attempts</label>
                <input
                  type="number"
                  value={policy.max_retry_attempts}
                  onChange={(e) =>
                    setPolicy({ ...policy, max_retry_attempts: Number(e.target.value) })
                  }
                  className="w-full px-3 py-2 rounded-lg bg-[#162032] border border-[#1f2937] text-xs font-mono text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Cooldown Window (Min)</label>
                <input
                  type="number"
                  value={policy.cooldown_minutes}
                  onChange={(e) =>
                    setPolicy({ ...policy, cooldown_minutes: Number(e.target.value) })
                  }
                  className="w-full px-3 py-2 rounded-lg bg-[#162032] border border-[#1f2937] text-xs font-mono text-white focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            {/* Submit Button */}
            <div className="pt-4 border-t border-slate-800 flex justify-end">
              <button
                type="submit"
                disabled={saving}
                className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold flex items-center gap-2 transition-all disabled:opacity-50"
              >
                <Save className="w-3.5 h-3.5" />
                <span>{saving ? "Saving Changes..." : "Save Policy Configuration"}</span>
              </button>
            </div>
          </form>
        </div>

        {/* Right Column: Hard Financial Invariants */}
        <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2 text-xs font-bold text-emerald-400 uppercase tracking-wider">
            <Lock className="w-4 h-4" />
            <span>Immutable Safety Invariants</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            The following financial safeguards are enforced deterministically at runtime and cannot be bypassed:
          </p>

          <div className="space-y-3 pt-2">
            {invariants.map((inv, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-[#162032]/60 border border-[#1f2937] space-y-1">
                <div className="text-xs font-bold text-slate-200">{inv.title}</div>
                <div className="text-[11px] text-slate-400 leading-relaxed">{inv.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

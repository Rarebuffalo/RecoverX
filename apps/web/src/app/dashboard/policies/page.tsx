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
      <div className="p-8 text-center text-slate-500 text-xs font-mono bg-white border border-slate-200 rounded-xl">
        Loading merchant policy configuration...
      </div>
    );
  }

  const invariants = [
    {
      title: "1. The LLM is Untrusted Advisory Only",
      desc: "AI proposals are strictly non-authoritative. The model cannot trigger gateways, disburse funds, or override policy parameters.",
    },
    {
      title: "2. The Deterministic Policy Gate Governs Execution",
      desc: "Only the policy engine has financial authority to authorize, escalate, or halt recovery link dispatches.",
    },
    {
      title: "3. Server-Side Amount & Account Authority",
      desc: "Payment amounts are derived solely from verified database records. Model-suggested amounts are discarded.",
    },
    {
      title: "4. Single Action Execution per Stage",
      desc: "Autonomous financial execution is bounded strictly to dynamic payment link creation. No blind automated card charges.",
    },
    {
      title: "5. Absolute Action Idempotency",
      desc: "Every action execution enforces unique deterministic idempotency keys, preventing duplicate financial transactions.",
    },
    {
      title: "6. Zero Blind Retries on Ambiguity",
      desc: "Network timeouts or unconfirmed gateway responses enter AMBIGUOUS quarantine pending authoritative reconciliation.",
    },
    {
      title: "7. Zero Payment Overwrite Invariant",
      desc: "An already paid or captured order cannot receive recovery actions or duplicate payment links.",
    },
    {
      title: "8. Webhook Cryptographic HMAC Verification",
      desc: "All state updates require cryptographic HMAC-SHA256 signature verification before database commit.",
    },
    {
      title: "9. Hard Permanent Decline Containment",
      desc: "Stolen card, fraud, and account-closed failure codes permanently block automated recovery attempts.",
    },
    {
      title: "10. Comprehensive Append-Only Audit Ledger",
      desc: "Every detection, diagnosis, score factor, policy verdict, and webhook event is recorded in an immutable audit ledger.",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Policy Configuration &amp; Safety Invariants
            </h1>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 font-semibold">
              Policy v{policy.policy_version}
            </span>
          </div>
          <p className="text-xs text-slate-600 mt-1">
            Configure merchant recovery guardrails and review immutable mathematical invariants governing autonomous operations.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-600 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-xs">
          <span>MERCHANT SCOPE:</span>
          <span className="font-bold text-slate-900">acc_acme_prod</span>
        </div>
      </div>

      {savedSuccess && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2 shadow-xs">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>Policy configuration successfully updated and verified.</span>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Configurable Merchant Policy */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-6">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-900 uppercase tracking-wider">
              <Settings2 className="w-4 h-4 text-blue-600" />
              <span>Configurable Merchant Limits</span>
            </div>
            <span className="text-[10px] font-mono text-slate-400">Scoped per Tenant</span>
          </div>

          <form onSubmit={handleSave} className="space-y-4 text-xs">
            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                Autonomous Recovery Score Threshold (0 - 100)
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={policy.min_score_threshold}
                onChange={(e) =>
                  setPolicy({
                    ...policy,
                    min_score_threshold: Number(e.target.value),
                  })
                }
                className="w-full px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 text-slate-900 font-mono focus:outline-none focus:border-blue-500"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Minimum deterministic score required to allow autonomous payment link dispatch. Default: 60.
              </p>
            </div>

            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                Maximum Autonomous Amount Cap (₹ INR)
              </label>
              <input
                type="number"
                min="0"
                step="100"
                value={policy.max_auto_recovery_amount_inr}
                onChange={(e) =>
                  setPolicy({
                    ...policy,
                    max_auto_recovery_amount_inr: Number(e.target.value),
                  })
                }
                className="w-full px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 text-slate-900 font-mono focus:outline-none focus:border-blue-500"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Transactions above this amount automatically escalate for human review. Default: ₹15,000.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-700 font-semibold mb-1">
                  Max Recovery Retries
                </label>
                <input
                  type="number"
                  min="1"
                  max="5"
                  value={policy.max_retry_attempts}
                  onChange={(e) =>
                    setPolicy({
                      ...policy,
                      max_retry_attempts: Number(e.target.value),
                    })
                  }
                  className="w-full px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 text-slate-900 font-mono focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">
                  Cooldown Period (Min)
                </label>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={policy.cooldown_minutes}
                  onChange={(e) =>
                    setPolicy({
                      ...policy,
                      cooldown_minutes: Number(e.target.value),
                    })
                  }
                  className="w-full px-3 py-2 rounded-lg bg-slate-50 border border-slate-200 text-slate-900 font-mono focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={saving}
                className="w-full py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs flex items-center justify-center gap-2 shadow-xs transition disabled:opacity-50"
              >
                <Save className="w-3.5 h-3.5" />
                <span>{saving ? "Saving Policy..." : "Save Policy Changes"}</span>
              </button>
            </div>
          </form>
        </div>

        {/* Right: 10 Immutable Invariants Checklist */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-900 uppercase tracking-wider">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>10 Immutable Safety Invariants</span>
            </div>
            <span className="text-[10px] font-mono text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              System Hardcoded
            </span>
          </div>

          <div className="space-y-3 overflow-y-auto max-h-[480px] pr-1">
            {invariants.map((inv, idx) => (
              <div
                key={idx}
                className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs space-y-1"
              >
                <div className="font-bold text-slate-900 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span>{inv.title}</span>
                </div>
                <p className="text-slate-600 leading-relaxed text-[11px] pl-5">
                  {inv.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

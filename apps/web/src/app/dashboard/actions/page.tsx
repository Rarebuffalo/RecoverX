"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { RotateCw, ShieldCheck, ExternalLink, ArrowUpRight, Search } from "lucide-react";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { fetchActions } from "@/lib/api";
import { RecoveryAction } from "@/lib/types";

export default function RecoveryActionsPage() {
  const [actions, setActions] = useState<RecoveryAction[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchActions();
        setActions(data);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filtered = actions.filter((act) => {
    return (
      act.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      act.opportunity_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      act.idempotency_key.toLowerCase().includes(searchQuery.toLowerCase()) ||
      act.action_type.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#1e293b]">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Recovery Actions Ledger
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Immutable log of dispatched payment links, retries, and gateway provider actions with deterministic idempotency.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-400 bg-[#162032] px-3 py-1.5 rounded-lg border border-[#1e293b]">
          <span>TOTAL ACTIONS:</span>
          <span className="font-bold text-slate-100">{actions.length} EXECUTIONS</span>
        </div>
      </div>

      {/* Search Bar */}
      <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-4 flex items-center justify-between shadow-sm">
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search Action ID, Opportunity ID, Idempotency key..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-[#162032] border border-[#1f2937] text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      {/* Actions Table */}
      <div className="bg-[#111827] border border-[#1f2937] rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#162032]/60 text-slate-400 uppercase font-mono text-[10px] border-b border-[#1f2937]">
              <tr>
                <th className="px-5 py-3 font-semibold">Action ID / Type</th>
                <th className="px-4 py-3 font-semibold">Opportunity</th>
                <th className="px-4 py-3 font-semibold">Amount</th>
                <th className="px-4 py-3 font-semibold">Idempotency Key</th>
                <th className="px-4 py-3 font-semibold">Policy Gate</th>
                <th className="px-4 py-3 font-semibold">Execution Status</th>
                <th className="px-4 py-3 font-semibold">Provider Ref</th>
                <th className="px-4 py-3 font-semibold text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1f2937] text-slate-300">
              {filtered.map((act) => (
                <tr key={act.id} className="hover:bg-[#162032]/40 transition-colors">
                  <td className="px-5 py-3.5">
                    <div className="font-mono font-semibold text-slate-100 text-xs">{act.id}</div>
                    <div className="text-[11px] text-blue-400 font-mono">
                      {act.action_type.replace(/_/g, " ")}
                    </div>
                  </td>
                  <td className="px-4 py-3.5 font-mono text-slate-400 text-xs">
                    <Link
                      href={`/dashboard/opportunities/${act.opportunity_id}`}
                      className="hover:text-blue-400 underline decoration-slate-600 underline-offset-2"
                    >
                      {act.opportunity_id}
                    </Link>
                  </td>
                  <td className="px-4 py-3.5 font-mono font-semibold text-slate-200">
                    {act.order_amount_inr ? `₹${act.order_amount_inr.toLocaleString()}` : "—"}
                  </td>
                  <td className="px-4 py-3.5 font-mono text-[11px] text-slate-400 truncate max-w-xs">
                    {act.idempotency_key}
                  </td>
                  <td className="px-4 py-3.5">
                    {act.policy_approved ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                        <ShieldCheck className="w-3 h-3" /> APPROVED
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-rose-500/10 text-rose-400 border border-rose-500/30">
                        BLOCKED
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3.5">
                    <StatusBadge status={act.execution_status} />
                  </td>
                  <td className="px-4 py-3.5 font-mono text-[11px]">
                    {act.payment_link_url ? (
                      <a
                        href={act.payment_link_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-blue-400 hover:underline inline-flex items-center gap-1"
                      >
                        <span>{act.provider_action_id || "plink_RZP"}</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    ) : (
                      <span className="text-slate-400">{act.provider_action_id || "N/A"}</span>
                    )}
                  </td>
                  <td className="px-4 py-3.5 text-right">
                    <Link
                      href={`/dashboard/opportunities/${act.opportunity_id}`}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-[#1f2937] hover:bg-blue-600 text-slate-200 hover:text-white font-medium transition-colors text-[11px]"
                    >
                      <span>View Opp</span>
                      <ArrowUpRight className="w-3 h-3" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

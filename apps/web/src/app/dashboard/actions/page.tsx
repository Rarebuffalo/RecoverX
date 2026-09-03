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
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            Recovery Actions Ledger
          </h1>
          <p className="text-xs text-slate-600 mt-1">
            Immutable log of dispatched payment links, retries, and gateway provider actions with deterministic idempotency.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-600 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-xs">
          <span>TOTAL ACTIONS:</span>
          <span className="font-bold text-slate-900">{actions.length} EXECUTIONS</span>
        </div>
      </div>

      {/* Search Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 flex items-center justify-between shadow-xs">
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search Action ID, Opportunity ID, Idempotency key..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition"
          />
        </div>
      </div>

      {/* Actions Table */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider text-[10px] border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Action ID &amp; Type</th>
                <th className="py-3 px-4">Opportunity Reference</th>
                <th className="py-3 px-4">Provider / Reference ID</th>
                <th className="py-3 px-4 text-center">Status</th>
                <th className="py-3 px-4">Idempotency Key</th>
                <th className="py-3 px-4 text-right">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">
                    Loading recovery actions...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">
                    No recovery actions match query.
                  </td>
                </tr>
              ) : (
                filtered.map((act) => (
                  <tr key={act.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3.5 px-4">
                      <div className="font-mono font-bold text-slate-900">{act.id}</div>
                      <div className="text-[10px] text-blue-600 uppercase font-semibold mt-0.5">
                        {act.action_type}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 font-mono">
                      <Link
                        href={`/opportunities/${act.opportunity_id}`}
                        className="text-blue-600 hover:text-blue-800 flex items-center gap-1 font-semibold"
                      >
                        <span>{act.opportunity_id}</span>
                        <ArrowUpRight className="w-3 h-3" />
                      </Link>
                    </td>
                    <td className="py-3.5 px-4">
                      {act.payment_link_url ? (
                        <a
                          href={act.payment_link_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-slate-800 hover:text-blue-600 flex items-center gap-1 font-mono text-[11px] truncate max-w-xs"
                        >
                          <span className="truncate">{act.provider_action_id || act.payment_link_url}</span>
                          <ExternalLink className="w-3 h-3 shrink-0" />
                        </a>
                      ) : (
                        <span className="font-mono text-slate-400">
                          {act.provider_action_id || "—"}
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <StatusBadge status={act.execution_status} size="sm" />
                    </td>
                    <td className="py-3.5 px-4 font-mono text-[11px] text-slate-500 max-w-xs truncate">
                      {act.idempotency_key}
                    </td>
                    <td className="py-3.5 px-4 text-right text-slate-500 font-mono text-[11px]">
                      {act.created_at ? new Date(act.created_at).toLocaleTimeString() : "Just now"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

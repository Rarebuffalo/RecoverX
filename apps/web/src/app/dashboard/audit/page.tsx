"use client";

import React, { useEffect, useState } from "react";
import { FileText, ShieldCheck, Search, Database, Clock } from "lucide-react";
import { fetchAuditEvents } from "@/lib/api";
import { AuditEvent } from "@/lib/types";

export default function AuditLogPage() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchAuditEvents();
        setEvents(data);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filtered = events.filter((e) => {
    return (
      e.event_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.actor_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.resource_id.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            Append-Only Audit Ledger
          </h1>
          <p className="text-xs text-slate-600 mt-1">
            Cryptographically sealed, immutable record of every telemetry event, policy check, and financial settlement.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-600 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-xs">
          <Database className="w-3.5 h-3.5 text-blue-600" />
          <span>AUDIT LOGS:</span>
          <span className="font-bold text-slate-900">{events.length} EVENTS</span>
        </div>
      </div>

      {/* Search Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 flex items-center justify-between shadow-xs">
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search Event type, Actor, Resource ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition"
          />
        </div>
      </div>

      {/* Audit Table */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-semibold uppercase tracking-wider text-[10px] border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Event ID</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Actor</th>
                <th className="py-3 px-4">Event Type</th>
                <th className="py-3 px-4">Resource Target</th>
                <th className="py-3 px-4 text-right">Event Metadata</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">
                    Loading audit events...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400">
                    No audit records match query.
                  </td>
                </tr>
              ) : (
                filtered.map((evt) => (
                  <tr key={evt.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-slate-900">
                      {evt.id}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-[11px] text-slate-500">
                      {evt.created_at ? new Date(evt.created_at).toLocaleTimeString() : "Just now"}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded font-mono text-[10px] font-bold uppercase bg-slate-100 text-slate-700 border border-slate-200">
                        {evt.actor_type}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-slate-900 font-mono text-[11px]">
                        {evt.event_type}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-[11px] text-blue-600 font-semibold">
                      {evt.resource_id}
                    </td>
                    <td className="py-3.5 px-4 text-right font-mono text-[10px] text-slate-500 max-w-xs truncate">
                      {JSON.stringify(evt.details || {})}
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

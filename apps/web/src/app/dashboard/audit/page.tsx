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
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#1e293b]">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Append-Only Audit Ledger
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Cryptographically sealed, immutable record of every telemetry event, policy check, and financial settlement.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-400 bg-[#162032] px-3 py-1.5 rounded-lg border border-[#1e293b]">
          <Database className="w-3.5 h-3.5 text-blue-400" />
          <span>AUDIT LOGS:</span>
          <span className="font-bold text-slate-100">{events.length} EVENTS</span>
        </div>
      </div>

      {/* Search Bar */}
      <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-4 flex items-center justify-between shadow-sm">
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search Event type, Actor, Resource ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-[#162032] border border-[#1f2937] text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      {/* Audit Events Table */}
      <div className="bg-[#111827] border border-[#1f2937] rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#162032]/60 text-slate-400 uppercase font-mono text-[10px] border-b border-[#1f2937]">
              <tr>
                <th className="px-5 py-3 font-semibold">Timestamp</th>
                <th className="px-4 py-3 font-semibold">Event Type</th>
                <th className="px-4 py-3 font-semibold">Actor Type / ID</th>
                <th className="px-4 py-3 font-semibold">Resource</th>
                <th className="px-4 py-3 font-semibold">Details & Metadata</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1f2937] text-slate-300">
              {filtered.map((evt) => (
                <tr key={evt.id} className="hover:bg-[#162032]/40 transition-colors">
                  <td className="px-5 py-3.5 font-mono text-slate-400 text-[11px] whitespace-nowrap">
                    {evt.created_at ? new Date(evt.created_at).toLocaleTimeString() : "14:31:02"}
                  </td>
                  <td className="px-4 py-3.5">
                    <span className="font-mono font-semibold text-blue-400 text-[11px]">
                      {evt.event_type}
                    </span>
                  </td>
                  <td className="px-4 py-3.5 font-mono">
                    <div className="text-slate-200 font-semibold text-xs">{evt.actor_type}</div>
                    <div className="text-[10px] text-slate-400">{evt.actor_id || "system"}</div>
                  </td>
                  <td className="px-4 py-3.5 font-mono text-slate-300">
                    <div className="text-xs">{evt.resource_type}</div>
                    <div className="text-[10px] text-slate-400">{evt.resource_id}</div>
                  </td>
                  <td className="px-4 py-3.5 font-mono text-[11px] text-slate-400 max-w-md">
                    <pre className="bg-[#162032] p-2 rounded border border-slate-800 text-[10px] overflow-x-auto text-slate-300">
                      {JSON.stringify(evt.details || {}, null, 1)}
                    </pre>
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

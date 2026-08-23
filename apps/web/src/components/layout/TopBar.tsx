"use client";

import { Bell, Search, Store, Shield, CheckCircle2 } from "lucide-react";

export function TopBar() {
  return (
    <header className="h-16 bg-[#0d131f]/80 backdrop-blur border-b border-[#1e293b] px-6 flex items-center justify-between sticky top-0 z-30">
      {/* Merchant Switcher & Environment */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2.5 px-3 py-1.5 rounded-lg bg-[#162032] border border-[#1e293b] text-sm text-slate-200">
          <Store className="w-4 h-4 text-blue-400" />
          <span className="font-semibold text-slate-100">Acme Digital Commerce</span>
          <span className="text-xs text-slate-400 border-l border-slate-700 pl-2">acc_acme_prod</span>
        </div>

        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <span>RAZORPAY TEST MODE</span>
        </div>
      </div>

      {/* Global Actions */}
      <div className="flex items-center gap-3">
        {/* Search */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search order, payment, customer..."
            className="w-64 pl-9 pr-4 py-1.5 rounded-lg bg-[#131d2e] border border-[#1e293b] text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>

        {/* Real-time Health / Invariant Status */}
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#162032] border border-[#1e293b] text-xs text-slate-300">
          <Shield className="w-3.5 h-3.5 text-blue-400" />
          <span className="text-slate-400">Guards:</span>
          <span className="font-medium text-emerald-400">10 Active Invariants</span>
        </div>

        {/* Notifications */}
        <button
          aria-label="Notifications"
          className="w-9 h-9 rounded-lg bg-[#131d2e] border border-[#1e293b] flex items-center justify-center text-slate-400 hover:text-slate-200 transition-colors relative"
        >
          <Bell className="w-4 h-4" />
          <span className="w-2 h-2 rounded-full bg-blue-500 absolute top-2 right-2 ring-2 ring-[#0d131f]" />
        </button>

        {/* User Avatar */}
        <div className="flex items-center gap-2 pl-2 border-l border-[#1e293b]">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-xs font-bold text-white shadow-sm">
            RS
          </div>
          <div className="hidden md:block text-left">
            <div className="text-xs font-semibold text-slate-200">Revenue Ops</div>
            <div className="text-[10px] text-slate-400">admin@acme.com</div>
          </div>
        </div>
      </div>
    </header>
  );
}

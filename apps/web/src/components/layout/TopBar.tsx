"use client";

import { Store, Shield, CheckCircle2 } from "lucide-react";

export function TopBar() {
  return (
    <header className="h-16 bg-white/95 backdrop-blur border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-20 shadow-xs">
      {/* Merchant Switcher & Environment */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2.5 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-sm text-slate-800">
          <Store className="w-4 h-4 text-blue-600" />
          <span className="font-semibold text-slate-900">Acme Digital Commerce</span>
          <span className="text-xs text-slate-400 border-l border-slate-200 pl-2 font-mono">
            acc_acme_prod
          </span>
        </div>

        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>RAZORPAY TEST MODE</span>
        </div>
      </div>

      {/* Right: Verified Guardrail Status & Role */}
      <div className="flex items-center gap-4">
        {/* Real-time Guardrail Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
          <Shield className="w-3.5 h-3.5 text-blue-600" />
          <span className="text-slate-500">Guardrails:</span>
          <span className="font-semibold text-emerald-700">10 Active Invariants</span>
        </div>

        {/* User Context */}
        <div className="flex items-center gap-2 pl-3 border-l border-slate-200">
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold text-white shadow-xs">
            RS
          </div>
          <div className="hidden md:block text-left">
            <div className="text-xs font-semibold text-slate-900">Revenue Ops</div>
            <div className="text-[10px] text-slate-500">admin@acme.com</div>
          </div>
        </div>
      </div>
    </header>
  );
}

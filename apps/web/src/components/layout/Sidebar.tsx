"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Zap,
  RotateCw,
  BarChart3,
  ShieldCheck,
  FileText,
  PlayCircle,
  TrendingUp,
  RefreshCw,
  CheckCircle2,
} from "lucide-react";
import clsx from "clsx";
import { resetDemoState } from "@/lib/api";

const primaryNav = [
  { label: "Command Center", href: "/dashboard", icon: LayoutDashboard },
  { label: "Opportunities", href: "/opportunities", icon: Zap },
  { label: "Actions", href: "/dashboard/actions", icon: RotateCw },
  { label: "Analytics", href: "/dashboard/analytics", icon: BarChart3 },
];

const governanceNav = [
  { label: "Policies", href: "/dashboard/policies", icon: ShieldCheck },
  { label: "Audit Log", href: "/dashboard/audit", icon: FileText },
];

const demoNav = [
  { label: "Demo Center", href: "/dashboard/demo", icon: PlayCircle },
];

export function Sidebar() {
  const pathname = usePathname();
  const [isResetting, setIsResetting] = useState(false);
  const [resetSuccess, setResetSuccess] = useState(false);

  const handleReset = async () => {
    try {
      setIsResetting(true);
      await resetDemoState();
      setResetSuccess(true);
      setTimeout(() => {
        setResetSuccess(false);
        window.location.reload();
      }, 700);
    } catch (err) {
      console.error("Reset failed", err);
      setIsResetting(false);
    }
  };

  const isRouteActive = (href: string) => {
    if (href === "/dashboard") {
      return pathname === "/dashboard";
    }
    if (href === "/opportunities") {
      return pathname === "/opportunities" || pathname?.startsWith("/opportunities/") || pathname === "/dashboard/opportunities" || pathname?.startsWith("/dashboard/opportunities/");
    }
    return pathname?.startsWith(href);
  };

  return (
    <aside className="w-64 bg-[#0d131f] border-r border-[#1e293b] flex flex-col justify-between h-screen sticky top-0 shrink-0 select-none z-30">
      <div className="overflow-y-auto">
        {/* Brand Header */}
        <div className="h-16 flex items-center px-5 border-b border-[#1e293b] gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/30">
            <TrendingUp className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-base tracking-tight text-white">RecoverX</span>
              <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                v2.0
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium leading-none mt-0.5">
              Revenue Recovery Layer
            </p>
          </div>
        </div>

        {/* Primary Navigation Menu */}
        <div className="px-3 py-4 space-y-1">
          <div className="px-3 pb-2 text-[10px] font-semibold tracking-wider text-slate-400 uppercase">
            Revenue Operations
          </div>
          {primaryNav.map((item) => {
            const Icon = item.icon;
            const active = isRouteActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all",
                  active
                    ? "bg-blue-600/15 text-blue-400 font-semibold border border-blue-500/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-[#162032]"
                )}
              >
                <Icon className={clsx("w-4 h-4", active ? "text-blue-400" : "text-slate-400")} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>

        {/* Divider */}
        <div className="mx-4 my-2 border-t border-[#1e293b]" />

        {/* Governance & Compliance */}
        <div className="px-3 py-2 space-y-1">
          <div className="px-3 pb-2 text-[10px] font-semibold tracking-wider text-slate-400 uppercase">
            Control &amp; Governance
          </div>
          {governanceNav.map((item) => {
            const Icon = item.icon;
            const active = isRouteActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all",
                  active
                    ? "bg-blue-600/15 text-blue-400 font-semibold border border-blue-500/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-[#162032]"
                )}
              >
                <Icon className={clsx("w-4 h-4", active ? "text-blue-400" : "text-slate-400")} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>

        {/* Divider */}
        <div className="mx-4 my-2 border-t border-[#1e293b]" />

        {/* Demo Center */}
        <div className="px-3 py-2 space-y-1">
          <div className="px-3 pb-2 text-[10px] font-semibold tracking-wider text-slate-400 uppercase">
            Simulation &amp; Testing
          </div>
          {demoNav.map((item) => {
            const Icon = item.icon;
            const active = isRouteActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all",
                  active
                    ? "bg-purple-600/15 text-purple-400 font-semibold border border-purple-500/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-[#162032]"
                )}
              >
                <Icon className={clsx("w-4 h-4", active ? "text-purple-400" : "text-slate-400")} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Bottom Area: Local Demo Status & Reset Button */}
      <div className="p-3 border-t border-[#1e293b] bg-[#090d16]/50 space-y-2">
        <div className="flex items-center justify-between px-2 text-xs">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="font-semibold text-slate-300">LOCAL DEMO</span>
          </div>
          <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            TEST RAILS
          </span>
        </div>

        <button
          onClick={handleReset}
          disabled={isResetting}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-[#162032] hover:bg-[#1f2d47] border border-[#1e293b] text-slate-300 hover:text-white text-xs font-semibold transition-all disabled:opacity-50"
        >
          {resetSuccess ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400">Reset Complete</span>
            </>
          ) : (
            <>
              <RefreshCw className={clsx("w-3.5 h-3.5 text-slate-400", isResetting && "animate-spin text-blue-400")} />
              <span>{isResetting ? "Resetting State..." : "Reset Demo"}</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Zap,
  RotateCw,
  BarChart3,
  ShieldCheck,
  FileText,
  Settings,
  PlayCircle,
  TrendingUp,
} from "lucide-react";
import clsx from "clsx";

const navItems = [
  { label: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { label: "Opportunities", href: "/dashboard/opportunities", icon: Zap },
  { label: "Recovery Actions", href: "/dashboard/actions", icon: RotateCw },
  { label: "Analytics & Frontier", href: "/dashboard/analytics", icon: BarChart3 },
  { label: "Policies", href: "/dashboard/policies", icon: ShieldCheck },
  { label: "Audit Log", href: "/dashboard/audit", icon: FileText },
  { label: "Interactive Demo", href: "/dashboard/demo", icon: PlayCircle },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-[#0d131f] border-r border-[#1e293b] flex flex-col justify-between h-screen sticky top-0 shrink-0 select-none">
      <div>
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
              Autonomous Revenue Recovery
            </p>
          </div>
        </div>

        {/* Navigation Menu */}
        <div className="px-3 py-4 space-y-1">
          <div className="px-3 pb-2 text-[10px] font-semibold tracking-wider text-slate-400 uppercase">
            Revenue Operations
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.href === "/dashboard"
                ? pathname === "/dashboard"
                : pathname?.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all",
                  isActive
                    ? "bg-blue-600/15 text-blue-400 font-semibold border border-blue-500/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-[#162032]"
                )}
              >
                <Icon className={clsx("w-4 h-4", isActive ? "text-blue-400" : "text-slate-400")} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Safety & Compliance Badge */}
      <div className="p-3 border-t border-[#1e293b]">
        <div className="bg-[#131d2e] rounded-lg p-3 border border-[#1e293b]/80 space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-semibold text-slate-200">Zero-Hallucination Gate</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            100% of financial disbursements verified by deterministic policy invariants.
          </p>
        </div>

        <div className="mt-2 pt-2 flex items-center justify-between text-xs text-slate-400 px-2">
          <span>Razorpay Rails</span>
          <span className="text-emerald-400 font-mono font-medium text-[11px]">SANDBOX MODE</span>
        </div>
      </div>
    </aside>
  );
}

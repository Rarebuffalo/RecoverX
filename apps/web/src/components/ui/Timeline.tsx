import React from "react";
import { CheckCircle2, Clock, Zap, Shield, FileCheck, ArrowRight } from "lucide-react";
import clsx from "clsx";

interface TimelineEvent {
  time: string;
  title: string;
  description: string;
  type: "detection" | "scoring" | "ai" | "policy" | "execution" | "settlement" | "warning";
  status: "completed" | "active" | "pending";
}

interface TimelineProps {
  events: TimelineEvent[];
}

export function Timeline({ events }: TimelineProps) {
  const getIcon = (type: TimelineEvent["type"]) => {
    switch (type) {
      case "detection":
        return <Clock className="w-4 h-4 text-amber-400" />;
      case "scoring":
        return <Zap className="w-4 h-4 text-blue-400" />;
      case "ai":
        return <Zap className="w-4 h-4 text-purple-400" />;
      case "policy":
        return <Shield className="w-4 h-4 text-emerald-400" />;
      case "execution":
        return <FileCheck className="w-4 h-4 text-blue-400" />;
      case "settlement":
        return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
      default:
        return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="space-y-4">
      {events.map((event, idx) => {
        const isLast = idx === events.length - 1;

        return (
          <div key={idx} className="flex gap-4 group">
            {/* Timeline Line & Indicator */}
            <div className="flex flex-col items-center">
              <div
                className={clsx(
                  "w-8 h-8 rounded-full flex items-center justify-center border shadow-sm shrink-0",
                  event.status === "completed" && "bg-[#162032] border-blue-500/40",
                  event.status === "active" && "bg-blue-600 border-blue-400 animate-pulse text-white",
                  event.status === "pending" && "bg-slate-900 border-slate-700 opacity-50"
                )}
              >
                {getIcon(event.type)}
              </div>
              {!isLast && <div className="w-0.5 grow bg-slate-800 my-1 group-last:hidden" />}
            </div>

            {/* Event Content */}
            <div className="pb-6 grow">
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="font-semibold text-slate-200 text-sm">{event.title}</span>
                <span className="font-mono text-slate-400 text-[11px]">{event.time}</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed bg-[#162032]/40 p-2.5 rounded-lg border border-[#1f2937]/50 mt-1">
                {event.description}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

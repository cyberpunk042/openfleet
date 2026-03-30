"use client";

/**
 * FleetHealthPanel — Immune system, teaching system, and methodology
 * activity visible in the OCMC UI.
 *
 * Consumes board memory entries tagged with immune-system, teaching-system,
 * and methodology. Displays recent activity with color-coded indicators.
 *
 * This is injected into the board page to give the PO visibility into
 * the three systems' operations.
 */

import { useEffect, useMemo, useState } from "react";

interface HealthEvent {
  id: string;
  content: string;
  tags: string[];
  source: string;
  created_at: string;
  system: "immune" | "teaching" | "methodology" | "unknown";
}

interface FleetHealthPanelProps {
  boardId: string;
  memoryEntries?: Array<{
    id: string;
    content: string;
    tags: string[];
    source: string;
    created_at: string;
  }>;
}

const SYSTEM_COLORS = {
  immune: { bg: "bg-red-50", border: "border-red-200", text: "text-red-700", dot: "bg-red-500" },
  teaching: { bg: "bg-amber-50", border: "border-amber-200", text: "text-amber-700", dot: "bg-amber-500" },
  methodology: { bg: "bg-blue-50", border: "border-blue-200", text: "text-blue-700", dot: "bg-blue-500" },
  unknown: { bg: "bg-slate-50", border: "border-slate-200", text: "text-slate-700", dot: "bg-slate-400" },
};

const SYSTEM_LABELS = {
  immune: "Immune System",
  teaching: "Teaching",
  methodology: "Methodology",
  unknown: "System",
};

function classifySystem(tags: string[]): HealthEvent["system"] {
  if (tags.includes("immune-system")) return "immune";
  if (tags.includes("teaching-system")) return "teaching";
  if (tags.includes("methodology")) return "methodology";
  return "unknown";
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

export function FleetHealthPanel({ boardId, memoryEntries }: FleetHealthPanelProps) {
  const events = useMemo<HealthEvent[]>(() => {
    if (!memoryEntries) return [];

    return memoryEntries
      .filter((entry) => {
        const tags = entry.tags || [];
        return (
          tags.includes("immune-system") ||
          tags.includes("teaching-system") ||
          tags.includes("methodology")
        );
      })
      .map((entry) => ({
        id: entry.id,
        content: entry.content,
        tags: entry.tags,
        source: entry.source,
        created_at: entry.created_at,
        system: classifySystem(entry.tags),
      }))
      .slice(0, 20);
  }, [memoryEntries]);

  if (events.length === 0) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <h3 className="text-sm font-semibold text-slate-900">Fleet Health</h3>
        <p className="mt-2 text-xs text-slate-500">
          No immune, teaching, or methodology events yet.
        </p>
      </div>
    );
  }

  // Summary counts
  const counts = {
    immune: events.filter((e) => e.system === "immune").length,
    teaching: events.filter((e) => e.system === "teaching").length,
    methodology: events.filter((e) => e.system === "methodology").length,
  };

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <h3 className="text-sm font-semibold text-slate-900">Fleet Health</h3>

      {/* Summary badges */}
      <div className="mt-2 flex gap-2">
        {counts.immune > 0 ? (
          <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-[11px] font-medium text-red-700">
            <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
            {counts.immune} immune
          </span>
        ) : null}
        {counts.teaching > 0 ? (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-medium text-amber-700">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
            {counts.teaching} teaching
          </span>
        ) : null}
        {counts.methodology > 0 ? (
          <span className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-2 py-0.5 text-[11px] font-medium text-blue-700">
            <span className="h-1.5 w-1.5 rounded-full bg-blue-500" />
            {counts.methodology} methodology
          </span>
        ) : null}
      </div>

      {/* Event list */}
      <div className="mt-3 max-h-[300px] space-y-1.5 overflow-y-auto">
        {events.map((event) => {
          const colors = SYSTEM_COLORS[event.system];
          const label = SYSTEM_LABELS[event.system];
          return (
            <div
              key={event.id}
              className={`rounded-md border ${colors.border} ${colors.bg} px-3 py-2`}
            >
              <div className="flex items-center gap-2">
                <span className={`h-2 w-2 rounded-full ${colors.dot}`} />
                <span className={`text-[11px] font-medium ${colors.text}`}>
                  {label}
                </span>
                <span className="ml-auto text-[10px] text-slate-400">
                  {formatTime(event.created_at)}
                </span>
              </div>
              <p className="mt-1 text-xs text-slate-700 line-clamp-2">
                {event.content}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
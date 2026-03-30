"use client";

/**
 * FleetEventStream — Color-coded event stream for the fleet.
 *
 * Displays board memory entries as a live event stream with
 * color-coding by system:
 * - Red/orange: immune system events
 * - Amber/yellow: teaching system events
 * - Blue: methodology events
 * - Slate: regular fleet events
 *
 * Supports filtering by system.
 */

import { useMemo, useState } from "react";

interface StreamEvent {
  id: string;
  content: string;
  tags: string[];
  source: string;
  created_at: string;
}

interface FleetEventStreamProps {
  memoryEntries?: StreamEvent[];
  maxItems?: number;
}

type SystemFilter = "all" | "immune" | "teaching" | "methodology" | "fleet";

function getSystemFromTags(tags: string[]): string {
  if (tags.includes("immune-system")) return "immune";
  if (tags.includes("teaching-system")) return "teaching";
  if (tags.includes("methodology")) return "methodology";
  return "fleet";
}

const SYSTEM_STYLES: Record<string, { dot: string; text: string }> = {
  immune: { dot: "bg-red-500", text: "text-red-600" },
  teaching: { dot: "bg-amber-500", text: "text-amber-600" },
  methodology: { dot: "bg-blue-500", text: "text-blue-600" },
  fleet: { dot: "bg-slate-400", text: "text-slate-600" },
};

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return "";
  }
}

export function FleetEventStream({ memoryEntries, maxItems = 50 }: FleetEventStreamProps) {
  const [filter, setFilter] = useState<SystemFilter>("all");

  const events = useMemo(() => {
    if (!memoryEntries) return [];

    let filtered = memoryEntries;
    if (filter !== "all") {
      filtered = memoryEntries.filter((e) => getSystemFromTags(e.tags) === filter);
    }

    return filtered.slice(0, maxItems);
  }, [memoryEntries, filter, maxItems]);

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900">Event Stream</h3>
        <div className="flex gap-1">
          {(["all", "immune", "teaching", "methodology", "fleet"] as SystemFilter[]).map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setFilter(f)}
              className={`rounded-md px-2 py-0.5 text-[10px] font-medium transition ${
                filter === f
                  ? "bg-slate-900 text-white"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {f === "all" ? "All" : f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-3 max-h-[400px] space-y-0.5 overflow-y-auto font-mono text-[11px]">
        {events.length === 0 ? (
          <p className="py-4 text-center text-xs text-slate-400">No events</p>
        ) : (
          events.map((event) => {
            const system = getSystemFromTags(event.tags);
            const styles = SYSTEM_STYLES[system];
            return (
              <div key={event.id} className="flex items-start gap-2 py-0.5">
                <span className="shrink-0 pt-1.5">
                  <span className={`block h-1.5 w-1.5 rounded-full ${styles.dot}`} />
                </span>
                <span className="shrink-0 text-slate-400">
                  {formatTime(event.created_at)}
                </span>
                <span className={`shrink-0 font-medium ${styles.text}`}>
                  {event.source}
                </span>
                <span className="text-slate-700 line-clamp-1">
                  {event.content}
                </span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
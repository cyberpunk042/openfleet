"use client";

/**
 * FleetControlBar — Fleet control dropdowns in the OCMC header.
 *
 * Always visible on every page. Four independent axes:
 * - Work Mode: where new work comes from
 * - Cycle Phase: what kind of work agents do
 * - Backend Mode: which AI backend
 * - Budget Mode: orchestrator tempo
 *
 * Reads/writes board.fleet_config via PATCH API.
 */

import { useCallback, useEffect, useState } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { customFetch } from "@/api/mutator";

const WORK_MODES = [
  { value: "full-autonomous", label: "Full Autonomous" },
  { value: "project-management-work", label: "PM Work" },
  { value: "local-work-only", label: "Local Work Only" },
  { value: "finish-current-work", label: "Finish Current" },
  { value: "work-paused", label: "Work Paused" },
];

const CYCLE_PHASES = [
  { value: "execution", label: "Execution" },
  { value: "planning", label: "Planning" },
  { value: "analysis", label: "Analysis" },
  { value: "investigation", label: "Investigation" },
  { value: "review", label: "Review" },
  { value: "crisis-management", label: "Crisis" },
];

const BACKEND_MODES = [
  { value: "claude", label: "Claude" },
  { value: "localai", label: "LocalAI" },
  { value: "openrouter", label: "OpenRouter" },
  { value: "claude+localai", label: "Claude + LocalAI" },
  { value: "claude+openrouter", label: "Claude + OpenRouter" },
  { value: "localai+openrouter", label: "LocalAI + OpenRouter" },
  { value: "claude+localai+openrouter", label: "All Backends" },
];

const BUDGET_MODES = [
  { value: "turbo", label: "Turbo", desc: "5s cycle" },
  { value: "aggressive", label: "Aggressive", desc: "15s cycle" },
  { value: "standard", label: "Standard", desc: "30s cycle" },
  { value: "economic", label: "Economic", desc: "60s cycle" },
];

interface FleetControlBarProps {
  boardId?: string;
}

export function FleetControlBar({ boardId }: FleetControlBarProps) {
  const [workMode, setWorkMode] = useState("full-autonomous");
  const [cyclePhase, setCyclePhase] = useState("execution");
  const [backendMode, setBackendMode] = useState("claude");
  const [budgetMode, setBudgetMode] = useState("standard");
  const [costUsedPct, setCostUsedPct] = useState(0);
  const [sessionCostPct, setSessionCostPct] = useState(0);
  const [loading, setLoading] = useState(false);
  const [resolvedBoardId, setResolvedBoardId] = useState<string | undefined>(boardId);
  const [workModeBeforePause, setWorkModeBeforePause] = useState<string | null>(null);

  // Auto-resolve board ID if not provided
  useEffect(() => {
    if (boardId) {
      setResolvedBoardId(boardId);
      return;
    }

    const resolveBoard = async () => {
      try {
        const resp = await customFetch<any>("/api/v1/boards?limit=10&offset=0", { method: "GET" });
        const payload = resp.data || resp;
        const boards = payload.items || [];
        const fleet = boards.find((b: any) => b.name === "Fleet Operations") || boards[0];
        if (fleet) {
          setResolvedBoardId(fleet.id);
        }
      } catch {
        // Silent fail
      }
    };

    resolveBoard();
  }, [boardId]);

  // Fetch current fleet_config from board
  useEffect(() => {
    if (!resolvedBoardId) return;

    const fetchConfig = async () => {
      try {
        const resp = await customFetch<any>(`/api/v1/boards/${resolvedBoardId}`, { method: "GET" });
        const board = resp.data || resp;
        const config = board.fleet_config || {};
        if (config.work_mode) setWorkMode(config.work_mode);
        if (config.cycle_phase) setCyclePhase(config.cycle_phase);
        if (config.backend_mode) setBackendMode(config.backend_mode);
        if (config.budget_mode) setBudgetMode(config.budget_mode);
        if (config.cost_used_pct != null) setCostUsedPct(config.cost_used_pct);
        if (config.session_cost_pct != null) setSessionCostPct(config.session_cost_pct);
        if (config.work_mode_before_pause !== undefined) setWorkModeBeforePause(config.work_mode_before_pause);
      } catch {
        // Silent fail — keep defaults
      }
    };

    fetchConfig();
    const interval = setInterval(fetchConfig, 30000);
    return () => clearInterval(interval);
  }, [resolvedBoardId]);

  // Update fleet_config on the board
  const updateConfig = useCallback(
    async (updates: Record<string, string>) => {
      if (!resolvedBoardId || loading) return;
      setLoading(true);

      try {
        const currentConfig = {
          work_mode: workMode,
          cycle_phase: cyclePhase,
          backend_mode: backendMode,
          budget_mode: budgetMode,
          updated_at: new Date().toISOString(),
          updated_by: "human",
        };

        const newConfig = { ...currentConfig, ...updates };

        await customFetch(`/api/v1/boards/${resolvedBoardId}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ fleet_config: newConfig }),
        });
      } catch {
        // Silent fail
      } finally {
        setLoading(false);
      }
    },
    [resolvedBoardId, workMode, cyclePhase, backendMode, budgetMode, loading],
  );

  const handleWorkModeChange = (value: string) => {
    setWorkMode(value);
    if (value === "work-paused") {
      // Pausing — save current mode so resume can restore it
      updateConfig({ work_mode: value, work_mode_before_pause: workMode });
    } else {
      updateConfig({ work_mode: value });
    }
  };

  const handleCyclePhaseChange = (value: string) => {
    setCyclePhase(value);
    updateConfig({ cycle_phase: value });
  };

  const handleBackendModeChange = (value: string) => {
    setBackendMode(value);
    updateConfig({ backend_mode: value });
  };

  const handleBudgetModeChange = (value: string) => {
    setBudgetMode(value);
    updateConfig({ budget_mode: value });
  };

  return (
    <div className="flex items-center gap-2">
      <Select value={workMode} onValueChange={handleWorkModeChange}>
        <SelectTrigger
          className="h-8 w-[150px] rounded-md border-slate-200 bg-white px-2 text-xs font-medium text-slate-700 shadow-none"
          disabled={loading}
        >
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {WORK_MODES.map((mode) => (
            <SelectItem key={mode.value} value={mode.value}>
              {mode.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={cyclePhase} onValueChange={handleCyclePhaseChange}>
        <SelectTrigger
          className="h-8 w-[120px] rounded-md border-slate-200 bg-white px-2 text-xs font-medium text-slate-700 shadow-none"
          disabled={loading}
        >
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {CYCLE_PHASES.map((phase) => (
            <SelectItem key={phase.value} value={phase.value}>
              {phase.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={backendMode} onValueChange={handleBackendModeChange}>
        <SelectTrigger
          className="h-8 w-[100px] rounded-md border-slate-200 bg-white px-2 text-xs font-medium text-slate-700 shadow-none"
          disabled={loading}
        >
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {BACKEND_MODES.map((mode) => (
            <SelectItem key={mode.value} value={mode.value}>
              {mode.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={budgetMode} onValueChange={handleBudgetModeChange}>
        <SelectTrigger
          className="h-8 w-[160px] rounded-md border-slate-200 bg-white px-2 text-xs font-medium text-slate-700 shadow-none"
          disabled={loading}
        >
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {BUDGET_MODES.map((mode) => (
            <SelectItem key={mode.value} value={mode.value}>
              <span>{mode.label}</span>
              <span className="ml-1 text-slate-400">{mode.desc}</span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Cost bars: 5h session + 7d weekly */}
      <div className="flex items-center gap-2" title={`5h: ${sessionCostPct}% | 7d: ${costUsedPct}%`}>
        <div className="flex flex-col gap-1">
          <div className="h-2 w-16 rounded-full bg-slate-100 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${sessionCostPct >= 90 ? "bg-red-500" : sessionCostPct >= 70 ? "bg-amber-500" : "bg-emerald-500"}`}
              style={{ width: `${Math.min(sessionCostPct, 100)}%` }}
            />
          </div>
          <div className="h-2 w-16 rounded-full bg-slate-100 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${costUsedPct >= 90 ? "bg-red-500" : costUsedPct >= 70 ? "bg-amber-500" : "bg-emerald-500"}`}
              style={{ width: `${Math.min(costUsedPct, 100)}%` }}
            />
          </div>
        </div>
        <div className="flex flex-col text-[10px] font-mono text-slate-500 leading-tight">
          <span>5h: {sessionCostPct}%</span>
          <span>7d: {costUsedPct}%</span>
        </div>
      </div>
    </div>
  );
}

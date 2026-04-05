// Fleet Heartbeat Gate Plugin
//
// Reads .brain-decision.json from agent workspace before each heartbeat.
// If decision is "silent", returns handled=true to skip the Claude call.
// The orchestrator (Python) writes these files every cycle.

import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

interface BrainDecision {
  decision: "silent" | "wake" | "strategic";
  agent: string;
  timestamp: string;
  reasons: Array<{ trigger: string; details: string; urgency: string }>;
  model_override?: string;
  effort_override?: string;
}

const DECISION_FILENAME = ".brain-decision.json";
const STALE_THRESHOLD_MS = 5 * 60 * 1000; // 5 minutes

function readBrainDecision(workspaceDir: string): BrainDecision | null {
  const path = join(workspaceDir, DECISION_FILENAME);
  if (!existsSync(path)) return null;

  try {
    const raw = readFileSync(path, "utf-8");
    const data = JSON.parse(raw) as BrainDecision;

    // Check staleness — if decision is older than 5 min, ignore it (let Claude run)
    if (data.timestamp) {
      const age = Date.now() - new Date(data.timestamp).getTime();
      if (age > STALE_THRESHOLD_MS) return null;
    }

    return data;
  } catch {
    return null;
  }
}

export default function register(api: any) {
  api.registerHook(
    "before_dispatch",
    async (event: any, ctx: any) => {
      // Only gate heartbeats, not regular messages
      if (ctx.trigger !== "heartbeat") {
        return { handled: false };
      }

      // Resolve agent workspace directory
      const workspaceDir = ctx.agentDir || ctx.workspaceDir;
      if (!workspaceDir) {
        return { handled: false };
      }

      const decision = readBrainDecision(workspaceDir);
      if (!decision) {
        // No decision file or stale — let Claude run normally
        return { handled: false };
      }

      if (decision.decision === "silent") {
        // Brain says: nothing needs attention. Skip Claude call.
        return {
          handled: true,
          text: "HEARTBEAT_OK",
        };
      }

      // WAKE or STRATEGIC — let Claude run
      return { handled: false };
    },
    { name: "fleet-heartbeat-gate" },
  );
}

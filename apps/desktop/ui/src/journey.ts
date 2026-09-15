/**
 * Reading the eighteen-step journey the Core derived, and governing the console with it.
 *
 * This module holds the only journey logic the interface is allowed to have: parsing the payload
 * and deciding which panel a step opens. Everything else — what a step means, when it is done —
 * is derived in `vera_mmu/wizard.py` and merely displayed here. Recomputing any of it in
 * TypeScript would let the two drift, and it is the interface that would end up lying.
 *
 * One rule matters more than the mapping: a journey that has not been read yet closes nothing.
 * Locking a panel because we have not asked would be acting on absent information, which is the
 * one thing this product refuses everywhere else.
 */

export type JourneyStep = {
  id: string;
  index: number;
  label: string;
  state: "BLOCKED" | "AVAILABLE" | "COMPLETED" | "NOT_OBSERVABLE";
  reason: string;
};

export type PanelId = "observe" | "prepare" | "identity" | "capabilities" | "gates" | "integrate" | "verify";

export type PanelAccess = { open: boolean; reason: string };

/** Which journey step governs each panel of the console. */
export const PANEL_STEPS: Record<PanelId, string> = {
  observe: "scan-project",
  prepare: "choose-domain",
  identity: "choose-domain",
  capabilities: "declare-capabilities",
  gates: "build-gates",
  integrate: "generate",
  verify: "run-doctor",
};

const STATES = ["BLOCKED", "AVAILABLE", "COMPLETED", "NOT_OBSERVABLE"] as const;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** Read the steps the Core derived, discarding anything that is not one. */
export function readJourney(value: unknown): JourneyStep[] {
  if (!isRecord(value) || !Array.isArray(value.steps)) return [];
  return value.steps
    .filter(isRecord)
    .map((step) => ({
      id: typeof step.id === "string" ? step.id : "",
      index: typeof step.index === "number" ? step.index : 0,
      label: typeof step.label === "string" ? step.label : "Étape inconnue",
      state: (STATES as readonly string[]).includes(String(step.state))
        ? (step.state as JourneyStep["state"])
        : "BLOCKED",
      reason: typeof step.reason === "string" ? step.reason : "",
    }))
    .filter((step) => step.id.length > 0);
}

/** Say whether a panel may be used, and when it may not, why — in the Core's own words. */
export function panelAccess(steps: JourneyStep[], panel: PanelId): PanelAccess {
  // A journey not yet read, and a step absent from the payload, are the same situation: we do
  // not know. Closing a panel on that would be acting on absent information.
  const step = steps.find((candidate) => candidate.id === PANEL_STEPS[panel]);
  if (step === undefined) return { open: true, reason: "" };
  if (step.state !== "BLOCKED") return { open: true, reason: "" };
  return { open: false, reason: step.reason };
}

/** How many of the eighteen steps the project actually carries the evidence for. */
export function completedCount(steps: JourneyStep[]): number {
  return steps.filter((step) => step.state === "COMPLETED").length;
}

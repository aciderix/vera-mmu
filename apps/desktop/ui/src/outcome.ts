/**
 * Reading the journey's conclusion the Core computed, and nothing more.
 *
 * The verdict, the two step-15 and step-18 rows and the failing checks all come from
 * `vera_mmu/journey_outcome.py`. This module parses them; it never decides that a project is
 * healthy, because the one screen that says "done" is the one that must never say it on its own.
 *
 * Its refusals point the same way — towards claiming less. A status it cannot read is `FAILED`,
 * never `COMPLETE`: an unreadable payload is a project nobody vouched for, and the two must not
 * look alike. A failing check missing its remediation is still shown, with the gap named, rather
 * than dropped for being incomplete.
 */

export type OutcomeStatus = "INCOMPLETE" | "REFUSED" | "FAILED" | "COMPLETE";
export type RowStatus = "VALID" | "PASS" | "REFUSED" | "FAIL" | "NOT_REACHED";

export type FailingCheck = { name: string; detail: string; remediation: string };
export type OutcomeRow = { status: RowStatus; detail: string };
export type RemainingStep = { id: string; index: number; label: string; state: string; reason: string };

const OUTCOME_STATES = ["INCOMPLETE", "REFUSED", "FAILED", "COMPLETE"] as const;
const ROW_STATES = ["VALID", "PASS", "REFUSED", "FAIL", "NOT_REACHED"] as const;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function text(value: unknown, fallback: string): string {
  return typeof value === "string" && value.length > 0 ? value : fallback;
}

/** The single verdict, with anything unreadable read as a project that did not conclude. */
export function readStatus(payload: Record<string, unknown> | null): OutcomeStatus {
  if (!isRecord(payload)) return "FAILED";
  return (OUTCOME_STATES as readonly string[]).includes(String(payload.status))
    ? (payload.status as OutcomeStatus)
    : "FAILED";
}

/** The sentence the Core wrote about this project; never composed here. */
export function readVerdict(payload: Record<string, unknown> | null): string {
  if (!isRecord(payload)) return "Aucune conclusion lisible : le Core n’a rendu aucun verdict.";
  return text(payload.verdict, "Aucune conclusion lisible : le Core n’a rendu aucun verdict.");
}

/** One of the two closing rows — `validation` for step 15, `doctor` for step 18. */
export function readRow(payload: Record<string, unknown> | null, key: "validation" | "doctor"): OutcomeRow {
  const row = isRecord(payload) && isRecord(payload[key]) ? payload[key] : null;
  if (row === null) return { status: "FAIL", detail: "Le Core n’a rendu aucune ligne pour cette étape." };
  return {
    status: (ROW_STATES as readonly string[]).includes(String(row.status)) ? (row.status as RowStatus) : "FAIL",
    detail: text(row.detail, ""),
  };
}

/** The Doctor rows that failed, each carrying the repair the Core named for it. */
export function readFailing(payload: Record<string, unknown> | null): FailingCheck[] {
  const row = isRecord(payload) && isRecord(payload.doctor) ? payload.doctor : null;
  if (row === null || !Array.isArray(row.failing)) return [];
  return (row.failing as unknown[]).filter(isRecord).map((item) => ({
    name: text(item.name, "contrôle inconnu"),
    detail: text(item.detail, ""),
    remediation: text(item.remediation, "Le Core n’a nommé aucune réparation pour ce contrôle."),
  }));
}

/** The steps still open, in the order the journey declares them. */
export function readRemaining(payload: Record<string, unknown> | null): RemainingStep[] {
  const steps = isRecord(payload) && isRecord(payload.steps) ? payload.steps : null;
  if (steps === null || !Array.isArray(steps.remaining)) return [];
  return (steps.remaining as unknown[]).filter(isRecord).map((item) => ({
    id: text(item.id, ""),
    index: typeof item.index === "number" && Number.isFinite(item.index) ? item.index : 0,
    label: text(item.label, "Étape inconnue"),
    state: text(item.state, "BLOCKED"),
    reason: text(item.reason, ""),
  }));
}

/** How many of the journey's steps carry their evidence, `null` when the payload does not say. */
export function readProgress(payload: Record<string, unknown> | null): { completed: number; total: number } | null {
  const steps = isRecord(payload) && isRecord(payload.steps) ? payload.steps : null;
  if (steps === null) return null;
  const { completed, total } = steps;
  if (typeof completed !== "number" || typeof total !== "number" || !Number.isFinite(completed) || !Number.isFinite(total)) {
    return null;
  }
  return { completed, total };
}

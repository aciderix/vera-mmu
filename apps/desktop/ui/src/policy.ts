/**
 * Reading the policy lines the Core published, and nothing more.
 *
 * Which values a line accepts, and whether anything enforces it, are decided in
 * `vera_mmu/policy_catalog.py`. This module only reads them, and carries one refusal of its own,
 * in the direction that claims less: a line whose enforcement the payload does not state is shown
 * as `DECLARED_ONLY`, never as enforced. Announcing a rule as applied when we could not read that
 * it is would be the politest kind of lie — someone would tighten a line and believe it holds.
 */

export type PolicyLine = {
  section: string;
  key: string;
  value: string | string[] | null;
  /** The closed set of values, or null when the line holds a list the Core validates itself. */
  values: string[] | null;
  enforcement: "ENFORCED" | "DECLARED_ONLY";
  reason: string;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function stringList(value: unknown): string[] | null {
  return Array.isArray(value) && value.every((item) => typeof item === "string") ? (value as string[]) : null;
}

/** Read the policy lines of an options or preview payload, discarding anything that is not one. */
export function readPolicyLines(payload: Record<string, unknown> | null): PolicyLine[] {
  if (!isRecord(payload) || !Array.isArray(payload.lines)) return [];
  return (payload.lines as unknown[])
    .filter(isRecord)
    .map((line) => ({
      section: typeof line.section === "string" ? line.section : "",
      key: typeof line.key === "string" ? line.key : "",
      value: typeof line.value === "string" ? line.value : stringList(line.value),
      values: stringList(line.values),
      // Anything but an explicit ENFORCED is read as merely declared.
      enforcement: line.enforcement === "ENFORCED" ? ("ENFORCED" as const) : ("DECLARED_ONLY" as const),
      reason: typeof line.reason === "string" ? line.reason : "",
    }))
    .filter((line) => line.section.length > 0 && line.key.length > 0);
}

/** Render one line's current value for an input field, whatever shape it holds. */
export function policyValueText(line: PolicyLine): string {
  if (line.value === null) return "";
  return Array.isArray(line.value) ? line.value.join(", ") : line.value;
}

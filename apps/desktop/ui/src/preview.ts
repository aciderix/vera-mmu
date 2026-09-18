/**
 * Reading the §34 MCP Preview the Core compiled, and nothing more.
 *
 * Every figure, hash and alert is produced in `vera_mmu/mcp_preview.py` from the compiled package.
 * This module must never compute one: a second calculation is a second opinion, and the screen
 * would eventually show the wrong one.
 *
 * Its refusals both point the same way — towards claiming less. A count it cannot read is `null`,
 * never `0`, because "nothing" and "we could not tell" look identical on a dashboard and only one
 * of them is safe. And an alert whose status it cannot read is shown as raised, because a warning
 * displayed for nothing costs a second while one silently dropped costs the thing it warned about.
 */

export type PreviewAlert = {
  id: string;
  severity: "ERROR" | "WARNING";
  status: "RAISED" | "CLEAR" | "NOT_APPLICABLE";
  message: string;
  instances: string[];
};

const COUNT_KEYS = [
  "core_tools",
  "project_tools",
  "read_only",
  "write",
  "sensitive",
  "network",
  "gates",
  "capabilities",
] as const;

export type CountKey = (typeof COUNT_KEYS)[number];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** The eight figures §34 displays, each `null` when the payload does not carry it. */
export function readCounts(payload: Record<string, unknown> | null): Record<CountKey, number | null> {
  const counts = isRecord(payload) && isRecord(payload.counts) ? payload.counts : {};
  const result = {} as Record<CountKey, number | null>;
  for (const key of COUNT_KEYS) {
    const value = counts[key];
    result[key] = typeof value === "number" && Number.isFinite(value) ? value : null;
  }
  return result;
}

/** The hashes the build is bound to, in the order §34 shows them. */
export function readHashes(payload: Record<string, unknown> | null): { label: string; value: string }[] {
  if (!isRecord(payload) || !isRecord(payload.hashes)) return [];
  const hashes = payload.hashes;
  return ["profile_hash", "policy_hash", "capability_catalog_hash", "gate_catalog_hash", "mcp_build_hash", "package_hash"]
    .map((label) => ({ label, value: hashes[label] }))
    .filter((item): item is { label: string; value: string } => typeof item.value === "string" && item.value.length > 0);
}

/** The alerts the Core evaluated, with an unreadable status read as raised. */
export function readAlerts(payload: Record<string, unknown> | null): PreviewAlert[] {
  if (!isRecord(payload) || !Array.isArray(payload.alerts)) return [];
  return (payload.alerts as unknown[]).filter(isRecord).map((item) => ({
    id: typeof item.id === "string" ? item.id : "alerte",
    severity: item.severity === "WARNING" ? "WARNING" : "ERROR",
    status: item.status === "CLEAR" || item.status === "NOT_APPLICABLE" ? item.status : "RAISED",
    message: typeof item.message === "string" ? item.message : "",
    instances: Array.isArray(item.instances) ? item.instances.filter((entry): entry is string => typeof entry === "string") : [],
  }));
}

/** Whether anything would block a clean generation: an ERROR the Core actually raised. */
export function blockingAlerts(alerts: PreviewAlert[]): PreviewAlert[] {
  return alerts.filter((alert) => alert.status === "RAISED" && alert.severity === "ERROR");
}

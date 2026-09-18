/**
 * Reading the resume contract the Core published, and what a change to it would break.
 *
 * The contract's own rules — at least one required section, a budget big enough to hold them,
 * an integration the project actually declares — live in `vera_mmu/resume_editor.py`. This module
 * reads the answer.
 *
 * Its one refusal is about the notice, not the rules: a payload whose `invalidates` list cannot be
 * read yields **no** claim rather than an empty one. "This breaks nothing" and "we could not tell"
 * are different sentences, and only the first is safe to put on a screen next to a confirm button.
 */

export type ResumeSection = { id: string; required: boolean };
export type ArmedGuard = { adapterId: string; status: string; resumeContractHash: string; reason: string };

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** Read the declared resume sections, keeping their order and their required flag. */
export function readSections(payload: Record<string, unknown> | null): ResumeSection[] {
  if (!isRecord(payload) || !Array.isArray(payload.sections)) return [];
  return (payload.sections as unknown[])
    .filter(isRecord)
    .map((item) => ({
      id: typeof item.id === "string" ? item.id : "",
      // An unreadable flag is read as optional: claiming a section is required when we could not
      // tell would announce a contract stricter than the one the Core holds.
      required: item.required === true,
    }))
    .filter((item) => item.id.length > 0);
}

/** Read the integrations the project declares and those it has enabled. */
export function readIntegrations(payload: Record<string, unknown> | null): { enabled: string[]; available: string[] } {
  const empty = { enabled: [] as string[], available: [] as string[] };
  if (!isRecord(payload) || !isRecord(payload.integrations)) return empty;
  const block = payload.integrations;
  const list = (value: unknown): string[] =>
    Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
  return { enabled: list(block.enabled), available: list(block.available) };
}

/**
 * What an edit would invalidate, or `null` when the payload does not say.
 *
 * `null` and `[]` mean different things and the screen must not merge them: an empty list is the
 * Core stating that nothing is armed, and `null` is the absence of an answer.
 */
export function readInvalidated(payload: Record<string, unknown> | null, key = "invalidates"): ArmedGuard[] | null {
  if (!isRecord(payload) || !Array.isArray(payload[key])) return null;
  return (payload[key] as unknown[]).filter(isRecord).map((item) => ({
    adapterId: typeof item.adapter_id === "string" ? item.adapter_id : "",
    status: typeof item.status === "string" ? item.status : "UNKNOWN",
    resumeContractHash: typeof item.resume_contract_hash === "string" ? item.resume_contract_hash : "",
    reason: typeof item.reason === "string" ? item.reason : "",
  }));
}

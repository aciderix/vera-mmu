/**
 * Reading the declared structure of a project: its taxonomy and its Work Graph (steps 5 to 8).
 *
 * Both payloads come from the Core — `profile_taxonomy.py` and `work_graph_config.py` — and this
 * module only parses them. It decides nothing: which modes exist, what a removal would orphan and
 * whether the lifecycle can be edited are all the Core's to say.
 *
 * Its refusals point towards claiming less, and here that has a precise direction. A usage count
 * it cannot read is `null`, never `0`: zero reads as "safe to remove", and a type wrongly shown as
 * unused is the one mistake that orphans records. A lifecycle whose `editable` flag is unreadable
 * is treated as fixed, because offering an edit the Core would refuse is worse than withholding
 * one it would have allowed.
 */

export type TaxonomySection = {
  section: string;
  declared: string[];
  required: boolean;
  usage: Record<string, number | null>;
};

export type TaxonomyChange = { section: string; added: string[]; removed: string[]; declared: string[] };

export type PolicyLine = { id: string; status: string; mode: string | null; availableModes: string[] };

export type Lifecycle = { states: string[]; initialState: string | null; transitions: number; editable: boolean };

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function strings(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

/** The three editable sections, each with what the memory already holds under every type. */
export function readTaxonomySections(payload: Record<string, unknown> | null): TaxonomySection[] {
  const sections = isRecord(payload) && isRecord(payload.sections) ? payload.sections : null;
  if (sections === null) return [];
  return Object.keys(sections)
    .sort()
    .filter((name) => isRecord(sections[name]))
    .map((name) => {
      const block = sections[name] as Record<string, unknown>;
      const declared = strings(block.declared);
      const counts = isRecord(block.usage) ? block.usage : {};
      const usage: Record<string, number | null> = {};
      for (const item of declared) {
        const value = counts[item];
        usage[item] = typeof value === "number" && Number.isFinite(value) ? value : null;
      }
      return { section: name, declared, required: block.required === true, usage };
    });
}

/** Whether removing this type is known to orphan nothing — unknown is never "yes". */
export function isSafeToRemove(section: TaxonomySection, type: string): boolean {
  return section.usage[type] === 0;
}

/** What an edit would add and remove, section by section. */
export function readChanges(payload: Record<string, unknown> | null): TaxonomyChange[] {
  if (!isRecord(payload) || !Array.isArray(payload.changes)) return [];
  return (payload.changes as unknown[]).filter(isRecord).map((item) => ({
    section: typeof item.section === "string" ? item.section : "",
    added: strings(item.added),
    removed: strings(item.removed),
    declared: strings(item.declared),
  }));
}

/** The Core's refusals, verbatim. */
export function readBlockers(payload: Record<string, unknown> | null): string[] {
  return isRecord(payload) ? strings(payload.blockers) : [];
}

/** The two transition policies, with the closed set of modes each may take. */
export function readPolicyLines(payload: Record<string, unknown> | null): PolicyLine[] {
  if (!isRecord(payload)) return [];
  return (["start_policy", "completion_policy"] as const)
    .filter((key) => isRecord(payload[key]))
    .map((key) => {
      const block = payload[key] as Record<string, unknown>;
      return {
        id: key,
        status: typeof block.status === "string" ? block.status : "NOT_DECLARED",
        mode: typeof block.mode === "string" ? block.mode : null,
        availableModes: strings(block.available_modes),
      };
    });
}

/** The Core's lifecycle, read as fixed whenever the payload does not clearly say otherwise. */
export function readLifecycle(payload: Record<string, unknown> | null): Lifecycle | null {
  if (!isRecord(payload) || !Array.isArray(payload.states)) return null;
  return {
    states: strings(payload.states),
    initialState: typeof payload.initial_state === "string" ? payload.initial_state : null,
    transitions: Array.isArray(payload.transitions) ? payload.transitions.length : 0,
    editable: payload.editable === true,
  };
}

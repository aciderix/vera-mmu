/**
 * The interface's only structure-reading logic, under test.
 *
 * What the Core decides is proven in `tests/test_profile_taxonomy.py` and
 * `tests/test_work_graph_config.py`. What is pinned here is that the screen never softens what it
 * reads: an unreadable usage count is `null` rather than `0`, so a type is never shown as safe to
 * remove on missing information, and an unreadable lifecycle reads as fixed rather than editable.
 */
import { describe, expect, it } from "vitest";

import {
  isSafeToRemove,
  readBlockers,
  readChanges,
  readLifecycle,
  readPolicyLines,
  readTaxonomySections,
} from "./structure";

const options = {
  format: "vera-taxonomy-edit/v1",
  sections: {
    knowledge: { declared: ["DECISION", "FACT"], required: true, usage: { DECISION: 12, FACT: 0 } },
    entities: { declared: ["COMPONENT"], required: false, usage: { COMPONENT: 0 } },
    relations: { declared: [], required: false, usage: {} },
  },
};

const workGraph = {
  format: "vera-work-graph/v1",
  enabled: true,
  states: ["PLANNED", "IN_PROGRESS", "DONE"],
  initial_state: "PLANNED",
  transitions: [{ from: "PLANNED", event: "start", to: "IN_PROGRESS" }],
  editable: false,
  start_policy: { status: "DECLARED", mode: "EXPLICIT", available_modes: ["AUTOMATIC", "EXPLICIT"] },
  completion_policy: { status: "NOT_DECLARED", mode: null, available_modes: ["GATE_BACKED"] },
};

describe("readTaxonomySections", () => {
  it("reads the three sections in a stable order, with their usage", () => {
    const sections = readTaxonomySections(options);
    expect(sections.map((item) => item.section)).toEqual(["entities", "knowledge", "relations"]);
    const knowledge = sections.find((item) => item.section === "knowledge")!;
    expect(knowledge.declared).toEqual(["DECISION", "FACT"]);
    expect(knowledge.required).toBe(true);
    expect(knowledge.usage).toEqual({ DECISION: 12, FACT: 0 });
  });

  it("reads an unreadable usage count as null, never as zero", () => {
    // Zero reads as "safe to remove"; a type wrongly shown unused is what orphans records.
    const sections = readTaxonomySections({ sections: { knowledge: { declared: ["A", "B"], usage: { A: "12" } } } });
    expect(sections[0].usage).toEqual({ A: null, B: null });
  });

  it("returns nothing for anything that is not a taxonomy reading", () => {
    for (const value of [null, {}, { sections: [] }]) {
      expect(readTaxonomySections(value as Record<string, unknown> | null)).toEqual([]);
    }
  });
});

describe("isSafeToRemove", () => {
  it("says yes only on a count the Core actually gave as zero", () => {
    const [, knowledge] = readTaxonomySections(options);
    expect(isSafeToRemove(knowledge, "FACT")).toBe(true);
    expect(isSafeToRemove(knowledge, "DECISION")).toBe(false);
  });

  it("says no on an unknown count and on an unknown type", () => {
    const [section] = readTaxonomySections({ sections: { knowledge: { declared: ["A"], usage: {} } } });
    expect(isSafeToRemove(section, "A")).toBe(false);
    expect(isSafeToRemove(section, "ABSENT")).toBe(false);
  });
});

describe("readChanges and readBlockers", () => {
  it("reads what an edit would add and remove", () => {
    const preview = { changes: [{ section: "knowledge", added: ["NEW"], removed: [], declared: ["NEW"] }], blockers: [] };
    expect(readChanges(preview)).toEqual([{ section: "knowledge", added: ["NEW"], removed: [], declared: ["NEW"] }]);
    expect(readBlockers(preview)).toEqual([]);
  });

  it("shows the Core's refusals verbatim", () => {
    expect(readBlockers({ blockers: ["`DECISION` porte déjà 12 enregistrement(s)"] })).toEqual([
      "`DECISION` porte déjà 12 enregistrement(s)",
    ]);
    expect(readBlockers(null)).toEqual([]);
  });
});

describe("readPolicyLines", () => {
  it("reads both transition policies with their closed set of modes", () => {
    const [start, completion] = readPolicyLines(workGraph);
    expect(start).toEqual({ id: "start_policy", status: "DECLARED", mode: "EXPLICIT", availableModes: ["AUTOMATIC", "EXPLICIT"] });
    expect(completion.status).toBe("NOT_DECLARED");
    expect(completion.mode).toBeNull();
  });

  it("reads an unreadable status as undeclared rather than as declared", () => {
    const [line] = readPolicyLines({ start_policy: { status: 7, mode: 7, available_modes: "all" } });
    expect(line.status).toBe("NOT_DECLARED");
    expect(line.availableModes).toEqual([]);
  });
});

describe("readLifecycle", () => {
  it("reads the Core's lifecycle", () => {
    expect(readLifecycle(workGraph)).toEqual({
      states: ["PLANNED", "IN_PROGRESS", "DONE"],
      initialState: "PLANNED",
      transitions: 1,
      editable: false,
    });
  });

  it("never reads a lifecycle as editable on missing information", () => {
    // Offering an edit the Core would refuse is worse than withholding one it would allow.
    for (const value of [{ states: [], editable: "true" }, { states: [], editable: 1 }, { states: [] }]) {
      expect(readLifecycle(value)!.editable).toBe(false);
    }
    expect(readLifecycle(null)).toBeNull();
  });
});

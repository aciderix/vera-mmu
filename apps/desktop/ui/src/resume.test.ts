/**
 * The interface's only resume-contract logic, under test.
 *
 * The contract's rules are proven in `tests/test_resume_editor.py`. What is pinned here is that
 * the screen never overstates: an unreadable required flag is read as optional, and an absent
 * `invalidates` list is `null` — "we could not tell" — rather than an empty list meaning
 * "this breaks nothing".
 */
import { describe, expect, it } from "vitest";

import { readIntegrations, readInvalidated, readSections } from "./resume";

const options = {
  format: "vera-resume-edit/v1",
  sections: [
    { id: "working-rules", required: true },
    { id: "notes", required: false },
  ],
  integrations: { enabled: ["generic-mcp"], available: ["codex", "generic-mcp"] },
  invalidates: [
    { adapter_id: "generic-mcp", status: "ARMED", resume_contract_hash: "a".repeat(64), reason: "changera" },
  ],
};

describe("readSections", () => {
  it("reads the declared sections in order, with their required flag", () => {
    expect(readSections(options)).toEqual([
      { id: "working-rules", required: true },
      { id: "notes", required: false },
    ]);
  });

  it("reads an unreadable required flag as optional rather than as required", () => {
    // Announcing a stricter contract than the Core holds would misdescribe what a handoff needs.
    for (const required of [undefined, "true", 1, null]) {
      expect(readSections({ sections: [{ id: "risks", required }] })[0].required).toBe(false);
    }
  });

  it("drops an entry without an identifier and anything that is not a contract", () => {
    expect(readSections({ sections: [{ required: true }, "risks"] })).toEqual([]);
    for (const value of [null, {}, { sections: "risks" }]) {
      expect(readSections(value as Record<string, unknown> | null)).toEqual([]);
    }
  });
});

describe("readIntegrations", () => {
  it("reads what is enabled and what the project declares", () => {
    expect(readIntegrations(options)).toEqual({ enabled: ["generic-mcp"], available: ["codex", "generic-mcp"] });
  });

  it("offers nothing when the Core published nothing", () => {
    for (const value of [null, {}, { integrations: "none" }, { integrations: { enabled: 3 } }]) {
      expect(readIntegrations(value as Record<string, unknown> | null)).toEqual({ enabled: [], available: [] });
    }
  });
});

describe("readInvalidated", () => {
  it("reads the guards the Core says a change would break", () => {
    expect(readInvalidated(options)).toEqual([
      { adapterId: "generic-mcp", status: "ARMED", resumeContractHash: "a".repeat(64), reason: "changera" },
    ]);
  });

  it("distinguishes 'nothing is armed' from 'the payload did not say'", () => {
    expect(readInvalidated({ invalidates: [] })).toEqual([]);
    for (const value of [null, {}, { invalidates: "none" }]) {
      expect(readInvalidated(value as Record<string, unknown> | null)).toBeNull();
    }
  });

  it("reads the applied result under its own key", () => {
    expect(readInvalidated({ invalidated: [] }, "invalidated")).toEqual([]);
  });
});

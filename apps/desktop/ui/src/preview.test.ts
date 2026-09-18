/**
 * The interface's only MCP-preview logic, under test.
 *
 * The figures and the alerts are produced in `vera_mmu/mcp_preview.py` and proven in
 * `tests/test_mcp_preview.py`. What is pinned here is that the screen never softens what it
 * reads: an unreadable count is `null` rather than `0`, and an unreadable alert status is raised
 * rather than clear.
 */
import { describe, expect, it } from "vitest";

import { blockingAlerts, readAlerts, readCounts, readHashes } from "./preview";

const payload = {
  format: "vera-mcp-preview/v1",
  counts: { core_tools: 47, project_tools: 0, read_only: 25, write: 22, sensitive: 3, network: 0, gates: 3, capabilities: 3 },
  hashes: { profile_hash: "a".repeat(64), policy_hash: "b".repeat(64), package_hash: "c".repeat(64) },
  alerts: [
    { id: "capability_without_objective_validator", severity: "ERROR", status: "RAISED", message: "x", instances: ["lint"] },
    { id: "gate_depends_on_network_capability", severity: "WARNING", status: "NOT_APPLICABLE", message: "y", instances: [] },
  ],
};

describe("readCounts", () => {
  it("reads the eight figures §34 displays", () => {
    const counts = readCounts(payload);
    expect(counts.core_tools).toBe(47);
    expect(counts.network).toBe(0);
    expect(counts.capabilities).toBe(3);
  });

  it("reads a figure it cannot read as null, never as zero", () => {
    // On a dashboard "none" and "we could not tell" look identical, and only one is safe.
    const counts = readCounts({ counts: { core_tools: "47", gates: null } });
    expect(counts.core_tools).toBeNull();
    expect(counts.gates).toBeNull();
    expect(readCounts(null).write).toBeNull();
  });
});

describe("readHashes", () => {
  it("reads the hashes present, in the order the screen shows them", () => {
    expect(readHashes(payload).map((item) => item.label)).toEqual(["profile_hash", "policy_hash", "package_hash"]);
  });

  it("drops anything that is not a hash rather than rendering it", () => {
    expect(readHashes({ hashes: { profile_hash: 42, policy_hash: "" } })).toEqual([]);
    expect(readHashes(null)).toEqual([]);
  });
});

describe("readAlerts", () => {
  it("reads the alerts the Core evaluated, with their instances", () => {
    const [first, second] = readAlerts(payload);
    expect(first).toEqual({ id: "capability_without_objective_validator", severity: "ERROR", status: "RAISED", message: "x", instances: ["lint"] });
    expect(second.status).toBe("NOT_APPLICABLE");
  });

  it("reads an unreadable status as raised rather than as clear", () => {
    // A warning shown for nothing costs a second; one silently dropped costs what it warned about.
    for (const status of [undefined, "FINE", 1, null]) {
      expect(readAlerts({ alerts: [{ id: "x", status }] })[0].status).toBe("RAISED");
    }
  });

  it("returns nothing for anything that is not a preview", () => {
    for (const value of [null, {}, { alerts: "none" }]) {
      expect(readAlerts(value as Record<string, unknown> | null)).toEqual([]);
    }
  });
});

describe("blockingAlerts", () => {
  it("keeps only the errors the Core actually raised", () => {
    expect(blockingAlerts(readAlerts(payload)).map((item) => item.id)).toEqual(["capability_without_objective_validator"]);
  });

  it("does not treat an impossible alert as blocking", () => {
    const alerts = readAlerts({ alerts: [{ id: "x", severity: "ERROR", status: "NOT_APPLICABLE" }] });
    expect(blockingAlerts(alerts)).toEqual([]);
  });
});

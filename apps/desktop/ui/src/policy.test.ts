/**
 * The interface's only policy logic, under test.
 *
 * The closed values and the enforcement status are decided in `vera_mmu/policy_catalog.py` and
 * proven in `tests/test_policy_editor.py`. What is pinned here is the one refusal the screen owns:
 * a line whose enforcement it could not read is shown as merely declared, never as enforced.
 */
import { describe, expect, it } from "vitest";

import { policyValueText, readPolicyLines } from "./policy";

const options = {
  format: "vera-policy-edit/v1",
  lines: [
    { section: "filesystem", key: "write", value: "confirm", values: ["allow", "confirm", "deny"], enforcement: "ENFORCED", reason: "require_project_write" },
    { section: "filesystem", key: "read", value: "allow", values: ["allow", "confirm", "deny"], enforcement: "DECLARED_ONLY", reason: "rien ne la lit" },
    { section: "process", key: "allowed_runners", value: ["NOOP"], values: null, enforcement: "ENFORCED", reason: "croisement" },
  ],
};

describe("readPolicyLines", () => {
  it("reads every line the Core published, scalar and list alike", () => {
    const lines = readPolicyLines(options);
    expect(lines).toHaveLength(3);
    expect(lines[0]).toEqual({ section: "filesystem", key: "write", value: "confirm", values: ["allow", "confirm", "deny"], enforcement: "ENFORCED", reason: "require_project_write" });
    expect(lines[2].value).toEqual(["NOOP"]);
    expect(lines[2].values).toBeNull();
  });

  it("shows a line it could not read the enforcement of as merely declared", () => {
    // Announcing a rule as applied when we could not read that it is would let someone tighten a
    // line and believe it holds.
    for (const enforcement of [undefined, "enforced", "YES", 1]) {
      const [line] = readPolicyLines({ lines: [{ section: "git", key: "push", enforcement }] });
      expect(line.enforcement).toBe("DECLARED_ONLY");
    }
  });

  it("drops an entry that does not name a line rather than inventing one", () => {
    expect(readPolicyLines({ lines: [{ key: "write" }, { section: "git" }, "push"] })).toEqual([]);
  });

  it("returns nothing for anything that is not a policy payload", () => {
    for (const value of [null, {}, { lines: "none" }]) {
      expect(readPolicyLines(value as Record<string, unknown> | null)).toEqual([]);
    }
  });
});

describe("policyValueText", () => {
  it("renders a scalar as itself and a list as a comma-separated field", () => {
    const [scalar, , list] = readPolicyLines(options);
    expect(policyValueText(scalar)).toBe("confirm");
    expect(policyValueText(list)).toBe("NOOP");
  });

  it("renders an unreadable value as empty rather than as the word null", () => {
    const [line] = readPolicyLines({ lines: [{ section: "git", key: "push", value: 42 }] });
    expect(policyValueText(line)).toBe("");
  });
});

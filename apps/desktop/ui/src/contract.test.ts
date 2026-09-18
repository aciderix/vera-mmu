/**
 * The interface's only capability-contract logic, under test.
 *
 * Narrow on purpose, like `journey.test.ts`. The rules of §32 live in the Core and are proven in
 * `tests/test_capability_builder.py`; what is pinned here is that the console reads them without
 * ever substituting one of its own — and, above all, the two directions absence must take: an
 * unpublished catalogue offers nothing rather than a hard-coded list, and a preview that is not a
 * reviewed contract cannot be confirmed.
 */
import { describe, expect, it } from "vitest";

import { asChoices, asList, asRefusals, isConfirmable } from "./contract";

describe("asList", () => {
  it("splits a typed field into trimmed, non-empty entries", () => {
    expect(asList(" tool , findings ,, ")).toEqual(["tool", "findings"]);
  });

  it("returns nothing for an empty field rather than one empty name", () => {
    expect(asList("   ")).toEqual([]);
  });

  it("never judges what it splits: an invalid name travels to the Core intact", () => {
    // Refusing here would let the interface and the Core disagree about what is valid.
    expect(asList("../etc/passwd, Tool")).toEqual(["../etc/passwd", "Tool"]);
  });
});

describe("asChoices", () => {
  it("reads a plain closed catalogue the Core published", () => {
    expect(asChoices({ validators: ["EVIDENCE_HASH", "EVIDENCE_FIELDS"] }, "validators"))
      .toEqual(["EVIDENCE_HASH", "EVIDENCE_FIELDS"]);
  });

  it("reads an annotated catalogue by its identifiers", () => {
    expect(asChoices({ runners: [{ id: "NOOP", consumes_validator: false }, { id: "EVIDENCE_HASH" }] }, "runners"))
      .toEqual(["NOOP", "EVIDENCE_HASH"]);
  });

  it("offers nothing when the Core has published nothing", () => {
    // A hard-coded fallback would be the interface inventing a closed set the Core owns.
    for (const value of [null, {}, { runners: "NOOP" }, { runners: [42, {}, ""] }]) {
      expect(asChoices(value as Record<string, unknown> | null, "runners")).toEqual([]);
    }
  });
});

describe("asRefusals", () => {
  it("reads the refusals the Core named, with their codes", () => {
    expect(asRefusals({ refusals: [{ code: "MISSING_TIMEOUT", message: "Timeout absent." }] }))
      .toEqual([{ code: "MISSING_TIMEOUT", message: "Timeout absent." }]);
  });

  it("keeps a refusal whose code is unreadable rather than dropping it", () => {
    expect(asRefusals({ refusals: [{ message: "Refusé." }] })).toEqual([{ code: "REFUSED", message: "Refusé." }]);
  });

  it("returns nothing for anything that is not a preview", () => {
    for (const value of [null, {}, { refusals: "none" }]) {
      expect(asRefusals(value as Record<string, unknown> | null)).toEqual([]);
    }
  });
});

describe("isConfirmable", () => {
  it("allows confirmation only for a reviewed contract the Core did not refuse", () => {
    expect(isConfirmable({ status: "PREVIEW", refusals: [] })).toBe(true);
  });

  it("refuses a contract the Core refused", () => {
    expect(isConfirmable({ status: "REFUSED", refusals: [{ code: "NETWORK_WITHOUT_POLICY", message: "x" }] })).toBe(false);
  });

  it("refuses a payload carrying a refusal even if its status says otherwise", () => {
    // The status and the list disagreeing is exactly when guessing would write something.
    expect(isConfirmable({ status: "PREVIEW", refusals: [{ code: "MISSING_TIMEOUT", message: "x" }] })).toBe(false);
  });

  it("refuses an unknown or absent status instead of assuming nothing was refused", () => {
    for (const value of [null, {}, { status: "FINE" }, { refusals: [] }]) {
      expect(isConfirmable(value as Record<string, unknown> | null)).toBe(false);
    }
  });
});

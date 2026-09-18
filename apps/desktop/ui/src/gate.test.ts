/**
 * The interface's only gate-report logic, under test.
 *
 * The rule §33 rests on — an appreciation cannot found a proof — lives in the Core and is proven
 * in `tests/test_evidence_classes.py`. What is pinned here is that the screen reads that verdict
 * without ever softening it: an unreadable class is not shown as a technical validation, and a
 * missing promotion flag is not read as "yes".
 */
import { describe, expect, it } from "vitest";

import { countByClass, readPromotion, readRequirements } from "./gate";

const report = {
  format: "vera-gate-report/v1",
  requirements: [
    { evidence_id: "e1", evidence_type: "TEST_PROOF", evidence_class: "TECHNICAL_VALIDATION", verdict: "PASS", admission: "ADMITTED", primary: true, may_create_proof: true, reason: "rejouable" },
    { evidence_id: "e2", evidence_type: "HUMAN_ASSERTION", evidence_class: "SEMANTIC_APPRECIATION", verdict: "PASS", admission: "NOT_DECIDED", primary: false, may_create_proof: false, reason: "jugement" },
  ],
  promotion: { can_satisfy_gate: false, can_create_proof: true, satisfaction_reason: "1 sur 2", proof_reason: "e1" },
};

describe("readRequirements", () => {
  it("reads each requirement the Core classified", () => {
    const [technical, semantic] = readRequirements(report);
    expect(technical).toEqual({
      evidenceId: "e1", evidenceType: "TEST_PROOF", evidenceClass: "TECHNICAL_VALIDATION",
      verdict: "PASS", admission: "ADMITTED", primary: true, mayCreateProof: true, reason: "rejouable",
    });
    expect(semantic.evidenceClass).toBe("SEMANTIC_APPRECIATION");
    expect(semantic.mayCreateProof).toBe(false);
  });

  it("never shows an unreadable class as a technical validation", () => {
    const [requirement] = readRequirements({
      requirements: [{ evidence_id: "e1", evidence_class: "PROBABLY_FINE", may_create_proof: true }],
    });
    expect(requirement.evidenceClass).toBe("UNKNOWN");
    expect(requirement.mayCreateProof).toBe(false);
  });

  it("refuses to found a proof on a class it could not read, even when the payload says it may", () => {
    // The flag and the class disagreeing is exactly when believing the flag would launder an opinion.
    const [requirement] = readRequirements({ requirements: [{ evidence_id: "e1", may_create_proof: true }] });
    expect(requirement.mayCreateProof).toBe(false);
  });

  it("returns nothing for anything that is not a gate report", () => {
    for (const value of [null, {}, { requirements: "none" }, { requirements: [{ evidence_type: "TEST_PROOF" }] }]) {
      expect(readRequirements(value as Record<string, unknown> | null)).toEqual([]);
    }
  });
});

describe("readPromotion", () => {
  it("reads both lines the Core rendered", () => {
    expect(readPromotion(report)).toEqual({
      canSatisfyGate: false, canCreateProof: true, satisfactionReason: "1 sur 2", proofReason: "e1",
    });
  });

  it("reads an absent or unreadable promotion as neither, never as yes", () => {
    for (const value of [null, {}, { promotion: "yes" }, { promotion: { can_create_proof: "true" } }]) {
      const lines = readPromotion(value as Record<string, unknown> | null);
      expect(lines.canSatisfyGate).toBe(false);
      expect(lines.canCreateProof).toBe(false);
    }
  });
});

describe("countByClass", () => {
  it("counts the three classes and what it could not read", () => {
    const counts = countByClass(readRequirements(report));
    expect(counts.TECHNICAL_VALIDATION).toBe(1);
    expect(counts.SEMANTIC_APPRECIATION).toBe(1);
    expect(counts.SIMPLE_OBSERVATION).toBe(0);
    expect(counts.UNKNOWN).toBe(0);
  });
});

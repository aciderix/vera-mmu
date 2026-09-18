/**
 * The interface's only journey-conclusion logic, under test.
 *
 * The verdict itself is computed in `vera_mmu/journey_outcome.py` and proven in
 * `tests/test_journey_outcome.py`. What is pinned here is that the screen never softens what it
 * reads: an unreadable payload concludes `FAILED`, not `COMPLETE`, and a failing check missing its
 * repair is still shown with the gap named rather than dropped.
 */
import { describe, expect, it } from "vitest";

import { readFailing, readProgress, readRemaining, readRow, readStatus, readVerdict } from "./outcome";

const complete = {
  format: "vera-journey-outcome/v1",
  status: "COMPLETE",
  verdict: "Les 18 étapes sont franchies.",
  steps: { total: 18, completed: 12, not_observable: 6, next_step: null, remaining: [] },
  validation: { status: "VALID", detail: "Surface cohérente." },
  doctor: { status: "PASS", detail: "20 contrôle(s) exécutés.", checks: 20, failing: [] },
};

const failed = {
  status: "FAILED",
  verdict: "Projet non sain.",
  steps: { total: 18, completed: 12, not_observable: 6, next_step: null, remaining: [] },
  validation: { status: "VALID", detail: "" },
  doctor: {
    status: "FAIL",
    detail: "20 contrôle(s) exécutés, 1 en échec.",
    checks: 20,
    failing: [{ name: "wal", status: "FAIL", detail: "Journal inattendu.", remediation: "Rouvrir la mémoire." }],
  },
};

describe("readStatus", () => {
  it("reads the verdict the Core rendered", () => {
    expect(readStatus(complete)).toBe("COMPLETE");
    expect(readStatus(failed)).toBe("FAILED");
  });

  it("reads anything it cannot read as FAILED, never as COMPLETE", () => {
    // An unreadable payload is a project nobody vouched for; the two must not look alike.
    for (const value of [null, {}, { status: "OK" }, { status: 4 }]) {
      expect(readStatus(value as Record<string, unknown> | null)).toBe("FAILED");
    }
  });
});

describe("readVerdict", () => {
  it("shows the Core's own sentence", () => {
    expect(readVerdict(complete)).toBe("Les 18 étapes sont franchies.");
  });

  it("says that nothing was rendered rather than inventing a sentence", () => {
    expect(readVerdict(null)).toContain("aucun verdict");
    expect(readVerdict({ verdict: "" })).toContain("aucun verdict");
  });
});

describe("readRow", () => {
  it("reads the two closing rows separately", () => {
    expect(readRow(complete, "validation").status).toBe("VALID");
    expect(readRow(complete, "doctor").status).toBe("PASS");
  });

  it("reads a missing or unreadable row as a failure", () => {
    expect(readRow({}, "doctor").status).toBe("FAIL");
    expect(readRow({ doctor: { status: "MAYBE" } }, "doctor").status).toBe("FAIL");
    expect(readRow(null, "validation").detail).not.toBe("");
  });

  it("keeps NOT_REACHED distinct from a failure", () => {
    // "Not computed yet" and "computed and failed" are different facts and must read differently.
    expect(readRow({ doctor: { status: "NOT_REACHED", detail: "Étape 4 ouverte." } }, "doctor").status).toBe("NOT_REACHED");
  });
});

describe("readFailing", () => {
  it("reads each failing check with the repair the Core named", () => {
    expect(readFailing(failed)).toEqual([
      { name: "wal", detail: "Journal inattendu.", remediation: "Rouvrir la mémoire." },
    ]);
  });

  it("shows a check whose repair is missing rather than dropping it", () => {
    const [check] = readFailing({ doctor: { failing: [{ name: "wal", detail: "x" }] } });
    expect(check.name).toBe("wal");
    expect(check.remediation).toContain("aucune réparation");
  });

  it("returns nothing when the payload carries no failures", () => {
    for (const value of [null, {}, complete, { doctor: { failing: "none" } }]) {
      expect(readFailing(value as Record<string, unknown> | null)).toEqual([]);
    }
  });
});

describe("readRemaining", () => {
  it("reads the open steps the Core listed", () => {
    const payload = { steps: { remaining: [{ id: "generate", index: 16, label: "Générer", state: "AVAILABLE", reason: "r" }] } };
    expect(readRemaining(payload)).toEqual([{ id: "generate", index: 16, label: "Générer", state: "AVAILABLE", reason: "r" }]);
  });

  it("returns nothing when nothing remains or nothing is readable", () => {
    expect(readRemaining(complete)).toEqual([]);
    expect(readRemaining(null)).toEqual([]);
  });
});

describe("readProgress", () => {
  it("reads the progress the Core counted", () => {
    expect(readProgress(complete)).toEqual({ completed: 12, total: 18 });
  });

  it("returns null rather than a fabricated ratio", () => {
    expect(readProgress(null)).toBeNull();
    expect(readProgress({ steps: { completed: "12", total: 18 } })).toBeNull();
  });
});

/**
 * The interface's only journey logic, under test.
 *
 * What is checked here is narrow on purpose: the console must read the state the Core derived and
 * never recompute it. So these tests pin the parsing, the panel mapping, and above all the two
 * refusals — a malformed payload closes nothing by inventing a state, and a journey that has not
 * been read yet closes nothing at all.
 */
import { describe, expect, it } from "vitest";

import { PANEL_STEPS, completedCount, panelAccess, readJourney, type PanelId } from "./journey";

function payload(steps: Array<Partial<{ id: string; index: number; label: string; state: string; reason: string }>>) {
  return { format: "vera-wizard-state/v1", steps };
}

describe("readJourney", () => {
  it("reads the steps the Core derived", () => {
    const steps = readJourney(payload([
      { id: "scan-project", index: 1, label: "Scanner le projet", state: "NOT_OBSERVABLE", reason: "sans trace" },
      { id: "choose-domain", index: 4, label: "Choisir le domaine", state: "AVAILABLE", reason: "aucun domaine" },
    ]));
    expect(steps).toHaveLength(2);
    expect(steps[1]).toEqual({ id: "choose-domain", index: 4, label: "Choisir le domaine", state: "AVAILABLE", reason: "aucun domaine" });
  });

  it("returns nothing for anything that is not a journey", () => {
    for (const value of [null, undefined, 42, "steps", {}, { steps: "no" }, []]) {
      expect(readJourney(value)).toEqual([]);
    }
  });

  it("drops entries without an identifier rather than inventing one", () => {
    expect(readJourney(payload([{ index: 3, state: "AVAILABLE" }, { id: "validate", index: 15, state: "NOT_OBSERVABLE" }])))
      .toHaveLength(1);
  });

  it("treats an unknown state as blocked rather than as progress", () => {
    const [step] = readJourney(payload([{ id: "generate", index: 16, state: "DEFINITELY_FINE" }]));
    expect(step.state).toBe("BLOCKED");
  });
});

describe("panelAccess", () => {
  const journey = readJourney(payload([
    { id: "scan-project", index: 1, state: "NOT_OBSERVABLE", reason: "sans trace" },
    { id: "choose-domain", index: 4, state: "COMPLETED", reason: "" },
    { id: "declare-capabilities", index: 9, state: "AVAILABLE", reason: "aucune capability" },
    { id: "build-gates", index: 10, state: "BLOCKED", reason: "Aucune capability déclarée : une gate ne peut porter sur rien." },
    { id: "generate", index: 16, state: "BLOCKED", reason: "Rien n’a encore été généré." },
    { id: "run-doctor", index: 18, state: "NOT_OBSERVABLE", reason: "sans trace" },
  ]));

  it("opens a panel whose step is not blocked", () => {
    expect(panelAccess(journey, "observe").open).toBe(true);
    expect(panelAccess(journey, "prepare").open).toBe(true);
    expect(panelAccess(journey, "capabilities").open).toBe(true);
    expect(panelAccess(journey, "verify").open).toBe(true);
  });

  it("closes a blocked panel and gives the Core's own reason", () => {
    const gates = panelAccess(journey, "gates");
    expect(gates.open).toBe(false);
    expect(gates.reason).toBe("Aucune capability déclarée : une gate ne peut porter sur rien.");
    expect(panelAccess(journey, "integrate").open).toBe(false);
  });

  it("closes nothing when the journey has not been read", () => {
    for (const panel of Object.keys(PANEL_STEPS) as PanelId[]) {
      expect(panelAccess([], panel)).toEqual({ open: true, reason: "" });
    }
  });

  it("closes nothing when the step governing a panel is absent from the payload", () => {
    const partial = readJourney(payload([{ id: "scan-project", index: 1, state: "NOT_OBSERVABLE" }]));
    expect(panelAccess(partial, "gates")).toEqual({ open: true, reason: "" });
  });

  it("maps every panel to a declared step", () => {
    for (const panel of Object.keys(PANEL_STEPS) as PanelId[]) {
      expect(PANEL_STEPS[panel]).toMatch(/^[a-z-]+$/);
    }
  });
});

describe("completedCount", () => {
  it("counts only the steps the project carries evidence for", () => {
    const steps = readJourney(payload([
      { id: "choose-domain", index: 4, state: "COMPLETED" },
      { id: "edit-taxonomy", index: 5, state: "COMPLETED" },
      { id: "scan-project", index: 1, state: "NOT_OBSERVABLE" },
      { id: "generate", index: 16, state: "AVAILABLE" },
      { id: "install", index: 17, state: "BLOCKED" },
    ]));
    expect(completedCount(steps)).toBe(2);
  });
});

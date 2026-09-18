"""The journey's conclusion: validate, diagnose, and say whether the eighteen steps landed (§29.2).

The last four steps of §29.2 — valider, générer, installer, lancer Doctor — all existed and all
worked before this module. Nothing joined them. `wizard_state` reports `next_step: None` the moment
every observable step carries its evidence and stops there; the Doctor sat in the console as one
button among six, under a heading it shared with memory synchronisation. A project could therefore
walk its whole journey, be told nothing remained, and be broken — and no screen in the product said
so. That silence is what this closes.

**The wizard cannot answer this and should not try.** It is deliberately cheap, total and derived:
it must describe a half-configured project without failing on it, so it reads the declarative files
defensively and never opens the store. The Doctor opens SQLite, imports the MCP runtime and asks Git
what it tracks. Folding one into the other would make the journey expensive at every reading and
able to fail on exactly the state it exists to report.

**What can be answered is narrower than it first looks.** Whether anyone *ran* the Doctor leaves no
trace and stays unobservable, as the wizard says. But its *verdict* is a pure function of the project
on disk: nobody needs to have pressed anything for it to be true. The same holds for `validate`. The
other four traceless steps — scanner, détecter, proposer, prévisualiser — yield no verdict the
project carries, and stay unobservable for good.

**The verdict is refused early on purpose.** While an observable step is still open, the Doctor fails
for reasons that only mean « pas encore » : no memory, no generated runtime, no host configuration.
Presenting those as failures at the end of a journey that has not ended would teach the operator to
scroll past the one check that must never be scrolled past. Both rows are then `NOT_REACHED`, naming
the step that comes first.

Nothing here is recomputed: the steps come from `wizard_state`, the declarative verdict from
`validate_project`, the health verdict from `diagnose_project`. If the Doctor itself raises — which
its own contract says it does not — this module raises with it rather than reporting a project it
could not diagnose (I014).
"""
from __future__ import annotations

from pathlib import Path

from .doctor import diagnose_project
from .project_validation import ProjectValidationError, validate_project
from .store import StoreError
from .wizard import (
    AVAILABLE,
    BLOCKED,
    COMPLETED,
    NOT_OBSERVABLE,
    PROFILE_FILE_NAME,
    RUNTIME_DIR_NAME,
    WizardError,
    WizardState,
    WizardStep,
    wizard_state,
)


JOURNEY_OUTCOME_FORMAT = "vera-journey-outcome/v1"

#: The journey is not at its end: at least one observable step is still open.
INCOMPLETE = "INCOMPLETE"
#: Every observable step is done, but step 15 refuses the declarative surface.
REFUSED = "REFUSED"
#: The surface validates, but step 18 reports a project that is not healthy.
FAILED = "FAILED"
#: Validation is `VALID` and the Doctor is `PASS`.
COMPLETE = "COMPLETE"

#: A verdict deliberately not computed, with the step that must come first.
NOT_REACHED = "NOT_REACHED"

VALIDATE_INDEX = 15
DOCTOR_INDEX = 18
#: The two states that mean a step is still the operator's to close.
OPEN_STATES = (BLOCKED, AVAILABLE)


class JourneyOutcomeError(StoreError):
    """Raised when a journey cannot be concluded for an unambiguous project root."""


def journey_outcome(root: str | Path) -> dict[str, object]:
    """Conclude the eighteen-step journey for one project root. Writes nothing."""
    try:
        state = wizard_state(root)
    except WizardError as exc:
        raise JourneyOutcomeError(f"Conclusion du parcours impossible : {exc}") from exc

    remaining = tuple(step for step in state.steps if step.state in OPEN_STATES)
    if remaining:
        first = remaining[0]
        pending = (
            f"Étape {first.index} « {first.label} » est encore ouverte ({first.state}) : {first.reason} "
            f"Un diagnostic rendu ici ne dirait que « pas encore »."
        )
        return _payload(
            state,
            remaining,
            validation={"status": NOT_REACHED, "detail": pending, "hashes": {}},
            doctor={"status": NOT_REACHED, "detail": pending, "checks": 0, "failing": []},
            status=INCOMPLETE,
            verdict=(
                f"Parcours inachevé : {len(remaining)} étape(s) ouverte(s) sur {len(state.steps)}. "
                f"La première est l’étape {first.index} « {first.label} »."
            ),
        )

    profile_path = Path(state.root) / RUNTIME_DIR_NAME / PROFILE_FILE_NAME
    try:
        validation = validate_project(profile_path)
    except ProjectValidationError as exc:
        return _payload(
            state,
            remaining,
            validation={"status": REFUSED, "detail": str(exc), "hashes": {}},
            doctor={
                "status": NOT_REACHED,
                "detail": (
                    f"Étape {VALIDATE_INDEX} « Valider » refuse le projet : diagnostiquer une surface "
                    f"déclarative incohérente nommerait des symptômes au lieu de la cause."
                ),
                "checks": 0,
                "failing": [],
            },
            status=REFUSED,
            verdict=(
                f"Le parcours ne conclut pas : l’étape {VALIDATE_INDEX} « Valider » refuse la surface "
                f"déclarative du projet."
            ),
        )

    report = diagnose_project(profile_path)
    failing = tuple(check for check in report.checks if check.status == "FAIL")
    concluded = report.status == "PASS"
    return _payload(
        state,
        remaining,
        validation={
            "status": validation.status,
            "detail": f"Surface déclarative cohérente pour {validation.project_id}.",
            "hashes": {
                "profile_hash": validation.profile_hash,
                "playbook_hash": validation.playbook_hash,
                **validation.catalog_hashes,
            },
        },
        doctor={
            "status": report.status,
            "detail": (
                f"{len(report.checks)} contrôle(s) exécutés, {len(failing)} en échec."
                if failing
                else f"{len(report.checks)} contrôle(s) exécutés, aucun en échec."
            ),
            "checks": len(report.checks),
            "failing": [check.as_dict() for check in failing],
        },
        status=COMPLETE if concluded else FAILED,
        verdict=(
            f"Les {len(state.steps)} étapes sont franchies : surface déclarative VALID et Doctor PASS."
            if concluded
            else (
                f"Parcours terminé mais projet non sain : l’étape {DOCTOR_INDEX} « Lancer Doctor » "
                f"signale {len(failing)} contrôle(s) en échec."
            )
        ),
        project_id=validation.project_id,
    )


def _payload(
    state: WizardState,
    remaining: tuple[WizardStep, ...],
    *,
    validation: dict[str, object],
    doctor: dict[str, object],
    status: str,
    verdict: str,
    project_id: str | None = None,
) -> dict[str, object]:
    """Assemble the one payload every branch returns, so no branch can omit a row."""
    return {
        "format": JOURNEY_OUTCOME_FORMAT,
        "root": state.root,
        "project_id": project_id,
        "status": status,
        "verdict": verdict,
        "steps": {
            "total": len(state.steps),
            "completed": sum(1 for step in state.steps if step.state == COMPLETED),
            "not_observable": sum(1 for step in state.steps if step.state == NOT_OBSERVABLE),
            "next_step": state.next_step,
            "remaining": [step.as_dict() for step in remaining],
        },
        "validation": validation,
        "doctor": doctor,
        "mutation": "NONE",
    }

"""Reading and configuring the Work Graph of a project (§29.2, step 8).

Two facts shape this module, and both are stated rather than smoothed over.

**The lifecycle is closed in the Core.** Four states, three events, fixed transitions. A project
does not invent its own. Letting one declare a state machine the Core does not enforce would
produce a graph that lies: the screen would offer a transition the engine refuses. So the graph is
*reported* here, from the very constants `work_lifecycle` enforces, and what a project configures
is how strict the gate on a transition is — may an item start, or complete, without being ready.

**A transition policy is declared once and never changed.** Its table holds a single row and
refuses `UPDATE` and `DELETE` by trigger. That is a deliberate guarantee — a project cannot
loosen its own rule after the fact to make an awkward item pass — and it makes the declaration
irreversible. The preview says so in as many words, because a wizard that let someone click
through an irreversible decision inside an ordinary-looking form would be hiding it.

An undeclared policy is reported `NOT_DECLARED`, never as a default. The engine treats an absent
policy as unconstrained, but saying "OPEN" where the store holds nothing would report a decision
nobody took.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from .identity import canonical_json
from .store import MemoryStore, StoreError
from .work_completion_policies import (
    WORK_COMPLETION_POLICY_MODES,
    WorkCompletionPolicyError,
    WorkCompletionPolicyService,
)
from .work_lifecycle import ALLOWED_EVENTS, STATE_BY_EVENT
from .work_start_policies import WORK_START_POLICY_MODES, WorkStartPolicyError, WorkStartPolicyService


WORK_GRAPH_FORMAT = "vera-work-graph-configuration/v1"
# The initial state of a work item before any lifecycle event is recorded.
INITIAL_STATE = "PLANNED"


class WorkGraphConfigError(StoreError):
    """Raised when a Work Graph configuration cannot be planned or applied as reviewed."""


@dataclass(frozen=True)
class WorkGraphPreview:
    """What a configuration would declare, reviewed before anything is written."""

    format: str
    start_mode: str | None
    completion_mode: str | None
    notes: tuple[str, ...]
    blockers: tuple[str, ...]
    status: str
    irreversible: bool
    preview_hash: str
    mutation: str = "NONE"

    def as_dict(self) -> dict[str, object]:
        return {
            "format": self.format,
            "start_mode": self.start_mode,
            "completion_mode": self.completion_mode,
            "notes": list(self.notes),
            "blockers": list(self.blockers),
            "status": self.status,
            "irreversible": self.irreversible,
            "preview_hash": self.preview_hash,
            "mutation": self.mutation,
        }


def read_work_graph_configuration(store: MemoryStore) -> dict[str, object]:
    """Report the Core's lifecycle and the project's declared transition policies. Writes nothing."""
    if not isinstance(store, MemoryStore):
        raise WorkGraphConfigError("Lecture du Work Graph impossible : store invalide.")
    states = sorted({INITIAL_STATE, *STATE_BY_EVENT.values()})
    transitions = sorted(
        (
            {"from": state, "event": event, "to": STATE_BY_EVENT[event]}
            for state, events in ALLOWED_EVENTS.items()
            for event in events
        ),
        key=lambda item: (item["from"], item["event"]),
    )
    enabled = _enabled(store)
    return {
        "format": WORK_GRAPH_FORMAT,
        "enabled": enabled,
        "states": states,
        "initial_state": INITIAL_STATE,
        "transitions": transitions,
        "editable": False,
        "start_policy": _policy_state(WorkStartPolicyService(store), WorkStartPolicyError, sorted(WORK_START_POLICY_MODES)),
        "completion_policy": _policy_state(
            WorkCompletionPolicyService(store), WorkCompletionPolicyError, sorted(WORK_COMPLETION_POLICY_MODES)
        ),
        "mutation": "NONE",
    }


def preview_work_graph_configuration(
    store: MemoryStore, *, start_mode: str | None = None, completion_mode: str | None = None,
) -> WorkGraphPreview:
    """Plan the declaration of one or both transition policies. Writes nothing."""
    if not isinstance(store, MemoryStore):
        raise WorkGraphConfigError("Configuration du Work Graph impossible : store invalide.")
    if start_mode is None and completion_mode is None:
        raise WorkGraphConfigError("Aucune policy nommée : rien à configurer.")
    if start_mode is not None and start_mode not in WORK_START_POLICY_MODES:
        raise WorkGraphConfigError(f"Mode de démarrage hors catalogue fermé : {start_mode}.")
    if completion_mode is not None and completion_mode not in WORK_COMPLETION_POLICY_MODES:
        raise WorkGraphConfigError(f"Mode de complétion hors catalogue fermé : {completion_mode}.")

    current = read_work_graph_configuration(store)
    blockers: list[str] = []
    notes: list[str] = [
        "Une policy de transition se déclare **une seule fois** : sa table refuse toute mise à jour "
        "et toute suppression. Cette déclaration est définitive.",
        "Le cycle de vie lui-même n’est pas configurable : ses états et ses transitions sont ceux que "
        "le Core applique, et ce rapport les reproduit sans les inventer.",
    ]
    for label, mode, key in (("démarrage", start_mode, "start_policy"), ("complétion", completion_mode, "completion_policy")):
        if mode is None:
            continue
        declared = current[key]
        if isinstance(declared, dict) and declared.get("status") == "DECLARED":
            blockers.append(
                f"La policy de {label} est déjà déclarée en `{declared.get('mode')}` : elle ne peut pas être redéclarée."
            )
    if not _enabled(store):
        notes.append(
            "Le Project Profile n’active pas le Work Graph : ces policies resteront déclarées mais sans effet "
            "tant que `work.enabled` vaut faux."
        )

    status = "REFUSED" if blockers else "PREVIEW"
    payload = {
        "format": WORK_GRAPH_FORMAT,
        "start_mode": start_mode,
        "completion_mode": completion_mode,
        "current_start": current["start_policy"],
        "current_completion": current["completion_policy"],
        "blockers": sorted(blockers),
        "status": status,
    }
    return WorkGraphPreview(
        format=WORK_GRAPH_FORMAT,
        start_mode=start_mode,
        completion_mode=completion_mode,
        notes=tuple(notes),
        blockers=tuple(sorted(blockers)),
        status=status,
        irreversible=True,
        preview_hash=sha256(canonical_json(payload).encode("utf-8")).hexdigest(),
    )


def apply_work_graph_configuration(
    store: MemoryStore, preview: WorkGraphPreview, *, confirm: bool,
) -> dict[str, object]:
    """Declare exactly the policies the reviewed preview named, once and for all."""
    if confirm is not True:
        raise WorkGraphConfigError("Configuration du Work Graph refusée sans confirmation explicite.")
    if not isinstance(preview, WorkGraphPreview):
        raise WorkGraphConfigError("Preview de configuration du Work Graph invalide.")
    if preview.status == "REFUSED":
        raise WorkGraphConfigError("Configuration refusée : " + " ".join(preview.blockers))
    current = preview_work_graph_configuration(
        store, start_mode=preview.start_mode, completion_mode=preview.completion_mode
    )
    if current.preview_hash != preview.preview_hash:
        raise WorkGraphConfigError("Preview de configuration périmé : les policies ont changé depuis sa relecture.")

    declared: dict[str, str] = {}
    try:
        if preview.start_mode is not None:
            declared["start_policy"] = WorkStartPolicyService(store).declare(preview.start_mode, actor="vera").mode
        if preview.completion_mode is not None:
            declared["completion_policy"] = WorkCompletionPolicyService(store).declare(
                preview.completion_mode, actor="vera"
            ).mode
    except (WorkStartPolicyError, WorkCompletionPolicyError) as exc:
        raise WorkGraphConfigError(f"Déclaration de policy refusée par le Core : {exc}") from exc
    return {
        "format": WORK_GRAPH_FORMAT,
        "status": "APPLIED",
        "declared": declared,
        "irreversible": True,
        "preview_hash": preview.preview_hash,
    }


def _enabled(store: MemoryStore) -> bool:
    """Read `work.enabled` from the profile the store was opened with."""
    try:
        from .identity import load_profile

        profile = load_profile(store.workspace.profile_path)
    except Exception:  # noqa: BLE001 - an unreadable profile simply declares nothing here
        return False
    section = profile.get("work")
    return bool(section.get("enabled")) if isinstance(section, dict) else False


def _policy_state(service: Any, error: type[Exception], modes: list[str]) -> dict[str, object]:
    """Report a declared policy, or the plain fact that none was declared."""
    try:
        policy = service.get()
    except error:
        return {"status": "NOT_DECLARED", "mode": None, "available_modes": modes}
    return {
        "status": "DECLARED",
        "mode": policy.mode,
        "declared_at": policy.created_at,
        "declared_by": policy.created_by,
        "available_modes": modes,
    }

"""Transport-neutral memory write primitives for VERA Core.

This module is the mutating counterpart of :mod:`vera_mmu.read_api`. It is a strict facade:
every method delegates to an existing Core service and adds no storage semantics of its own.

What a caller may never supply through this surface: a command, an interpreter, a filesystem
path, a verdict, an admission, a content hash, a resume contract hash or a `PROVEN` status.
Those are computed or refused by the Core. A client provides identifiers, declared fields and
text; the Core decides whether the write is admissible.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping

from .addressing import make_address
from .front import FrontRevision, FrontService
from .handoff import Handoff, HandoffService
from .identity import DECLARATION_ID_RE, ProfileError, load_profile
from .knowledge import Knowledge, KnowledgeService
from .profile_resume import compile_profile_resume_dossier
from .store import MemoryStore, StoreError


class WriteApiError(StoreError):
    """Raised when a generic Core mutation request is invalid or out of scope."""


def declaration_to_store_type_id(declared: str) -> str:
    """Map one profile declaration id to its canonical store type id.

    The Project Profile declares catalogs in uppercase (`PLAYER_STATE`) while the store keys
    types in lowercase (`player-state`). The mapping is total and injective over valid
    declarations, so it resolves a name without inventing one: an input that is not a valid
    declaration is refused rather than coerced (invariant I014).
    """
    if not isinstance(declared, str) or DECLARATION_ID_RE.fullmatch(declared.strip()) is None:
        raise WriteApiError("Identifiant déclaratif invalide : majuscules, chiffres et « _ » attendus.")
    return declared.strip().lower().replace("_", "-")


class WriteService:
    """Expose the bounded, audited write half of the Core over persisted resources.

    Each call opens exactly one Core transaction through the owning service, which appends its
    own audit entry. No method here batches unrelated mutations or retries a refused write.
    """

    def __init__(self, store: MemoryStore) -> None:
        if not isinstance(store, MemoryStore):
            raise WriteApiError("Store invalide pour les opérations d’écriture VERA.")
        self.store = store

    # --- knowledge -------------------------------------------------------

    def declared_knowledge_types(self) -> tuple[str, ...]:
        """Return the knowledge types this Project Profile declares, in declaration form."""
        try:
            profile = load_profile(self.store.workspace.profile_path)
        except ProfileError as exc:
            raise WriteApiError("Project Profile illisible pour le catalogue knowledge.") from exc
        declared = profile.get("knowledge", {}).get("types")
        if not isinstance(declared, list) or not declared:
            raise WriteApiError("Le Project Profile ne déclare aucun type knowledge.")
        return tuple(str(item) for item in declared)

    def sync_profile_knowledge_types(self, *, actor: str = "vera") -> list[str]:
        """Register exactly the profile-declared knowledge types, idempotently.

        Without this, a generic project has no registered type and every append is refused.
        Only types the profile declares are registered, so the catalog stays closed (I007) and
        the Core learns nothing about the domain beyond what the profile states (I015).
        """
        service = KnowledgeService(self.store)
        registered: list[str] = []
        for declared in self.declared_knowledge_types():
            store_type_id = declaration_to_store_type_id(declared)
            if self.store.connection.execute("SELECT 1 FROM knowledge_type WHERE id = ?", (store_type_id,)).fetchone() is None:
                service.register_type(store_type_id, declared, actor=actor)
            registered.append(store_type_id)
        return sorted(registered)

    def resolve_knowledge_type(self, type_id: str) -> str:
        """Resolve a client-supplied type to a profile-declared, canonical store type id."""
        store_type_id = declaration_to_store_type_id(type_id) if DECLARATION_ID_RE.fullmatch(str(type_id).strip() or " ") else str(type_id).strip()
        if store_type_id not in {declaration_to_store_type_id(item) for item in self.declared_knowledge_types()}:
            raise WriteApiError("Type knowledge absent du catalogue déclaré par le Project Profile.")
        return store_type_id

    def append_knowledge(
        self,
        identifier: str,
        *,
        type_id: str,
        status: str,
        title: str,
        content: str,
        metadata: Mapping[str, Any] | None = None,
        actor: str = "vera",
    ) -> dict[str, object]:
        """Append exactly one knowledge record; the Core refuses `PROVEN` at this stage.

        The type is resolved against the profile catalog, in declaration or canonical form, so
        a client can neither invent a type nor bypass the declared taxonomy. Promotion to
        `PROVEN` is never a side effect of an append: it requires an admissible `PASS` evidence
        through the proof surface (invariant I004).
        """
        record = KnowledgeService(self.store).append(
            identifier, self.resolve_knowledge_type(type_id), status, title, content, metadata=metadata, actor=actor,
        )
        return self._knowledge_record(record)

    # --- front -----------------------------------------------------------

    def replace_front(
        self, identifier: str, fields: Mapping[str, str], *, actor: str = "vera", confirm: bool = False,
    ) -> dict[str, object]:
        """Record one complete Front snapshot for the fields declared by this profile."""
        revision = FrontService(self.store).replace(identifier, fields, actor=actor, confirm=confirm)
        return self._front_record(revision)

    def update_front(
        self, identifier: str, fields: Mapping[str, str], *, actor: str = "vera", confirm: bool = False,
    ) -> dict[str, object]:
        """Derive a new Front snapshot by patching only declared fields on the current one."""
        revision = FrontService(self.store).update(identifier, fields, actor=actor, confirm=confirm)
        return self._front_record(revision)

    # --- handoff ---------------------------------------------------------

    def prepare_handoff(
        self, identifier: str, sections: Mapping[str, str], *, actor: str = "vera", confirm: bool = False,
    ) -> dict[str, object]:
        """Prepare one handoff from section text, compiling the resume contract server-side.

        The caller supplies section content only. The dossier, its canonical form and its
        contract hash are computed from the Project Profile, so a client can neither fabricate
        an absent resume context nor present a stale contract as current (invariant I009).
        """
        dossier = compile_profile_resume_dossier(self.store, sections)
        handoff = HandoffService(self.store).prepare(identifier, dossier, actor=actor, confirm=confirm)
        return self._handoff_record(handoff)

    # --- records ---------------------------------------------------------

    def _knowledge_record(self, record: Knowledge) -> dict[str, object]:
        payload = asdict(record)
        payload["address"] = make_address(self.store.identity.project_id, "knowledge", record.id)
        return payload

    def _front_record(self, revision: FrontRevision) -> dict[str, object]:
        payload = asdict(revision)
        payload["address"] = make_address(self.store.identity.project_id, "front", revision.id)
        return payload

    def _handoff_record(self, handoff: Handoff) -> dict[str, object]:
        payload = asdict(handoff)
        payload.pop("payload_json", None)
        payload["address"] = make_address(self.store.identity.project_id, "handoff", handoff.id)
        return payload

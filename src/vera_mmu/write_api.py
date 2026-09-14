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
import os
from typing import Any, Mapping

from .addressing import make_address
from .bundles import project_bundle_path, restore_bundle
from .capabilities import CapabilityService
from .capability_contracts import CapabilityContractService
from .capability_policies import CapabilityPolicyService
from .front import FrontRevision, FrontService
from .gates import GateService
from .handoff import Handoff, HandoffService
from .identity import DECLARATION_ID_RE, ProfileError, load_profile
from .knowledge import Knowledge, KnowledgeService
from .profile_resume import compile_profile_resume_dossier
from .project_catalogs import ProjectCatalogError, load_project_catalogs
from .proof_policies import ProofPolicyService
from .proofs import KnowledgeProof, ProofService
from .store import MemoryStore, StoreError
from .validators import ValidatorService
from .work_items import WorkItem, WorkItemService
from .work_lifecycle import WorkLifecycleEvent, WorkLifecycleService


PROOF_HMAC_SECRET_VARIABLE = "VERA_MMU_PROOF_HMAC_SECRET"


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

    # --- declared capability catalog -------------------------------------

    def sync_profile_capabilities(self, *, actor: str = "vera") -> list[str]:
        """Materialize the profile-declared capability catalog into the store, idempotently.

        The catalog file was validated and hashed but never written to SQLite, so a freshly
        initialized project had no `ALLOW` capability and generation refused it. Each declared
        capability becomes exactly one capability, one contract and one policy decision:
        `CONFIRM` when the declaration requires confirmation, `ALLOW` otherwise. Nothing outside
        the declared catalog is ever registered, so the runtime stays closed (I007, I015).
        """
        try:
            catalogs = load_project_catalogs(self.store.workspace.profile_path)
        except ProjectCatalogError as exc:
            raise WriteApiError("Catalogues du Project Profile invalides ou absents.") from exc
        capabilities = CapabilityService(self.store)
        contracts = CapabilityContractService(self.store)
        policies = CapabilityPolicyService(self.store)
        validators = ValidatorService(self.store)
        registered: list[str] = []
        for declaration in catalogs.capabilities["capabilities"]:
            identifier = str(declaration["id"])
            schema = dict(declaration["parameter_schema"])
            if self.store.connection.execute("SELECT 1 FROM capability WHERE id = ?", (identifier,)).fetchone() is None:
                capabilities.create(
                    identifier, str(declaration["name"]), str(declaration["kind"]), str(declaration["version"]),
                    description=str(declaration["description"]), parameter_schema=schema, actor=actor,
                )
            if self.store.connection.execute("SELECT 1 FROM capability_contract WHERE capability_id = ?", (identifier,)).fetchone() is None:
                contracts.declare(
                    identifier, str(declaration["runner"]), str(declaration["network_policy"]),
                    int(declaration["timeout_seconds"]), parameter_schema=schema,
                    yields_proof=bool(declaration["yields_proof"]), actor=actor,
                )
            if self.store.connection.execute("SELECT 1 FROM capability_policy WHERE capability_id = ?", (identifier,)).fetchone() is None:
                decision = "CONFIRM" if bool(declaration["confirmation_required"]) else "ALLOW"
                policies.declare(identifier, decision, f"Déclarée {declaration['policy']} par le Project Profile.", actor=actor)
            registered.append(identifier)
        self._register_declared_validators(validators, catalogs.capabilities["capabilities"], actor=actor)
        return sorted(registered)

    def _register_declared_validators(self, validators: ValidatorService, declarations: list[Any], *, actor: str) -> None:
        """Register one validator per declared kind, which is all the store admits.

        The runner takes only `validator_id` and `evidence_id`; the domain fields a project must
        evidence live on the validator as its required keys, declared by each capability's
        `inputs`. Without this a declared capability passes generation and fails at execution.

        `validator.kind` is UNIQUE, so a store holds at most one validator per kind. When
        several capabilities share `EVIDENCE_FIELDS` their required keys are unioned, which
        means evidence must then carry every declared field; a project needing narrower rules
        should declare fewer field-validated capabilities.
        """
        by_kind: dict[str, set[str]] = {}
        for declaration in declarations:
            kind = str(declaration["validator"])
            fields = by_kind.setdefault(kind, set())
            if kind == "EVIDENCE_FIELDS":
                fields.update(str(name) for name in declaration["inputs"])
        for kind, fields in sorted(by_kind.items()):
            if self.store.connection.execute("SELECT 1 FROM validator WHERE kind = ?", (kind,)).fetchone() is not None:
                continue
            validators.register(
                f"vera-{kind.lower().replace('_', '-')}", kind,
                required_keys=tuple(sorted(fields)) if kind == "EVIDENCE_FIELDS" else None, actor=actor,
            )

    # --- work graph ------------------------------------------------------

    def create_work_item(
        self,
        identifier: str,
        *,
        item_type: str,
        title: str,
        description: str = "",
        priority: int | None = None,
        parent_id: str | None = None,
        assignee: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        actor: str = "vera",
    ) -> dict[str, object]:
        """Create one work item in the initial lifecycle state declared by the Core."""
        item = WorkItemService(self.store).create(
            identifier, item_type, title, description=description, priority=priority,
            parent_id=parent_id, assignee=assignee, metadata=metadata, actor=actor,
        )
        return self._work_item_record(item)

    def transition_work_item(
        self, identifier: str, *, work_item_id: str, event: str, reason: str, actor: str = "vera",
    ) -> dict[str, object]:
        """Apply one lifecycle event from the closed Core catalog.

        A client names an event, never a target state: the Core derives the state and refuses a
        transition its start/completion policies do not allow (invariant I007).
        """
        transition = WorkLifecycleService(self.store).transition(identifier, work_item_id, event, reason, actor=actor)
        return self._lifecycle_record(transition)

    def add_work_dependency(self, dependent_id: str, prerequisite_id: str, *, actor: str = "vera") -> dict[str, object]:
        """Declare one prerequisite edge; the Core refuses self-edges and cycles."""
        GateService(self.store).add_dependency(dependent_id, prerequisite_id, actor=actor)
        return {"dependent_id": dependent_id, "prerequisite_id": prerequisite_id, "status": "DECLARED"}

    def declare_gate(
        self,
        identifier: str,
        *,
        work_item_id: str,
        evidence_id: str,
        requirement_evidence_ids: tuple[str, ...] | list[str] | None = None,
        actor: str = "vera",
    ) -> dict[str, object]:
        """Declare one admission gate binding a work item to the evidence it requires."""
        service = GateService(self.store)
        requirements = tuple(requirement_evidence_ids or ())
        if requirements:
            service.declare_with_requirements(identifier, work_item_id, evidence_id, requirements, actor=actor)
        else:
            service.declare(identifier, work_item_id, evidence_id, actor=actor)
        return {
            "gate_id": identifier,
            "work_item_id": work_item_id,
            "evidence_id": evidence_id,
            "requirement_evidence_ids": list(requirements),
            "status": "DECLARED",
        }

    # --- proof -----------------------------------------------------------

    def declare_proof_policy(self, algorithm: str, *, hmac_required: bool, actor: str = "vera") -> dict[str, object]:
        """Declare the project's proof policy once; promotion is refused without it."""
        policy = ProofPolicyService(self.store).declare(algorithm, hmac_required=hmac_required, actor=actor)
        return asdict(policy)

    def promote_knowledge(
        self, identifier: str, *, knowledge_id: str, evidence_id: str, admission_id: str, actor: str = "vera",
    ) -> dict[str, object]:
        """Promote one knowledge record to `PROVEN` against an admitted `PASS` evidence.

        This is invariant I004 at its narrowest point. The caller names existing records only:
        it supplies no verdict, no admission decision and no signature. When the declared policy
        requires HMAC the secret is read from the environment, never from the caller, and its
        absence is a loud refusal rather than an unsigned promotion (I014). The secret is kept
        out of the project runtime because memory sync commits that directory to Git.
        """
        policy = ProofPolicyService(self.store).get()
        secret: bytes | None = None
        if policy.hmac_required:
            raw = os.environ.get(PROOF_HMAC_SECRET_VARIABLE, "")
            if not raw:
                raise WriteApiError(
                    f"La policy de preuve exige HMAC : définir {PROOF_HMAC_SECRET_VARIABLE} hors du dépôt avant promotion.",
                )
            secret = raw.encode("utf-8")
        proof = ProofService(self.store, hmac_secret=secret).promote(
            identifier, knowledge_id, evidence_id, admission_id, actor=actor,
        )
        return self._proof_record(proof)

    def attach_proof(self, gate_id: str, *, evidence_id: str, actor: str = "vera") -> dict[str, object]:
        """Attach one existing evidence to a declared gate as an additional requirement.

        The caller names records only: it supplies no verdict and no admission. The Core refuses
        an unknown gate or evidence, so attaching never creates the material it points at.
        """
        GateService(self.store).add_requirement(gate_id, evidence_id, actor=actor)
        return {"gate_id": gate_id, "evidence_id": evidence_id, "status": "ATTACHED"}

    # --- bundles ---------------------------------------------------------

    def restore_bundle_by_id(self, bundle_id: str, *, confirm: bool = False) -> dict[str, object]:
        """Restore one of this project's own bundles after explicit confirmation.

        The bundle is named, never pathed. The Core verifies the manifest chain and the project
        identity, and refuses to merge into a non-empty divergent memory: a restore either finds
        its own untouched snapshot, installs into an empty runtime, or is refused (I010, I011).
        """
        source = project_bundle_path(self.store, bundle_id)
        result = restore_bundle(source, self.store.workspace.profile_path, confirm=confirm)
        payload = asdict(result)
        payload.pop("path", None)
        return payload

    # --- records ---------------------------------------------------------

    def _knowledge_record(self, record: Knowledge) -> dict[str, object]:
        payload = asdict(record)
        payload["address"] = make_address(self.store.identity.project_id, "knowledge", record.id)
        return payload

    def _front_record(self, revision: FrontRevision) -> dict[str, object]:
        payload = asdict(revision)
        payload["address"] = make_address(self.store.identity.project_id, "front", revision.id)
        return payload

    def _work_item_record(self, item: WorkItem) -> dict[str, object]:
        payload = asdict(item)
        payload["address"] = make_address(self.store.identity.project_id, "work-item", item.id)
        return payload

    def _lifecycle_record(self, transition: WorkLifecycleEvent) -> dict[str, object]:
        return asdict(transition)

    def _proof_record(self, proof: KnowledgeProof) -> dict[str, object]:
        payload = asdict(proof)
        payload["address"] = make_address(self.store.identity.project_id, "proof", proof.id)
        return payload

    def _handoff_record(self, handoff: Handoff) -> dict[str, object]:
        payload = asdict(handoff)
        payload.pop("payload_json", None)
        payload["address"] = make_address(self.store.identity.project_id, "handoff", handoff.id)
        return payload

"""Transport-neutral boot, FIND and exact READ primitives for VERA Core."""
from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import json
from typing import Iterable

from .addressing import AddressError, make_address, parse_compat_address
from .bundles import BundleError, inspect_bundle, project_bundle_path
from .capabilities import CapabilityService
from .entities import EntityService
from .evidence import EvidenceService
from .executions import ExecutionService
from .front import FrontRevision, FrontService
from .identity import ProfileError, canonical_json, load_profile
from .handoff import Handoff, HandoffService
from .knowledge import KnowledgeService
from .profile_resume import ProfileResumeError, profile_resume_requirements
from .project_catalogs import ProjectCatalogError, load_project_catalogs
from .relations import RelationService
from .session_lifecycle import LifecycleError, ResumeGuardService
from .store import MemoryStore, StoreError
from .symbols import SymbolService
from .vcs import inspect_vcs
from .work_items import WorkItemService
from .work_lifecycle import STATE_BY_EVENT as WORK_ITEM_STATE_BY_EVENT


FINDABLE_RESOURCE_TYPES = frozenset({"knowledge", "entity", "work-item"})
READABLE_RESOURCE_TYPES = FINDABLE_RESOURCE_TYPES | frozenset({"front", "handoff", "relation", "capability", "execution", "evidence", "symbol", "proof"})
MAX_FIND_QUERY_CHARACTERS = 256
MAX_FIND_RESULTS = 100
MAX_READ_BATCH = 32
MAX_EXECUTION_HISTORY = 100
MAX_WORK_GRAPH_ITEMS = 500
_EXPORT_COUNTED_TABLES = ("knowledge", "entity", "relation", "work_item", "capability", "execution", "evidence", "knowledge_proof")


class ReadApiError(StoreError):
    """Raised when a generic Core retrieval request is invalid or out of scope."""


class ReadService:
    """Expose a bounded discovery/read split over generic, persisted Core resources.

    FIND returns only compact references. READ requires one canonical `vera://` address and
    returns exactly that verified record. Neither operation opens a transaction nor invokes
    any mutating service.
    """

    def __init__(self, store: MemoryStore) -> None:
        if not isinstance(store, MemoryStore):
            raise ReadApiError("Store invalide pour les opérations de lecture VERA.")
        self.store = store

    def vcs_status(self) -> dict[str, str]:
        """Return minimal local VCS observation without paths, commands or mutations."""
        return inspect_vcs(self.store).as_dict()

    def resume_brief(self) -> dict[str, object]:
        """State what a resume must contain, before anything is armed or acknowledged.

        The brief is derived from the Project Profile, never from a client: it names the exact
        sections the resume contract requires, their byte bounds, and the pointers an agent
        needs to rebuild context. Reading it never arms a guard and never acknowledges one.
        """
        try:
            requirements = profile_resume_requirements(self.store)
            budget = int(load_profile(self.store.workspace.profile_path)["storage"].get("max_resume_bytes", 0))
        except (ProfileResumeError, ProfileError, KeyError, TypeError, ValueError) as exc:
            raise ReadApiError("Contrat de reprise du Project Profile illisible.") from exc
        front = FrontService(self.store).current()
        handoff = HandoffService(self.store).latest()
        return {
            "format": "vera-resume-brief/v1",
            "project_identity": self.store.identity.as_dict(),
            "max_resume_bytes": budget,
            "required_sections": [
                {"id": item.identifier, "minimum_characters": item.minimum_characters, "maximum_characters": item.maximum_characters}
                for item in requirements
            ],
            "current_front": None if front is None else {
                "address": front_address(self.store.identity.project_id, front.id),
                "id": front.id,
                "fields_hash": front.fields_hash,
            },
            "latest_handoff": None if handoff is None else {
                "address": make_address(self.store.identity.project_id, "handoff", handoff.id),
                "id": handoff.id,
                "resume_contract_hash": handoff.resume_contract_hash,
            },
        }

    def resume_status(self, session_identity: str, adapter_id: str) -> dict[str, object]:
        """Report whether a resume contract is armed for this host session.

        The session identity is supplied by the attested adapter, never by a client, and the
        derived session state key is deliberately not returned: it identifies the host session
        and reading a status is not a reason to expose it.
        """
        service = ResumeGuardService(self.store)
        try:
            state = service.read_state(session_identity, adapter_id)
        except LifecycleError as exc:
            raise ReadApiError("État de reprise illisible ou étranger au projet.") from exc
        if state is None:
            return {
                "format": "vera-resume-status/v1",
                "project_identity": self.store.identity.as_dict(),
                "status": "NOT_ARMED",
                "reason": None,
                "mode": None,
                "resume_contract_hash": None,
                "armed_at": None,
                "acknowledged_at": None,
            }
        return {
            "format": "vera-resume-status/v1",
            "project_identity": self.store.identity.as_dict(),
            "status": state.status,
            "reason": state.reason,
            "mode": state.mode,
            "resume_contract_hash": state.resume_contract_hash,
            "armed_at": state.armed_at,
            "acknowledged_at": state.acknowledged_at,
        }

    def export_projection(self) -> dict[str, object]:
        """Describe the project's verifiable state without producing an archive.

        `export_bundle` writes a full `.zip`; this is the light counterpart: identity, schema
        and catalog hashes plus resource counts, enough to compare two projects or check a
        bundle's provenance without unpacking one. It is derived and writes nothing.
        """
        try:
            catalogs = load_project_catalogs(self.store.workspace.profile_path)
        except (ProjectCatalogError, OSError, ValueError) as exc:
            raise ReadApiError("Catalogues du Project Profile illisibles pour l’export.") from exc
        counts = {
            table: int(self.store.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in _EXPORT_COUNTED_TABLES
        }
        migrations = canonical_json({str(version): value for version, value in self.store.migration_checksums.items()})
        return {
            "format": "vera-export-projection/v1",
            "project_identity": self.store.identity.as_dict(),
            "schema_version": max(self.store.migration_checksums, default=0),
            "schema_hash": sha256(migrations.encode("utf-8")).hexdigest(),
            "catalog_hashes": {
                "capabilities": catalogs.capability_catalog_hash,
                "gates": catalogs.gate_catalog_hash,
                "policies": catalogs.policy_hash,
            },
            "counts": counts,
        }

    def preview_bundle_import(self, bundle_id: str) -> dict[str, object]:
        """Verify one bundle of this project and report what restoring it would do.

        The bundle is named, never pathed: the identifier is resolved inside the project's own
        bundles directory, so no client input reaches the filesystem. Nothing is written, and a
        manifest that does not belong to this project identity is refused (I010, I011).
        """
        try:
            manifest = inspect_bundle(project_bundle_path(self.store, bundle_id))
        except BundleError as exc:
            raise ReadApiError("Bundle project-local introuvable, illisible ou altéré.") from exc
        if manifest.get("project_identity") != self.store.identity.as_dict():
            raise ReadApiError("Bundle lié à une autre identité de projet.")
        database = self.store.locator.sqlite_path
        return {
            "format": "vera-bundle-import-preview/v1",
            "bundle_id": str(manifest["bundle_id"]),
            "project_identity": dict(manifest["project_identity"]),
            "memory_hash": str(manifest["memory_hash"]),
            "schema_hash": str(manifest["schema_hash"]),
            "artifact_count": len(manifest["artifact_inventory"]),
            "target_state": "OCCUPIED" if database.exists() else "EMPTY",
            "mutation": "NONE",
        }

    def work_graph(self) -> dict[str, object]:
        """Return the bounded work graph: items, their lifecycle state and declared edges.

        This is a projection, not a FIND: it returns structure and status, never descriptions
        or knowledge content. The traversal is capped so a large project cannot flood a client.
        """
        items = [
            {
                "id": str(row["id"]),
                "address": make_address(self.store.identity.project_id, "work-item", str(row["id"])),
                "type": str(row["type"]),
                "title": str(row["title"]),
                "status": WORK_ITEM_STATE_BY_EVENT.get(str(row["last_event"]), str(row["status"])),
                "priority": row["priority"],
                "parent_id": None if row["parent_id"] is None else str(row["parent_id"]),
            }
            for row in self.store.connection.execute(
                # The lifecycle state is derived from the append-only event log, not from the
                # creation status column, which keeps its initial value for the item's life.
                "SELECT item.id, item.type, item.title, item.status, item.priority, item.parent_id, "
                "(SELECT event FROM work_lifecycle_event AS lifecycle WHERE lifecycle.work_item_id = item.id "
                " ORDER BY lifecycle.sequence DESC LIMIT 1) AS last_event "
                "FROM work_item AS item ORDER BY item.id LIMIT ?",
                (MAX_WORK_GRAPH_ITEMS,),
            ).fetchall()
        ]
        dependencies = [
            {"dependent_id": str(row["dependent_id"]), "prerequisite_id": str(row["prerequisite_id"])}
            for row in self.store.connection.execute(
                "SELECT dependent_id, prerequisite_id FROM work_dependency ORDER BY dependent_id, prerequisite_id LIMIT ?",
                (MAX_WORK_GRAPH_ITEMS,),
            ).fetchall()
        ]
        gates = [
            {"gate_id": str(row["id"]), "work_item_id": str(row["work_item_id"]), "evidence_id": str(row["evidence_id"])}
            for row in self.store.connection.execute(
                "SELECT id, work_item_id, evidence_id FROM admission_gate ORDER BY id LIMIT ?",
                (MAX_WORK_GRAPH_ITEMS,),
            ).fetchall()
        ]
        return {
            "format": "vera-work-graph/v1",
            "project_identity": self.store.identity.as_dict(),
            "items": items,
            "dependencies": dependencies,
            "gates": gates,
        }

    def list_proofs(self, *, max_items: int = 20) -> dict[str, object]:
        """List persisted promotions compactly; the signature itself is never returned."""
        if not isinstance(max_items, int) or isinstance(max_items, bool) or not 1 <= max_items <= MAX_EXECUTION_HISTORY:
            raise ReadApiError(f"max_items doit être un entier entre 1 et {MAX_EXECUTION_HISTORY}.")
        proofs = [
            {
                "id": str(row["id"]),
                "address": make_address(self.store.identity.project_id, "proof", str(row["id"])),
                "knowledge_id": str(row["knowledge_id"]),
                "evidence_id": str(row["evidence_id"]),
                "admission_id": str(row["admission_id"]),
                "status": str(row["status"]),
                "created_at": str(row["created_at"]),
            }
            for row in self.store.connection.execute(
                "SELECT id, knowledge_id, evidence_id, admission_id, status, created_at "
                "FROM knowledge_proof ORDER BY created_at DESC, id DESC LIMIT ?",
                (max_items,),
            ).fetchall()
        ]
        return {"format": "vera-proof-history/v1", "proofs": proofs}

    def boot(self) -> dict[str, object]:
        """Return project-bound startup state without arming, acknowledging or mutating resume."""
        front = FrontService(self.store).current()
        handoff = HandoffService(self.store).latest()
        return {
            "format": "vera-boot/v1",
            "project_identity": self.store.identity.as_dict(),
            "current_front": None if front is None else {
                "address": front_address(self.store.identity.project_id, front.id),
                "id": front.id,
                "fields_hash": front.fields_hash,
                "created_at": front.created_at,
            },
            "latest_handoff": None if handoff is None else {
                "address": make_address(self.store.identity.project_id, "handoff", handoff.id),
                "id": handoff.id,
                "front_revision_id": handoff.front_revision_id,
                "payload_hash": handoff.payload_hash,
                "resume_contract_hash": handoff.resume_contract_hash,
                "created_at": handoff.created_at,
            },
            "resume_status": "NOT_ARMED",
        }

    def current_front(self) -> dict[str, object]:
        """Read the current immutable Front snapshot without accepting a client-selected id."""
        front = FrontService(self.store).current()
        if front is None:
            raise ReadApiError("Aucun Front courant VERA à lire.")
        return {
            "address": front_address(self.store.identity.project_id, front.id),
            "resource_type": "front",
            "record": _front_record(front),
        }

    def latest_handoff(self) -> dict[str, object]:
        """Read the latest verified handoff without accepting a client-selected id."""
        handoff = HandoffService(self.store).latest()
        if handoff is None:
            raise ReadApiError("Aucun handoff VERA courant à lire.")
        return {
            "address": make_address(self.store.identity.project_id, "handoff", handoff.id),
            "resource_type": "handoff",
            "record": _handoff_record(handoff),
        }

    def find(self, query: str, *, resource_types: Iterable[str] | None = None) -> list[dict[str, object]]:
        """Discover matching titles only; content and descriptions remain exclusive to READ."""
        needle = _query(query)
        resources = _resource_types(resource_types)
        escaped = _like_escape(needle)
        pattern = f"%{escaped}%"
        findings: list[dict[str, object]] = []
        if "knowledge" in resources:
            findings.extend(
                {
                    "address": make_address(self.store.identity.project_id, "knowledge", str(row["id"])),
                    "resource_type": "knowledge",
                    "id": str(row["id"]),
                    "title": str(row["title"]),
                    "status": str(row["status"]),
                    "type_id": str(row["type_id"]),
                }
                for row in self.store.connection.execute(
                    "SELECT id, title, status, type_id FROM knowledge WHERE title LIKE ? ESCAPE '\\' COLLATE NOCASE",
                    (pattern,),
                ).fetchall()
            )
        if "entity" in resources:
            findings.extend(
                {
                    "address": make_address(self.store.identity.project_id, "entity", str(row["id"])),
                    "resource_type": "entity",
                    "id": str(row["id"]),
                    "title": str(row["title"]),
                    "type_id": str(row["type_id"]),
                }
                for row in self.store.connection.execute(
                    "SELECT id, title, type_id FROM entity WHERE title LIKE ? ESCAPE '\\' COLLATE NOCASE",
                    (pattern,),
                ).fetchall()
            )
        if "work-item" in resources:
            findings.extend(
                {
                    "address": make_address(self.store.identity.project_id, "work-item", str(row["id"])),
                    "resource_type": "work-item",
                    "id": str(row["id"]),
                    "title": str(row["title"]),
                    "status": str(row["status"]),
                    "type": str(row["type"]),
                }
                for row in self.store.connection.execute(
                    "SELECT id, title, status, type FROM work_item WHERE title LIKE ? ESCAPE '\\' COLLATE NOCASE",
                    (pattern,),
                ).fetchall()
            )
        findings.sort(key=lambda item: (str(item["resource_type"]), str(item["id"])))
        return findings[:MAX_FIND_RESULTS]

    def related(self, address: str, *, direction: str = "BOTH", max_depth: int = 1, max_nodes: int = 20) -> dict[str, object]:
        """Traverse bounded entity relations breadth-first without exposing arbitrary graph queries."""
        try:
            root = parse_compat_address(address)
        except AddressError as exc:
            raise ReadApiError("Adresse related VERA invalide ou non canonique.") from exc
        if root.project_id != self.store.identity.project_id or root.resource_type != "entity":
            raise ReadApiError("La racine related doit être une entité VERA du projet courant.")
        if direction not in {"INBOUND", "OUTBOUND", "BOTH"}:
            raise ReadApiError("Direction related inconnue ou non autorisée.")
        if isinstance(max_depth, bool) or not isinstance(max_depth, int) or not 1 <= max_depth <= 3:
            raise ReadApiError("Profondeur related invalide : 1 à 3 requise.")
        if isinstance(max_nodes, bool) or not isinstance(max_nodes, int) or not 1 <= max_nodes <= 50:
            raise ReadApiError("Cardinalité related invalide : 1 à 50 requise.")
        try:
            EntityService(self.store).get(root.identifier)
            seen = {root.identifier}
            frontier = [(root.identifier, 0)]
            nodes: list[dict[str, object]] = []
            relations: list[dict[str, object]] = []
            relation_ids: set[str] = set()
            service = RelationService(self.store)
            while frontier and len(nodes) < max_nodes:
                entity_id, depth = frontier.pop(0)
                if depth >= max_depth:
                    continue
                clauses: list[str] = []
                parameters: list[str] = []
                if direction in {"OUTBOUND", "BOTH"}:
                    clauses.append("from_entity_id = ?")
                    parameters.append(entity_id)
                if direction in {"INBOUND", "BOTH"}:
                    clauses.append("to_entity_id = ?")
                    parameters.append(entity_id)
                rows = self.store.connection.execute(
                    "SELECT id FROM relation WHERE " + " OR ".join(clauses) + " ORDER BY id ASC", parameters
                ).fetchall()
                for row in rows:
                    relation = service.get(str(row[0]))
                    neighbor = relation.to_entity_id if relation.from_entity_id == entity_id else relation.from_entity_id
                    if neighbor not in seen:
                        if len(nodes) >= max_nodes:
                            continue
                        seen.add(neighbor)
                        entity = EntityService(self.store).get(neighbor)
                        nodes.append({"address": make_address(self.store.identity.project_id, "entity", entity.id), "id": entity.id, "type_id": entity.type_id, "title": entity.title})
                        frontier.append((neighbor, depth + 1))
                    if relation.id not in relation_ids:
                        relation_ids.add(relation.id)
                        relations.append({"id": relation.id, "type_id": relation.relation_type_id, "from_address": relation.from_address, "to_address": relation.to_address})
        except StoreError as exc:
            raise ReadApiError("Graphe relationnel VERA introuvable ou incohérent.") from exc
        return {"root_address": root.canonical, "direction": direction, "max_depth": max_depth, "max_nodes": max_nodes, "nodes": nodes, "relations": relations}

    def execution_history(self, *, max_items: int = 20) -> dict[str, object]:
        """List a small deterministic projection of persisted executions without their payloads."""
        if isinstance(max_items, bool) or not isinstance(max_items, int) or not 1 <= max_items <= MAX_EXECUTION_HISTORY:
            raise ReadApiError(f"Historique execution invalide : 1 à {MAX_EXECUTION_HISTORY} éléments requis.")
        rows = self.store.connection.execute(
            "SELECT id, capability_id, status, started_at, finished_at, artifact_hash "
            "FROM execution ORDER BY started_at DESC, id DESC LIMIT ?",
            (max_items,),
        ).fetchall()
        return {
            "max_items": max_items,
            "executions": [
                {
                    "address": make_address(self.store.identity.project_id, "execution", str(row["id"])),
                    "id": str(row["id"]),
                    "capability_id": str(row["capability_id"]),
                    "status": str(row["status"]),
                    "started_at": None if row["started_at"] is None else str(row["started_at"]),
                    "finished_at": None if row["finished_at"] is None else str(row["finished_at"]),
                    "artifact_hash": None if row["artifact_hash"] is None else str(row["artifact_hash"]),
                }
                for row in rows
            ],
        }

    def evidence_history(self, *, max_items: int = 20) -> dict[str, object]:
        """List a small deterministic evidence projection without content or actor disclosure."""
        if isinstance(max_items, bool) or not isinstance(max_items, int) or not 1 <= max_items <= MAX_EXECUTION_HISTORY:
            raise ReadApiError(f"Historique evidence invalide : 1 à {MAX_EXECUTION_HISTORY} éléments requis.")
        rows = self.store.connection.execute(
            "SELECT id, execution_id, evidence_type, verdict, content_hash, admission_status, created_at "
            "FROM evidence ORDER BY created_at DESC, id DESC LIMIT ?",
            (max_items,),
        ).fetchall()
        return {
            "max_items": max_items,
            "evidence": [
                {
                    "address": make_address(self.store.identity.project_id, "evidence", str(row["id"])),
                    "id": str(row["id"]),
                    "execution_id": str(row["execution_id"]),
                    "evidence_type": str(row["evidence_type"]),
                    "verdict": str(row["verdict"]),
                    "content_hash": str(row["content_hash"]),
                    "admission_status": str(row["admission_status"]),
                    "created_at": str(row["created_at"]),
                }
                for row in rows
            ],
        }

    def read(self, address: str) -> dict[str, object]:
        """Read one exact resource after validating its canonical address and project identity."""
        try:
            parsed = parse_compat_address(address)
        except AddressError as exc:
            raise ReadApiError("Adresse READ VERA invalide ou non canonique.") from exc
        if parsed.project_id != self.store.identity.project_id:
            raise ReadApiError("Adresse READ liée à une autre identité de projet.")
        try:
            if parsed.resource_type == "knowledge":
                record = asdict(KnowledgeService(self.store).get(parsed.identifier))
            elif parsed.resource_type == "entity":
                record = asdict(EntityService(self.store).get(parsed.identifier))
            elif parsed.resource_type == "work-item":
                record = asdict(WorkItemService(self.store).get(parsed.identifier))
            elif parsed.resource_type == "front":
                record = _front_record(FrontService(self.store).get(parsed.identifier))
            elif parsed.resource_type == "handoff":
                record = _handoff_record(HandoffService(self.store).get(parsed.identifier))
            elif parsed.resource_type == "relation":
                record = asdict(RelationService(self.store).get(parsed.identifier))
            elif parsed.resource_type == "capability":
                record = asdict(CapabilityService(self.store).get(parsed.identifier))
            elif parsed.resource_type == "execution":
                record = asdict(ExecutionService(self.store).get(parsed.identifier))
            elif parsed.resource_type == "evidence":
                record = asdict(EvidenceService(self.store).get(parsed.identifier))
            elif parsed.resource_type == "symbol":
                record = asdict(SymbolService(self.store).get(parsed.identifier))
            elif parsed.resource_type == "proof":
                record = self._proof(parsed.identifier)
            else:
                raise ReadApiError("Type de ressource READ non exposé dans le contrat fermé M11-J.")
        except ReadApiError:
            raise
        except StoreError as exc:
            raise ReadApiError("Ressource VERA exacte introuvable ou incohérente.") from exc
        return {"address": parsed.canonical, "resource_type": parsed.resource_type, "record": record}

    def _proof(self, identifier: str) -> dict[str, object]:
        """Read one promotion record without ever returning its HMAC digest.

        The digest is derived from the project secret. Reporting whether a proof is signed is
        enough to audit the policy; returning the digest itself would hand a verifier an
        offline oracle against that secret.
        """
        row = self.store.connection.execute(
            "SELECT id, knowledge_id, evidence_id, admission_id, status, hmac_required, hmac_digest, created_at, created_by "
            "FROM knowledge_proof WHERE id = ?",
            (identifier,),
        ).fetchone()
        if row is None:
            raise ReadApiError("Preuve VERA exacte introuvable.")
        return {
            "id": str(row["id"]),
            "knowledge_id": str(row["knowledge_id"]),
            "evidence_id": str(row["evidence_id"]),
            "admission_id": str(row["admission_id"]),
            "status": str(row["status"]),
            "hmac_required": bool(row["hmac_required"]),
            "signed": row["hmac_digest"] is not None,
            "created_at": str(row["created_at"]),
            "created_by": str(row["created_by"]),
        }

    def read_batch(self, addresses: Iterable[str]) -> list[dict[str, object]]:
        """Read a small explicit batch, preserving caller order and exact-address semantics."""
        if isinstance(addresses, (str, bytes)):
            raise ReadApiError("Le batch READ doit être une liste d’adresses VERA.")
        values = list(addresses)
        if not 1 <= len(values) <= MAX_READ_BATCH or not all(isinstance(address, str) for address in values):
            raise ReadApiError(f"Le batch READ doit contenir entre 1 et {MAX_READ_BATCH} adresses VERA.")
        return [self.read(address) for address in values]


def front_address(project_id: str, identifier: str) -> str:
    """Keep the Front reference an exact VERA address without exposing a path."""
    return make_address(project_id, "front", identifier)


def _front_record(front: FrontRevision) -> dict[str, object]:
    return asdict(front)


def _handoff_record(handoff: Handoff) -> dict[str, object]:
    record = asdict(handoff)
    payload_json = record.pop("payload_json")
    try:
        record["payload"] = json.loads(str(payload_json))
    except (TypeError, json.JSONDecodeError) as exc:
        raise ReadApiError("Handoff persistant illisible ou altéré.") from exc
    return record


def _query(value: str) -> str:
    if not isinstance(value, str) or value != value.strip() or "\x00" in value or not 2 <= len(value) <= MAX_FIND_QUERY_CHARACTERS:
        raise ReadApiError(f"La requête FIND doit contenir entre 2 et {MAX_FIND_QUERY_CHARACTERS} caractères canoniques.")
    return value


def _resource_types(value: Iterable[str] | None) -> frozenset[str]:
    if value is None:
        return FINDABLE_RESOURCE_TYPES
    if isinstance(value, (str, bytes)):
        raise ReadApiError("resource_types FIND doit être une liste de types de ressources.")
    values = list(value)
    if not values or len(values) > len(FINDABLE_RESOURCE_TYPES) or any(not isinstance(item, str) for item in values):
        raise ReadApiError("resource_types FIND invalide.")
    resources = frozenset(values)
    if not resources.issubset(FINDABLE_RESOURCE_TYPES):
        raise ReadApiError("resource_types FIND contient une ressource non exposée.")
    return resources


def _like_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

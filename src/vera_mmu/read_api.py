"""Transport-neutral boot, FIND and exact READ primitives for VERA Core."""
from __future__ import annotations

from dataclasses import asdict
import json
from typing import Iterable

from .addressing import AddressError, make_address, parse_address
from .entities import EntityService
from .front import FrontRevision, FrontService
from .handoff import Handoff, HandoffService
from .knowledge import KnowledgeService
from .relations import RelationService
from .store import MemoryStore, StoreError
from .work_items import WorkItemService


FINDABLE_RESOURCE_TYPES = frozenset({"knowledge", "entity", "work-item"})
READABLE_RESOURCE_TYPES = FINDABLE_RESOURCE_TYPES | frozenset({"front", "handoff", "relation"})
MAX_FIND_QUERY_CHARACTERS = 256
MAX_FIND_RESULTS = 100
MAX_READ_BATCH = 32


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

    def read(self, address: str) -> dict[str, object]:
        """Read one exact resource after validating its canonical address and project identity."""
        try:
            parsed = parse_address(address)
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
            else:
                raise ReadApiError("Type de ressource READ non exposé dans le contrat fermé M11-I.")
        except ReadApiError:
            raise
        except StoreError as exc:
            raise ReadApiError("Ressource VERA exacte introuvable ou incohérente.") from exc
        return {"address": parsed.canonical, "resource_type": parsed.resource_type, "record": record}

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

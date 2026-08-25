"""Declarative immutable capability registry for the VERA-MMU Core (M2.14)."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
import sqlite3
from typing import Any, Mapping

from .addressing import AddressError, make_address
from .identity import ProfileError, canonical_json
from .store import MemoryStore, StoreError


CAPABILITY_KINDS = frozenset({"ACTION", "CHECK", "ORACLE", "COLLECTOR", "GENERATOR", "QUERY"})
CAPABILITY_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){0,2}$")


class CapabilityError(StoreError):
    """Raised when a capability declaration violates the Core registry contract."""


class CapabilityNotFoundError(CapabilityError):
    """Raised when an exact capability read finds no matching identifier."""


@dataclass(frozen=True)
class Capability:
    """One immutable capability declaration, intentionally without runner or policy fields."""

    id: str
    name: str
    description: str
    kind: str
    version: str
    input_schema: dict[str, Any]
    parameter_schema: dict[str, Any]
    output_schema: dict[str, Any]
    metadata: dict[str, Any]
    created_at: str
    created_by: str
    address: str


class CapabilityService:
    """Create and read exact declarative capabilities; execution is deliberately out of scope."""

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def create(
        self,
        identifier: str,
        name: str,
        kind: str,
        version: str,
        *,
        description: str = "",
        input_schema: Mapping[str, Any] | None = None,
        parameter_schema: Mapping[str, Any] | None = None,
        output_schema: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
        actor: str = "system",
    ) -> Capability:
        """Create one generic immutable capability declaration and audit it atomically."""
        normalized_identifier = _require_identifier(self.store, identifier)
        normalized_name = _require_text(name, "name", maximum=256)
        normalized_kind = _require_kind(kind)
        normalized_version = _require_version(version)
        normalized_description = _require_optional_text(description, "description", maximum=4096)
        normalized_input_schema = _require_json_object(input_schema, "input_schema")
        normalized_parameter_schema = _require_json_object(parameter_schema, "parameter_schema")
        normalized_output_schema = _require_json_object(output_schema, "output_schema")
        normalized_metadata = _require_json_object(metadata, "metadata")
        normalized_actor = _require_text(actor, "actor", maximum=256)
        try:
            with self.store.transaction() as connection:
                connection.execute(
                    "INSERT INTO capability("
                    "id, name, description, kind, version, input_schema_json, parameter_schema_json, "
                    "output_schema_json, metadata_json, created_at, created_by"
                    ") VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                    (
                        normalized_identifier,
                        normalized_name,
                        normalized_description,
                        normalized_kind,
                        normalized_version,
                        canonical_json(normalized_input_schema),
                        canonical_json(normalized_parameter_schema),
                        canonical_json(normalized_output_schema),
                        canonical_json(normalized_metadata),
                        normalized_actor,
                    ),
                )
                row = connection.execute(
                    "SELECT id, name, description, kind, version, input_schema_json, parameter_schema_json, "
                    "output_schema_json, metadata_json, created_at, created_by FROM capability WHERE id = ?",
                    (normalized_identifier,),
                ).fetchone()
                if row is None:
                    raise CapabilityError("Création de capability non lisible.")
                self.store.append_audit(
                    connection,
                    "CAPABILITY_DECLARED",
                    {"capability_id": normalized_identifier, "kind": normalized_kind, "actor": normalized_actor},
                )
        except sqlite3.IntegrityError as exc:
            raise CapabilityError("Identifiant ou version de capability déjà utilisé ou invalide.") from exc
        return _capability_from_row(self.store, row)

    def get(self, identifier: str) -> Capability:
        """Read exactly one capability declaration by canonical VERA identifier; this is not FIND."""
        normalized_identifier = _require_identifier(self.store, identifier)
        row = self.store.connection.execute(
            "SELECT id, name, description, kind, version, input_schema_json, parameter_schema_json, "
            "output_schema_json, metadata_json, created_at, created_by FROM capability WHERE id = ?",
            (normalized_identifier,),
        ).fetchone()
        if row is None:
            raise CapabilityNotFoundError("Capability VERA introuvable.")
        return _capability_from_row(self.store, row)


def _require_identifier(store: MemoryStore, value: str) -> str:
    try:
        make_address(store.identity.project_id, "capability", value)
    except AddressError as exc:
        raise CapabilityError("Identifiant de capability VERA invalide.") from exc
    return value


def _require_kind(value: str) -> str:
    if not isinstance(value, str) or value not in CAPABILITY_KINDS:
        raise CapabilityError("Type de capability inconnu ou non autorisé.")
    return value


def _require_version(value: str) -> str:
    if not isinstance(value, str) or not CAPABILITY_VERSION_RE.fullmatch(value):
        raise CapabilityError("Version de capability invalide.")
    return value


def _require_text(value: str, label: str, *, maximum: int) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > maximum or "\x00" in value:
        raise CapabilityError(f"{label} doit être une chaîne canonique non vide.")
    return value


def _require_optional_text(value: str, label: str, *, maximum: int) -> str:
    if not isinstance(value, str) or value != value.strip() or len(value) > maximum or "\x00" in value:
        raise CapabilityError(f"{label} doit être une chaîne canonique.")
    return value


def _require_json_object(value: Mapping[str, Any] | None, label: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise CapabilityError(f"{label} doit être un objet JSON.")
    try:
        return json.loads(canonical_json(dict(value)))
    except (ProfileError, TypeError, ValueError) as exc:
        raise CapabilityError(f"{label} doit être sérialisable de façon canonique.") from exc


def _decode_json_object(value: object, label: str) -> dict[str, Any]:
    try:
        decoded = json.loads(str(value))
    except (TypeError, ValueError) as exc:
        raise CapabilityError(f"{label} de capability illisible.") from exc
    if not isinstance(decoded, dict):
        raise CapabilityError(f"{label} de capability non objet.")
    return decoded


def _capability_from_row(store: MemoryStore, row: sqlite3.Row) -> Capability:
    capability_id = str(row["id"])
    return Capability(
        id=capability_id,
        name=str(row["name"]),
        description=str(row["description"]),
        kind=str(row["kind"]),
        version=str(row["version"]),
        input_schema=_decode_json_object(row["input_schema_json"], "input_schema"),
        parameter_schema=_decode_json_object(row["parameter_schema_json"], "parameter_schema"),
        output_schema=_decode_json_object(row["output_schema_json"], "output_schema"),
        metadata=_decode_json_object(row["metadata_json"], "metadata"),
        created_at=str(row["created_at"]),
        created_by=str(row["created_by"]),
        address=make_address(store.identity.project_id, "capability", capability_id),
    )

"""Preview and apply a minimal capability declaration without accepting runners or policies."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from .addressing import AddressError, make_address
from .capabilities import CAPABILITY_KINDS, CAPABILITY_VERSION_RE, CapabilityError, CapabilityNotFoundError, CapabilityService
from .identity import canonical_json
from .store import MemoryStore, StoreError


CAPABILITY_DRAFT_FORMAT = "vera-capability-draft/v1"
_DASHBOARD_ACTOR = "DASHBOARD"


class CapabilityBuilderError(StoreError):
    """Raised when a capability declaration preview is invalid, stale, or unconfirmed."""


@dataclass(frozen=True)
class CapabilityDraftPreview:
    identifier: str
    name: str
    kind: str
    version: str
    description: str
    catalog_hash: str
    preview_hash: str

    def as_dict(self) -> dict[str, str]:
        return {
            "format": CAPABILITY_DRAFT_FORMAT,
            "identifier": self.identifier,
            "name": self.name,
            "kind": self.kind,
            "version": self.version,
            "description": self.description,
            "catalog_hash": self.catalog_hash,
            "preview_hash": self.preview_hash,
            "status": "PREVIEW",
        }


def preview_capability_draft(store: MemoryStore, *, identifier: str, name: str, kind: str, version: str, description: str = "") -> CapabilityDraftPreview:
    """Validate an allowlisted declaration and bind it to the current capability catalog state."""
    if not isinstance(store, MemoryStore):
        raise CapabilityBuilderError("Store invalide pour le builder de capability.")
    _validate_draft(store, identifier, name, kind, version, description)
    try:
        CapabilityService(store).get(identifier)
    except CapabilityNotFoundError:
        pass
    else:
        raise CapabilityBuilderError("Capability déjà déclarée : preview refusé.")
    catalog_hash = _catalog_hash(store)
    payload = {"format": CAPABILITY_DRAFT_FORMAT, "identifier": identifier, "name": name, "kind": kind, "version": version, "description": description, "catalog_hash": catalog_hash}
    return CapabilityDraftPreview(identifier, name, kind, version, description, catalog_hash, sha256(canonical_json(payload).encode("utf-8")).hexdigest())


def apply_capability_draft(store: MemoryStore, preview: CapabilityDraftPreview, *, confirm: bool) -> dict[str, object]:
    """Recompute the preview against current state, then create exactly one declaration atomically."""
    if confirm is not True:
        raise CapabilityBuilderError("Application de capability refusée sans confirmation explicite.")
    if not isinstance(preview, CapabilityDraftPreview):
        raise CapabilityBuilderError("Preview de capability invalide.")
    expected = preview_capability_draft(store, identifier=preview.identifier, name=preview.name, kind=preview.kind, version=preview.version, description=preview.description)
    if preview != expected:
        raise CapabilityBuilderError("Preview de capability altéré ou périmé.")
    try:
        capability = CapabilityService(store).create(preview.identifier, preview.name, preview.kind, preview.version, description=preview.description, actor=_DASHBOARD_ACTOR)
    except CapabilityError as exc:
        raise CapabilityBuilderError("Création de capability refusée.") from exc
    return {"status": "DECLARED", "preview_hash": preview.preview_hash, "capability": {"address": capability.address, "id": capability.id, "name": capability.name, "kind": capability.kind, "version": capability.version, "description": capability.description}}


def _validate_draft(store: MemoryStore, identifier: str, name: str, kind: str, version: str, description: str) -> None:
    try:
        make_address(store.identity.project_id, "capability", identifier)
    except AddressError as exc:
        raise CapabilityBuilderError("Identifiant de capability invalide.") from exc
    if not isinstance(name, str) or not name or name != name.strip() or len(name) > 256 or "\x00" in name:
        raise CapabilityBuilderError("Nom de capability invalide.")
    if not isinstance(kind, str) or kind not in CAPABILITY_KINDS:
        raise CapabilityBuilderError("Type de capability hors catalogue fermé.")
    if not isinstance(version, str) or CAPABILITY_VERSION_RE.fullmatch(version) is None:
        raise CapabilityBuilderError("Version de capability invalide.")
    if not isinstance(description, str) or description != description.strip() or len(description) > 4096 or "\x00" in description:
        raise CapabilityBuilderError("Description de capability invalide.")


def _catalog_hash(store: MemoryStore) -> str:
    rows = store.connection.execute("SELECT id, name, description, kind, version FROM capability ORDER BY id").fetchall()
    value: list[dict[str, Any]] = [{"id": str(row["id"]), "name": str(row["name"]), "description": str(row["description"]), "kind": str(row["kind"]), "version": str(row["version"])} for row in rows]
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()

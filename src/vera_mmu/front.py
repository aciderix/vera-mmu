"""Project-profile-bound, append-only Front snapshots (M11-AF)."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Mapping

from .identity import ProfileError, canonical_json, load_profile
from .project_policy import ProjectPolicyError, require_project_write
from .store import MemoryStore, StoreError


_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,127}$")


class FrontError(StoreError):
    """Raised when a Front snapshot cannot be safely read or written."""


@dataclass(frozen=True)
class FrontRevision:
    id: str
    previous_front_id: str | None
    profile_hash: str
    fields: dict[str, str]
    fields_hash: str
    created_at: str
    created_by: str


class FrontService:
    """Create immutable full Front snapshots; update is a derived new snapshot."""

    def __init__(self, store: MemoryStore) -> None:
        if not isinstance(store, MemoryStore):
            raise FrontError("Store invalide pour Front.")
        self.store = store

    def current(self) -> FrontRevision | None:
        row = self.store.connection.execute(
            "SELECT id, previous_front_id, profile_hash, fields_json, fields_hash, created_at, created_by "
            "FROM front_revision ORDER BY created_at DESC, id DESC LIMIT 1"
        ).fetchone()
        return None if row is None else self._from_row(row)

    def get(self, identifier: str) -> FrontRevision:
        _identifier(identifier, "Identifiant Front")
        row = self.store.connection.execute(
            "SELECT id, previous_front_id, profile_hash, fields_json, fields_hash, created_at, created_by FROM front_revision WHERE id = ?",
            (identifier,),
        ).fetchone()
        if row is None:
            raise FrontError("Révision Front introuvable.")
        return self._from_row(row)

    def replace(self, identifier: str, fields: Mapping[str, str], *, actor: str = "vera", confirm: bool = False) -> FrontRevision:
        """Record an exact complete snapshot for the fields declared by this profile."""
        _identifier(identifier, "Identifiant Front")
        _actor(actor)
        self._require_write(confirm)
        normalized = self._normalize_exact(fields)
        previous = self.current()
        return self._record(identifier, previous.id if previous else None, normalized, actor, "FRONT_REPLACED")

    def update(self, identifier: str, fields: Mapping[str, str], *, actor: str = "vera", confirm: bool = False) -> FrontRevision:
        """Derive a new exact snapshot by updating only declared fields on the current Front."""
        _identifier(identifier, "Identifiant Front")
        _actor(actor)
        self._require_write(confirm)
        previous = self.current()
        if previous is None:
            raise FrontError("Mise à jour Front refusée sans snapshot courant.")
        patch = self._normalize_patch(fields)
        merged = dict(previous.fields)
        merged.update(patch)
        return self._record(identifier, previous.id, self._normalize_exact(merged), actor, "FRONT_UPDATED")

    def _record(self, identifier: str, previous_id: str | None, fields: dict[str, str], actor: str, action: str) -> FrontRevision:
        text = canonical_json(fields)
        fields_hash = sha256(text.encode("utf-8")).hexdigest()
        with self.store.transaction() as connection:
            connection.execute(
                "INSERT INTO front_revision(id, previous_front_id, profile_hash, fields_json, fields_hash, created_at, created_by) "
                "VALUES(?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                (identifier, previous_id, self.store.identity.profile_hash, text, fields_hash, actor),
            )
            self.store.append_audit(connection, action, {"front_id": identifier, "previous_front_id": previous_id, "fields_hash": fields_hash, "actor": actor})
        return self.get(identifier)

    def _require_write(self, confirm: bool) -> None:
        try:
            require_project_write(self.store, confirm=confirm)
        except ProjectPolicyError as exc:
            raise FrontError("Écriture Front refusée par la policy projet.") from exc

    def _declared_fields(self) -> tuple[str, ...]:
        try:
            profile = load_profile(self.store.workspace.profile_path)
            front = profile["front"]
            fields = front["fields"]
        except (ProfileError, KeyError, TypeError) as exc:
            raise FrontError("Project Profile invalide pour Front.") from exc
        if not isinstance(fields, list) or not all(isinstance(item, str) for item in fields):
            raise FrontError("Champs Front du Project Profile invalides.")
        return tuple(fields)

    def _normalize_exact(self, fields: Mapping[str, str]) -> dict[str, str]:
        if not isinstance(fields, Mapping) or set(fields) != set(self._declared_fields()):
            raise FrontError("Le remplacement Front doit fournir exactement les champs déclarés.")
        return {name: _text(fields[name], f"Front.{name}") for name in self._declared_fields()}

    def _normalize_patch(self, fields: Mapping[str, str]) -> dict[str, str]:
        declared = set(self._declared_fields())
        if not isinstance(fields, Mapping) or not fields or not set(fields).issubset(declared):
            raise FrontError("La mise à jour Front doit viser un sous-ensemble non vide des champs déclarés.")
        return {name: _text(value, f"Front.{name}") for name, value in fields.items()}

    def _from_row(self, row: object) -> FrontRevision:
        try:
            fields = json.loads(str(row[3]))
            if not isinstance(fields, dict) or any(not isinstance(key, str) or not isinstance(value, str) for key, value in fields.items()):
                raise ValueError
            normalized = self._normalize_exact(fields)
            hash_value = sha256(canonical_json(normalized).encode("utf-8")).hexdigest()
            if hash_value != row[4] or row[2] != self.store.identity.profile_hash:
                raise ValueError
            return FrontRevision(str(row[0]), None if row[1] is None else str(row[1]), str(row[2]), normalized, str(row[4]), str(row[5]), str(row[6]))
        except (TypeError, ValueError, FrontError, json.JSONDecodeError) as exc:
            raise FrontError("Révision Front altérée, ambiguë ou étrangère au Project Profile.") from exc


def _identifier(value: str, label: str) -> None:
    if not isinstance(value, str) or _ID_RE.fullmatch(value) is None:
        raise FrontError(f"{label} invalide.")


def _actor(value: str) -> None:
    if not isinstance(value, str) or not value or len(value) > 256:
        raise FrontError("Acteur Front invalide.")


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\x00" in value or len(value) > 4096:
        raise FrontError(f"{label} doit être une chaîne canonique non vide de 4096 caractères au plus.")
    return value

"""Project-bound, append-only handoff snapshots derived from Front and Resume (M11-AF)."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re

from .front import FrontError, FrontRevision, FrontService
from .identity import canonical_json
from .profile_resume import ProfileResumeError, profile_resume_requirements
from .project_policy import ProjectPolicyError, require_project_write
from .session_lifecycle import ResumeDossier
from .store import MemoryStore, StoreError


_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,127}$")
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_FORMAT = "vera-handoff/v1"


class HandoffError(StoreError):
    """Raised when a handoff cannot be derived from verified current project state."""


@dataclass(frozen=True)
class Handoff:
    id: str
    front_revision_id: str
    profile_hash: str
    resume_contract_hash: str
    payload_json: str
    payload_hash: str
    created_at: str
    created_by: str


class HandoffService:
    """Prepare immutable handoffs; no import, restore, network or host action is implied."""

    def __init__(self, store: MemoryStore) -> None:
        if not isinstance(store, MemoryStore):
            raise HandoffError("Store invalide pour handoff.")
        self.store = store

    def latest(self) -> Handoff | None:
        row = self.store.connection.execute(
            "SELECT id, front_revision_id, profile_hash, resume_contract_hash, payload_json, payload_hash, created_at, created_by "
            "FROM handoff ORDER BY created_at DESC, id DESC LIMIT 1"
        ).fetchone()
        return None if row is None else self._from_row(row)

    def get(self, identifier: str) -> Handoff:
        _identifier(identifier)
        row = self.store.connection.execute(
            "SELECT id, front_revision_id, profile_hash, resume_contract_hash, payload_json, payload_hash, created_at, created_by FROM handoff WHERE id = ?",
            (identifier,),
        ).fetchone()
        if row is None:
            raise HandoffError("Handoff introuvable.")
        return self._from_row(row)

    def prepare(self, identifier: str, dossier: ResumeDossier, *, actor: str = "vera", confirm: bool = False) -> Handoff:
        _identifier(identifier)
        if not isinstance(actor, str) or not actor or len(actor) > 256:
            raise HandoffError("Acteur handoff invalide.")
        try:
            require_project_write(self.store, confirm=confirm)
        except ProjectPolicyError as exc:
            raise HandoffError("Préparation handoff refusée par la policy projet.") from exc
        front = FrontService(self.store).current()
        if front is None:
            raise FrontError("Préparation handoff refusée sans Front courant.")
        self._verify_dossier(dossier)
        payload = self._payload(front, dossier)
        payload_json = canonical_json(payload)
        payload_hash = sha256(payload_json.encode("utf-8")).hexdigest()
        with self.store.transaction() as connection:
            connection.execute(
                "INSERT INTO handoff(id, front_revision_id, profile_hash, resume_contract_hash, payload_json, payload_hash, created_at, created_by) "
                "VALUES(?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                (identifier, front.id, self.store.identity.profile_hash, dossier.resume_contract_hash, payload_json, payload_hash, actor),
            )
            self.store.append_audit(connection, "HANDOFF_PREPARED", {"handoff_id": identifier, "front_id": front.id, "resume_contract_hash": dossier.resume_contract_hash, "payload_hash": payload_hash, "actor": actor})
        return self.get(identifier)

    def _verify_dossier(self, dossier: ResumeDossier) -> None:
        if not isinstance(dossier, ResumeDossier) or dossier.project_id != self.store.identity.project_id or dossier.profile_hash != self.store.identity.profile_hash:
            raise HandoffError("Resume Dossier étranger au projet ou au Project Profile.")
        if not _HASH_RE.fullmatch(dossier.resume_contract_hash) or sha256(dossier.json_text.encode("utf-8")).hexdigest() != dossier.resume_contract_hash:
            raise HandoffError("Resume Dossier altéré ou hash incohérent.")
        try:
            if dossier.requirements != profile_resume_requirements(self.store):
                raise HandoffError("Resume Dossier périmé par rapport au Project Profile.")
        except ProfileResumeError as exc:
            raise HandoffError("Contrat de reprise Profile indisponible pour handoff.") from exc

    def _payload(self, front: FrontRevision, dossier: ResumeDossier) -> dict[str, object]:
        try:
            resume = json.loads(dossier.json_text)
        except json.JSONDecodeError as exc:
            raise HandoffError("Resume Dossier non JSON.") from exc
        return {"handoff": {"format": _FORMAT, "projectId": self.store.identity.project_id, "projectHash": self.store.identity.project_hash, "profileHash": self.store.identity.profile_hash, "front": {"id": front.id, "fieldsHash": front.fields_hash, "fields": front.fields}, "resume": resume}}

    def _from_row(self, row: object) -> Handoff:
        try:
            payload_json = str(row[4])
            if row[2] != self.store.identity.profile_hash or not _HASH_RE.fullmatch(str(row[3])) or sha256(payload_json.encode("utf-8")).hexdigest() != row[5]:
                raise ValueError
            payload = json.loads(payload_json)
            if not isinstance(payload, dict) or set(payload) != {"handoff"} or not isinstance(payload["handoff"], dict) or payload["handoff"].get("format") != _FORMAT:
                raise ValueError
            return Handoff(str(row[0]), str(row[1]), str(row[2]), str(row[3]), payload_json, str(row[5]), str(row[6]), str(row[7]))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise HandoffError("Handoff altéré, ambigu ou étranger.") from exc


def _identifier(value: str) -> None:
    if not isinstance(value, str) or _ID_RE.fullmatch(value) is None:
        raise HandoffError("Identifiant handoff invalide.")

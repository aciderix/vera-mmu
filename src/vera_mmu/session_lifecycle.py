"""Project-bound, transport-neutral resume dossier and session guard primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Mapping, Sequence

from .identity import canonical_json
from .store import MemoryStore, StoreError


_DOSSIER_FORMAT = "vera-resume-dossier/v1"
_STATE_FORMAT = "vera-session-guard/v1"
_SECTION_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
_ADAPTER_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,127}$")
_ARM_REASONS = frozenset({"SESSION_OPEN", "RESUME", "CONTEXT_PREPARE", "CONTEXT_RESTORED"})
_MODES = frozenset({"HARD", "SOFT"})
_MAX_RESUME_DOSSIER_BYTES = 24_000


class LifecycleError(StoreError):
    """Raised when resume lifecycle state is invalid, foreign, or ambiguous."""


class GuardDecision(str, Enum):
    """Closed Core outcomes that future host adapters may translate."""

    ALLOW = "ALLOW"
    ALLOW_WITH_NOTICE = "ALLOW_WITH_NOTICE"
    DENY = "DENY"
    NUDGE = "NUDGE"


@dataclass(frozen=True)
class ResumeSectionRequirement:
    """One project-declared section shape for a bounded resume ritual."""

    identifier: str
    minimum_characters: int
    maximum_characters: int


@dataclass(frozen=True)
class ResumeSection:
    identifier: str
    text: str


@dataclass(frozen=True)
class ResumeDossier:
    """Canonical project-bound dossier; no host event or Pack semantics are embedded."""

    project_id: str
    project_hash: str
    profile_hash: str
    requirements: tuple[ResumeSectionRequirement, ...]
    sections: tuple[ResumeSection, ...]
    resume_contract_hash: str
    json_text: str


@dataclass(frozen=True)
class ResumeGuardState:
    """Ephemeral local state; session input is represented only by a derived key."""

    adapter_id: str
    session_state_key: str
    reason: str
    mode: str
    status: str
    resume_contract_hash: str
    armed_at: str
    acknowledged_at: str | None
    acknowledgement_hash: str | None


@dataclass(frozen=True)
class GuardOutcome:
    decision: GuardDecision
    reason: str


class ResumeDossierService:
    """Compile a bounded ritual payload from already-authorized project information."""

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def compile(
        self,
        requirements: Sequence[ResumeSectionRequirement],
        sections: Mapping[str, str],
    ) -> ResumeDossier:
        normalized_requirements = _normalize_requirements(requirements)
        normalized_sections = _normalize_sections(normalized_requirements, sections)
        payload = {
            "resumeDossier": {
                "format": _DOSSIER_FORMAT,
                "projectId": self.store.identity.project_id,
                "projectHash": self.store.identity.project_hash,
                "profileHash": self.store.identity.profile_hash,
                "requirements": [
                    {"id": requirement.identifier, "minimum": requirement.minimum_characters, "maximum": requirement.maximum_characters}
                    for requirement in normalized_requirements
                ],
                "sections": [{"id": section.identifier, "text": section.text} for section in normalized_sections],
            }
        }
        json_text = canonical_json(payload) + "\n"
        if len(json_text.encode("utf-8")) > _MAX_RESUME_DOSSIER_BYTES:
            raise LifecycleError("Resume Dossier excède la borne de contexte configurée.")
        return ResumeDossier(
            project_id=self.store.identity.project_id,
            project_hash=self.store.identity.project_hash,
            profile_hash=self.store.identity.profile_hash,
            requirements=normalized_requirements,
            sections=normalized_sections,
            resume_contract_hash=_sha256_text(json_text),
            json_text=json_text,
        )


class ResumeGuardService:
    """Keep a fail-closed, runtime-confined resume guard outside MCP and host code."""

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def state_path(self, session_identity: str, adapter_id: str) -> Path:
        state_key = _state_key(self.store, session_identity, adapter_id)
        state_dir = self._state_dir()
        return state_dir / f"{state_key}.json"

    def arm(
        self,
        session_identity: str,
        adapter_id: str,
        reason: str,
        dossier: ResumeDossier,
        *,
        mode: str,
    ) -> ResumeGuardState:
        _require_session_identity(session_identity)
        _require_adapter_id(adapter_id)
        if reason not in _ARM_REASONS:
            raise LifecycleError("Événement d’armement lifecycle hors contrat fermé.")
        if mode not in _MODES:
            raise LifecycleError("Mode de garde lifecycle hors contrat fermé.")
        self._verify_dossier(dossier)
        path = self.state_path(session_identity, adapter_id)
        existing = self._read_existing(path, session_identity, adapter_id)
        if reason == "RESUME" and existing is not None and existing.status == "ACKNOWLEDGED":
            state = ResumeGuardState(
                adapter_id=adapter_id,
                session_state_key=existing.session_state_key,
                reason=reason,
                mode=mode,
                status="ACKNOWLEDGED",
                resume_contract_hash=dossier.resume_contract_hash,
                armed_at=existing.armed_at,
                acknowledged_at=existing.acknowledged_at,
                acknowledgement_hash=existing.acknowledgement_hash,
            )
        else:
            state = ResumeGuardState(
                adapter_id=adapter_id,
                session_state_key=_state_key(self.store, session_identity, adapter_id),
                reason=reason,
                mode=mode,
                status="ARMED" if mode == "HARD" else "DEGRADED",
                resume_contract_hash=dossier.resume_contract_hash,
                armed_at=_utc_now(),
                acknowledged_at=None,
                acknowledgement_hash=None,
            )
        self._write_state(path, state, dossier.requirements)
        with self.store.transaction() as connection:
            self.store.append_audit(
                connection,
                "RESUME_GUARD_ARMED",
                {
                    "adapter_id": adapter_id,
                    "session_state_key": state.session_state_key,
                    "reason": reason,
                    "mode": mode,
                    "status": state.status,
                    "resume_contract_hash": dossier.resume_contract_hash,
                },
            )
        return state

    def acknowledge(
        self,
        session_identity: str,
        adapter_id: str,
        resume_contract_hash: str,
        sections: Mapping[str, str],
    ) -> bool:
        if not _is_session_identity(session_identity) or not _ADAPTER_ID_RE.fullmatch(adapter_id):
            return False
        if not _is_hash(resume_contract_hash):
            return False
        try:
            path = self.state_path(session_identity, adapter_id)
            state = self._read_existing(path, session_identity, adapter_id)
        except LifecycleError:
            return False
        if state is None or state.status not in {"ARMED", "DEGRADED"}:
            return False
        if state.resume_contract_hash != resume_contract_hash:
            return False
        requirements = self._requirements_from_state(path, session_identity, adapter_id)
        try:
            normalized_sections = _normalize_sections(requirements, sections)
        except LifecycleError:
            return False
        acknowledged = ResumeGuardState(
            adapter_id=state.adapter_id,
            session_state_key=state.session_state_key,
            reason=state.reason,
            mode=state.mode,
            status="ACKNOWLEDGED",
            resume_contract_hash=state.resume_contract_hash,
            armed_at=state.armed_at,
            acknowledged_at=_utc_now(),
            acknowledgement_hash=_sha256_text(canonical_json({section.identifier: section.text for section in normalized_sections})),
        )
        self._write_state(path, acknowledged, requirements)
        with self.store.transaction() as connection:
            self.store.append_audit(
                connection,
                "RESUME_GUARD_ACKNOWLEDGED",
                {
                    "adapter_id": adapter_id,
                    "session_state_key": acknowledged.session_state_key,
                    "resume_contract_hash": acknowledged.resume_contract_hash,
                    "acknowledgement_hash": acknowledged.acknowledgement_hash,
                },
            )
        return True

    def acknowledge_current(
        self,
        session_identity: str,
        adapter_id: str,
        sections: Mapping[str, str],
    ) -> bool:
        """Acknowledge only the contract currently armed in local state.

        This is the path intended for an adapter-owned transport: no caller can submit a
        contract hash because it is read from the already project/session-bound state.
        """
        if not _is_session_identity(session_identity) or not _ADAPTER_ID_RE.fullmatch(adapter_id):
            return False
        try:
            state = self._read_existing(self.state_path(session_identity, adapter_id), session_identity, adapter_id)
        except LifecycleError:
            return False
        if state is None:
            return False
        return self.acknowledge(session_identity, adapter_id, state.resume_contract_hash, sections)

    def precheck(self, session_identity: str, adapter_id: str) -> GuardOutcome:
        if not _is_session_identity(session_identity):
            return GuardOutcome(GuardDecision.DENY, "resume guard: session identity missing")
        if not _ADAPTER_ID_RE.fullmatch(adapter_id):
            return GuardOutcome(GuardDecision.DENY, "resume guard: adapter identity invalid")
        try:
            state = self._read_existing(self.state_path(session_identity, adapter_id), session_identity, adapter_id)
        except LifecycleError:
            return GuardOutcome(GuardDecision.DENY, "resume guard: state integrity failure")
        if state is None or state.status == "ACKNOWLEDGED":
            return GuardOutcome(GuardDecision.ALLOW, "resume guard: no active acknowledgement required")
        if state.status == "DEGRADED":
            return GuardOutcome(
                GuardDecision.ALLOW_WITH_NOTICE,
                "resume guard: degraded dossier remains unacknowledged; continue only after repair",
            )
        if state.status == "ARMED":
            return GuardOutcome(
                GuardDecision.DENY,
                "resume guard: acknowledgement for the armed resume contract is required before an action",
            )
        return GuardOutcome(GuardDecision.DENY, "resume guard: state integrity failure")

    def session_ending(self, session_identity: str, adapter_id: str, *, already_nudged: bool) -> GuardOutcome:
        if already_nudged:
            return GuardOutcome(GuardDecision.ALLOW, "resume guard: nudge already emitted")
        if not _is_session_identity(session_identity) or not _ADAPTER_ID_RE.fullmatch(adapter_id):
            return GuardOutcome(GuardDecision.ALLOW, "resume guard: no scoped session state")
        try:
            state = self._read_existing(self.state_path(session_identity, adapter_id), session_identity, adapter_id)
        except LifecycleError:
            return GuardOutcome(GuardDecision.NUDGE, "resume guard: state integrity failure requires repair")
        if state is None or state.status == "ACKNOWLEDGED":
            return GuardOutcome(GuardDecision.ALLOW, "resume guard: no active acknowledgement required")
        return GuardOutcome(GuardDecision.NUDGE, "resume guard: active dossier remains unacknowledged")

    def _state_dir(self) -> Path:
        runtime_dir = self.store.locator.runtime_dir.resolve(strict=False)
        candidate = runtime_dir / "lifecycle"
        try:
            candidate.relative_to(runtime_dir)
        except ValueError as exc:
            raise LifecycleError("Répertoire lifecycle hors runtime VERA.") from exc
        if candidate.is_symlink():
            raise LifecycleError("Répertoire lifecycle symlinké refusé.")
        try:
            candidate.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise LifecycleError("Création du runtime lifecycle impossible.") from exc
        if not candidate.is_dir() or candidate.is_symlink():
            raise LifecycleError("Répertoire lifecycle ambigu ou non régulier.")
        return candidate

    def _verify_dossier(self, dossier: ResumeDossier) -> None:
        if not isinstance(dossier, ResumeDossier):
            raise LifecycleError("Resume Dossier invalide.")
        if dossier.project_id != self.store.identity.project_id or dossier.project_hash != self.store.identity.project_hash:
            raise LifecycleError("Resume Dossier lié à un autre projet.")
        if dossier.profile_hash != self.store.identity.profile_hash:
            raise LifecycleError("Resume Dossier lié à un autre profil.")
        if dossier.resume_contract_hash != _sha256_text(dossier.json_text):
            raise LifecycleError("Hash de Resume Dossier incohérent.")
        try:
            parsed = json.loads(dossier.json_text)
        except (TypeError, ValueError) as exc:
            raise LifecycleError("Resume Dossier JSON illisible.") from exc
        expected = {
            "resumeDossier": {
                "format": _DOSSIER_FORMAT,
                "projectId": dossier.project_id,
                "projectHash": dossier.project_hash,
                "profileHash": dossier.profile_hash,
                "requirements": [
                    {"id": requirement.identifier, "minimum": requirement.minimum_characters, "maximum": requirement.maximum_characters}
                    for requirement in dossier.requirements
                ],
                "sections": [{"id": section.identifier, "text": section.text} for section in dossier.sections],
            }
        }
        if parsed != expected or canonical_json(parsed) + "\n" != dossier.json_text:
            raise LifecycleError("Resume Dossier non canonique ou ambigu.")

    def _read_existing(self, path: Path, session_identity: str, adapter_id: str) -> ResumeGuardState | None:
        if path.is_symlink():
            raise LifecycleError("État lifecycle symlinké refusé.")
        if not path.exists():
            return None
        if not path.is_file():
            raise LifecycleError("État lifecycle non régulier refusé.")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise LifecycleError("État lifecycle illisible.") from exc
        if not isinstance(raw, Mapping):
            raise LifecycleError("État lifecycle non objet.")
        state = _state_from_payload(raw)
        expected_key = _state_key(self.store, session_identity, adapter_id)
        if state.adapter_id != adapter_id or state.session_state_key != expected_key:
            raise LifecycleError("État lifecycle étranger ou ambigu.")
        if raw.get("projectId") != self.store.identity.project_id or raw.get("projectHash") != self.store.identity.project_hash:
            raise LifecycleError("État lifecycle lié à un autre projet.")
        if raw.get("profileHash") != self.store.identity.profile_hash:
            raise LifecycleError("État lifecycle lié à un autre profil.")
        _requirements_from_payload(raw)
        return state

    def _requirements_from_state(self, path: Path, session_identity: str, adapter_id: str) -> tuple[ResumeSectionRequirement, ...]:
        if path.is_symlink() or not path.is_file():
            raise LifecycleError("État lifecycle indisponible pour acquittement.")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise LifecycleError("État lifecycle illisible.") from exc
        if not isinstance(raw, Mapping):
            raise LifecycleError("État lifecycle non objet.")
        self._read_existing(path, session_identity, adapter_id)
        return _requirements_from_payload(raw)

    def _write_state(
        self,
        path: Path,
        state: ResumeGuardState,
        requirements: Sequence[ResumeSectionRequirement],
    ) -> None:
        if path.is_symlink():
            raise LifecycleError("État lifecycle symlinké refusé.")
        if path.exists():
            if not path.is_file():
                raise LifecycleError("État lifecycle non régulier refusé.")
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise LifecycleError("État lifecycle existant illisible.") from exc
            if not isinstance(existing, Mapping):
                raise LifecycleError("État lifecycle existant non objet.")
            _state_from_payload(existing)
            _requirements_from_payload(existing)
        normalized_requirements = _normalize_requirements(requirements)
        payload = {
            "format": _STATE_FORMAT,
            "projectId": self.store.identity.project_id,
            "projectHash": self.store.identity.project_hash,
            "profileHash": self.store.identity.profile_hash,
            "adapterId": state.adapter_id,
            "sessionStateKey": state.session_state_key,
            "reason": state.reason,
            "mode": state.mode,
            "status": state.status,
            "resumeContractHash": state.resume_contract_hash,
            "armedAt": state.armed_at,
            "acknowledgedAt": state.acknowledged_at,
            "acknowledgementHash": state.acknowledgement_hash,
            "requirements": [
                {"id": requirement.identifier, "minimum": requirement.minimum_characters, "maximum": requirement.maximum_characters}
                for requirement in normalized_requirements
            ],
        }
        serialized = canonical_json(payload) + "\n"
        temporary_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=path.parent,
                prefix=f".{path.stem}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_name = temporary.name
                temporary.write(serialized)
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_name, path)
        except OSError as exc:
            raise LifecycleError("Écriture atomique de l’état lifecycle impossible.") from exc
        finally:
            if temporary_name is not None:
                try:
                    Path(temporary_name).unlink(missing_ok=True)
                except OSError:
                    pass


def _normalize_requirements(requirements: Sequence[ResumeSectionRequirement]) -> tuple[ResumeSectionRequirement, ...]:
    if not isinstance(requirements, Sequence) or isinstance(requirements, (str, bytes)) or not requirements or len(requirements) > 32:
        raise LifecycleError("Contrat de sections lifecycle invalide.")
    normalized: list[ResumeSectionRequirement] = []
    seen: set[str] = set()
    for requirement in requirements:
        if not isinstance(requirement, ResumeSectionRequirement):
            raise LifecycleError("Section lifecycle invalide.")
        if not _SECTION_ID_RE.fullmatch(requirement.identifier) or requirement.identifier in seen:
            raise LifecycleError("Identifiant de section lifecycle invalide ou dupliqué.")
        if (
            not isinstance(requirement.minimum_characters, int)
            or isinstance(requirement.minimum_characters, bool)
            or not isinstance(requirement.maximum_characters, int)
            or isinstance(requirement.maximum_characters, bool)
            or requirement.minimum_characters < 1
            or requirement.maximum_characters < requirement.minimum_characters
            or requirement.maximum_characters > 16_384
        ):
            raise LifecycleError("Bornes de section lifecycle invalides.")
        seen.add(requirement.identifier)
        normalized.append(requirement)
    return tuple(normalized)


def _normalize_sections(
    requirements: Sequence[ResumeSectionRequirement],
    sections: Mapping[str, str],
) -> tuple[ResumeSection, ...]:
    if not isinstance(sections, Mapping) or set(sections) != {requirement.identifier for requirement in requirements}:
        raise LifecycleError("Sections de Resume Dossier incomplètes ou ambiguës.")
    normalized: list[ResumeSection] = []
    for requirement in requirements:
        value = sections.get(requirement.identifier)
        if not isinstance(value, str) or value != value.strip() or "\x00" in value:
            raise LifecycleError("Texte de section lifecycle invalide.")
        if not requirement.minimum_characters <= len(value) <= requirement.maximum_characters:
            raise LifecycleError("Texte de section lifecycle hors bornes.")
        normalized.append(ResumeSection(requirement.identifier, value))
    return tuple(normalized)


def _requirements_from_payload(payload: Mapping[str, Any]) -> tuple[ResumeSectionRequirement, ...]:
    raw = payload.get("requirements")
    if not isinstance(raw, list):
        raise LifecycleError("Contrat de sections lifecycle absent.")
    parsed: list[ResumeSectionRequirement] = []
    for item in raw:
        if not isinstance(item, Mapping) or set(item) != {"id", "minimum", "maximum"}:
            raise LifecycleError("Contrat de sections lifecycle ambigu.")
        parsed.append(ResumeSectionRequirement(item["id"], item["minimum"], item["maximum"]))
    return _normalize_requirements(parsed)


def _state_from_payload(payload: Mapping[str, Any]) -> ResumeGuardState:
    required = {
        "format",
        "projectId",
        "projectHash",
        "profileHash",
        "adapterId",
        "sessionStateKey",
        "reason",
        "mode",
        "status",
        "resumeContractHash",
        "armedAt",
        "acknowledgedAt",
        "acknowledgementHash",
        "requirements",
    }
    if set(payload) != required or payload.get("format") != _STATE_FORMAT:
        raise LifecycleError("Format d’état lifecycle invalide.")
    adapter_id = payload.get("adapterId")
    session_state_key = payload.get("sessionStateKey")
    reason = payload.get("reason")
    mode = payload.get("mode")
    status = payload.get("status")
    contract_hash = payload.get("resumeContractHash")
    armed_at = payload.get("armedAt")
    acknowledged_at = payload.get("acknowledgedAt")
    acknowledgement_hash = payload.get("acknowledgementHash")
    if not isinstance(adapter_id, str) or not _ADAPTER_ID_RE.fullmatch(adapter_id):
        raise LifecycleError("Adapter d’état lifecycle invalide.")
    if not _is_hash(session_state_key) or not isinstance(reason, str) or reason not in _ARM_REASONS:
        raise LifecycleError("Identité ou raison d’état lifecycle invalide.")
    if mode not in _MODES or status not in {"ARMED", "ACKNOWLEDGED", "DEGRADED"}:
        raise LifecycleError("Mode ou statut d’état lifecycle invalide.")
    if not _is_hash(contract_hash) or not _is_timestamp(armed_at):
        raise LifecycleError("Hash ou horodatage d’état lifecycle invalide.")
    if status == "ACKNOWLEDGED":
        if not _is_timestamp(acknowledged_at) or not _is_hash(acknowledgement_hash):
            raise LifecycleError("Acquittement d’état lifecycle invalide.")
    elif acknowledged_at is not None or acknowledgement_hash is not None:
        raise LifecycleError("Acquittement inattendu dans l’état lifecycle.")
    if (mode == "HARD" and status == "DEGRADED") or (mode == "SOFT" and status == "ARMED"):
        raise LifecycleError("Relation mode/statut lifecycle invalide.")
    return ResumeGuardState(
        adapter_id=adapter_id,
        session_state_key=session_state_key,
        reason=reason,
        mode=mode,
        status=status,
        resume_contract_hash=contract_hash,
        armed_at=armed_at,
        acknowledged_at=acknowledged_at,
        acknowledgement_hash=acknowledgement_hash,
    )


def _state_key(store: MemoryStore, session_identity: str, adapter_id: str) -> str:
    _require_session_identity(session_identity)
    _require_adapter_id(adapter_id)
    return _sha256_text(f"{store.identity.project_hash}\x00{adapter_id}\x00{session_identity}")


def _require_session_identity(value: str) -> None:
    if not _is_session_identity(value):
        raise LifecycleError("Identité de session lifecycle invalide.")


def _is_session_identity(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value == value.strip() and len(value) <= 512 and "\x00" not in value


def _require_adapter_id(value: str) -> None:
    if not isinstance(value, str) or not _ADAPTER_ID_RE.fullmatch(value):
        raise LifecycleError("Identifiant d’adapter lifecycle invalide.")


def _is_hash(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _is_timestamp(value: object) -> bool:
    return isinstance(value, str) and bool(value) and len(value) <= 64 and value.endswith("Z")


def _sha256_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import sqlite3

from .identity import canonical_json
from .store import MemoryStore, StoreError


VALIDATOR_KINDS = frozenset({"EVIDENCE_HASH"})


class ValidatorError(StoreError):
    pass


@dataclass(frozen=True)
class Validator:
    id: str
    kind: str
    created_at: str
    created_by: str


@dataclass(frozen=True)
class ValidationResult:
    id: str
    validator_id: str
    evidence_id: str
    verdict: str
    expected_hash: str
    observed_hash: str | None
    created_at: str
    created_by: str


class ValidatorService:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def register(self, identifier: str, kind: str, *, actor: str = "system") -> Validator:
        if not isinstance(identifier, str) or not identifier or "/" in identifier:
            raise ValidatorError("Identifiant de validator invalide.")
        if kind not in VALIDATOR_KINDS:
            raise ValidatorError("Type de validator hors catalogue fermé.")
        if not isinstance(actor, str) or not actor or actor != actor.strip() or len(actor) > 256:
            raise ValidatorError("Actor invalide.")
        try:
            with self.store.transaction() as connection:
                connection.execute(
                    "INSERT INTO validator(id, kind, created_at, created_by) "
                    "VALUES(?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                    (identifier, kind, actor),
                )
                row = connection.execute(
                    "SELECT id, kind, created_at, created_by FROM validator WHERE id = ?", (identifier,)
                ).fetchone()
                self.store.append_audit(
                    connection,
                    "VALIDATOR_REGISTERED",
                    {"validator_id": identifier, "kind": kind, "actor": actor},
                )
        except sqlite3.IntegrityError as exc:
            raise ValidatorError("Validator invalide ou déjà enregistré.") from exc
        if row is None:
            raise ValidatorError("Validator non lisible.")
        return _validator(row)

    def get(self, identifier: str) -> Validator:
        if not isinstance(identifier, str) or not identifier or "/" in identifier:
            raise ValidatorError("Identifiant de validator invalide.")
        row = self.store.connection.execute(
            "SELECT id, kind, created_at, created_by FROM validator WHERE id = ?", (identifier,)
        ).fetchone()
        if row is None:
            raise ValidatorError("Validator introuvable.")
        return _validator(row)

    def get_result(self, identifier: str) -> ValidationResult:
        if not isinstance(identifier, str) or not identifier or "/" in identifier:
            raise ValidatorError("Identifiant de validation invalide.")
        row = self.store.connection.execute(
            "SELECT id, validator_id, evidence_id, verdict, expected_hash, observed_hash, created_at, created_by "
            "FROM validation_result WHERE id = ?",
            (identifier,),
        ).fetchone()
        if row is None:
            raise ValidatorError("Résultat de validation introuvable.")
        return _result(row)

    def validate(self, identifier: str, validator_id: str, evidence_id: str, *, actor: str = "system") -> ValidationResult:
        if not all(isinstance(value, str) and value and "/" not in value for value in (identifier, validator_id, evidence_id, actor)):
            raise ValidatorError("Identifiant de validation invalide.")
        try:
            with self.store.transaction() as connection:
                result = record_evidence_hash_validation(connection, identifier, validator_id, evidence_id, actor=actor)
                self.store.append_audit(
                    connection,
                    "VALIDATION_RECORDED",
                    {"validation_id": identifier, "validator_id": validator_id, "evidence_id": evidence_id, "verdict": result.verdict, "actor": actor},
                )
        except sqlite3.IntegrityError as exc:
            raise ValidatorError("Résultat de validation invalide ou déjà présent.") from exc
        return result


def record_evidence_hash_validation(connection: sqlite3.Connection, identifier: str, validator_id: str, evidence_id: str, *, actor: str) -> ValidationResult:
    validator = connection.execute("SELECT kind FROM validator WHERE id = ?", (validator_id,)).fetchone()
    evidence = connection.execute("SELECT content_json, content_hash FROM evidence WHERE id = ?", (evidence_id,)).fetchone()
    if validator is None or validator["kind"] != "EVIDENCE_HASH":
        raise ValidatorError("Validator EVIDENCE_HASH introuvable.")
    if evidence is None:
        raise ValidatorError("Evidence introuvable.")
    expected_hash = str(evidence["content_hash"])
    observed_hash = _canonical_hash(str(evidence["content_json"]))
    verdict = "PASS" if observed_hash == expected_hash else "FAIL"
    connection.execute(
        "INSERT INTO validation_result(id, validator_id, evidence_id, verdict, expected_hash, observed_hash, created_at, created_by) "
        "VALUES(?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
        (identifier, validator_id, evidence_id, verdict, expected_hash, observed_hash, actor),
    )
    row = connection.execute(
        "SELECT id, validator_id, evidence_id, verdict, expected_hash, observed_hash, created_at, created_by "
        "FROM validation_result WHERE id = ?",
        (identifier,),
    ).fetchone()
    if row is None:
        raise ValidatorError("Résultat de validation non lisible.")
    return _result(row)


def _canonical_hash(content_json: str) -> str:
    try:
        content = json.loads(content_json)
        if not isinstance(content, dict):
            raise ValueError("Le contenu d’evidence doit être un objet.")
        return hashlib.sha256(canonical_json(content).encode()).hexdigest()
    except (TypeError, ValueError) as exc:
        raise ValidatorError("Contenu d’evidence non canonique.") from exc


def _validator(row: sqlite3.Row) -> Validator:
    return Validator(str(row["id"]), str(row["kind"]), str(row["created_at"]), str(row["created_by"]))


def _result(row: sqlite3.Row) -> ValidationResult:
    return ValidationResult(
        id=str(row["id"]),
        validator_id=str(row["validator_id"]),
        evidence_id=str(row["evidence_id"]),
        verdict=str(row["verdict"]),
        expected_hash=str(row["expected_hash"]),
        observed_hash=None if row["observed_hash"] is None else str(row["observed_hash"]),
        created_at=str(row["created_at"]),
        created_by=str(row["created_by"]),
    )

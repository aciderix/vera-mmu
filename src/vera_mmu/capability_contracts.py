from __future__ import annotations

from dataclasses import dataclass
import json
import sqlite3
from typing import Any, Mapping

from .capabilities import CapabilityError
from .identity import canonical_json
from .parameter_validation import ParameterValidationError, validate_parameter_schema
from .store import MemoryStore, StoreError

RUNNER_PROFILES = frozenset({"NOOP", "EVIDENCE_HASH"})
NETWORK_POLICIES = frozenset({"DENY_NETWORK"})

class CapabilityContractError(StoreError):
    pass

@dataclass(frozen=True)
class CapabilityContract:
    capability_id: str
    runner_profile: str
    network_policy: str
    timeout_seconds: int
    parameter_schema: dict[str, Any]
    yields_proof: bool
    created_at: str
    created_by: str

class CapabilityContractService:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def declare(self, capability_id: str, runner_profile: str, network_policy: str, timeout_seconds: int, *, parameter_schema: Mapping[str, Any] | None = None, yields_proof: bool = False, actor: str = "system") -> CapabilityContract:
        if not isinstance(capability_id, str) or not capability_id or "/" in capability_id:
            raise CapabilityContractError("Identifiant de capability invalide.")
        if runner_profile not in RUNNER_PROFILES or network_policy not in NETWORK_POLICIES:
            raise CapabilityContractError("Profil de runner ou policy réseau hors catalogue fermé.")
        if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= 3600:
            raise CapabilityContractError("Timeout hors borne.")
        if not isinstance(yields_proof, bool):
            raise CapabilityContractError("yields_proof doit être booléen.")
        if not isinstance(actor, str) or not actor or actor != actor.strip():
            raise CapabilityContractError("Actor invalide.")
        if parameter_schema is None:
            parameter_schema = {}
        if not isinstance(parameter_schema, Mapping):
            raise CapabilityContractError("parameter_schema doit être un objet JSON.")
        try:
            schema = validate_parameter_schema(parameter_schema)
        except ParameterValidationError as exc:
            raise CapabilityContractError("parameter_schema hors sous-ensemble fermé.") from exc
        try:
            with self.store.transaction() as connection:
                if connection.execute("SELECT 1 FROM capability WHERE id = ?", (capability_id,)).fetchone() is None:
                    raise CapabilityContractError("Capability inconnue.")
                connection.execute("INSERT INTO capability_contract(capability_id, runner_profile, network_policy, timeout_seconds, parameter_schema_json, yields_proof, created_at, created_by) VALUES(?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)", (capability_id, runner_profile, network_policy, timeout_seconds, canonical_json(schema), int(yields_proof), actor))
                row = connection.execute("SELECT capability_id, runner_profile, network_policy, timeout_seconds, parameter_schema_json, yields_proof, created_at, created_by FROM capability_contract WHERE capability_id = ?", (capability_id,)).fetchone()
                self.store.append_audit(connection, "CAPABILITY_CONTRACT_DECLARED", {"capability_id": capability_id, "runner_profile": runner_profile, "actor": actor})
        except sqlite3.IntegrityError as exc:
            raise CapabilityContractError("Contrat de capability invalide ou déjà déclaré.") from exc
        if row is None:
            raise CapabilityContractError("Contrat non lisible.")
        return _contract(row)

    def get(self, capability_id: str) -> CapabilityContract:
        row = self.store.connection.execute("SELECT capability_id, runner_profile, network_policy, timeout_seconds, parameter_schema_json, yields_proof, created_at, created_by FROM capability_contract WHERE capability_id = ?", (capability_id,)).fetchone()
        if row is None:
            raise CapabilityContractError("Contrat de capability introuvable.")
        return _contract(row)

def _contract(row: sqlite3.Row) -> CapabilityContract:
    decoded = json.loads(str(row["parameter_schema_json"]))
    if not isinstance(decoded, dict):
        raise CapabilityContractError("Schéma de contrat illisible.")
    return CapabilityContract(str(row["capability_id"]), str(row["runner_profile"]), str(row["network_policy"]), int(row["timeout_seconds"]), decoded, bool(row["yields_proof"]), str(row["created_at"]), str(row["created_by"]))

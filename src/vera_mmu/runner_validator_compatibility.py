from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .identity import canonical_json
from .store import StoreError


EVIDENCE_VALIDATION_SCHEMA = {
    "type": "object",
    "properties": {
        "validator_id": {"type": "string"},
        "evidence_id": {"type": "string"},
    },
    "required": ["validator_id", "evidence_id"],
    "additionalProperties": False,
}
RUNNER_VALIDATOR_PAIRS = frozenset({("EVIDENCE_HASH", "EVIDENCE_HASH"), ("EVIDENCE_FIELDS", "EVIDENCE_FIELDS")})


class RunnerValidatorCompatibilityError(StoreError):
    pass


def ensure_runner_validator_compatibility(
    runner_profile: str,
    validator_kind: str,
    parameter_schema: Mapping[str, Any],
) -> None:
    if (runner_profile, validator_kind) not in RUNNER_VALIDATOR_PAIRS:
        raise RunnerValidatorCompatibilityError("Couple runner-validator hors catalogue fermé.")
    if not isinstance(parameter_schema, Mapping) or canonical_json(parameter_schema) != canonical_json(EVIDENCE_VALIDATION_SCHEMA):
        raise RunnerValidatorCompatibilityError("Schéma runner-validator hors catalogue fermé.")

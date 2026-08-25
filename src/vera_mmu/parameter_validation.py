from __future__ import annotations

import json
from typing import Any, Mapping

from .identity import canonical_json


ROOT_KEYS = frozenset({"type", "properties", "required", "additionalProperties"})
PROPERTY_KEYS = frozenset({"type"})
SCALAR_TYPES = frozenset({"string", "integer", "number", "boolean", "null"})


class ParameterValidationError(ValueError):
    pass


def validate_parameter_schema(schema: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(schema, Mapping):
        raise ParameterValidationError("Le schéma de paramètres doit être un objet JSON.")
    normalized = _json_object(schema, "Le schéma de paramètres")
    unknown = set(normalized) - ROOT_KEYS
    if unknown:
        raise ParameterValidationError("Le schéma de paramètres contient une clé non supportée.")
    root_type = normalized.get("type", "object")
    if root_type != "object":
        raise ParameterValidationError("Le schéma racine doit être de type object.")
    properties = normalized.get("properties", {})
    if not isinstance(properties, dict):
        raise ParameterValidationError("properties doit être un objet JSON.")
    for name, property_schema in properties.items():
        if not isinstance(name, str) or not name:
            raise ParameterValidationError("Chaque propriété doit avoir un nom non vide.")
        _validate_property_schema(property_schema)
    required = normalized.get("required", [])
    if not isinstance(required, list) or any(not isinstance(name, str) or not name for name in required):
        raise ParameterValidationError("required doit être une liste de noms de propriété non vides.")
    if len(set(required)) != len(required) or any(name not in properties for name in required):
        raise ParameterValidationError("required doit référencer une propriété unique déclarée.")
    additional_properties = normalized.get("additionalProperties", True)
    if not isinstance(additional_properties, bool):
        raise ParameterValidationError("additionalProperties doit être booléen.")
    return normalized


def validate_parameters(schema: Mapping[str, Any], parameters: Mapping[str, Any]) -> dict[str, Any]:
    validated_schema = validate_parameter_schema(schema)
    if not isinstance(parameters, Mapping):
        raise ParameterValidationError("Les paramètres doivent être un objet JSON.")
    values = _json_object(parameters, "Les paramètres")
    if any(not isinstance(name, str) for name in values):
        raise ParameterValidationError("Les noms de paramètres doivent être des chaînes.")
    properties = validated_schema.get("properties", {})
    required = validated_schema.get("required", [])
    for name in required:
        if name not in values:
            raise ParameterValidationError("Un paramètre requis est absent.")
    if not validated_schema.get("additionalProperties", True) and any(name not in properties for name in values):
        raise ParameterValidationError("Un paramètre non déclaré est interdit.")
    for name, value in values.items():
        property_schema = properties.get(name)
        if property_schema is not None:
            _validate_scalar(value, property_schema["type"])
    return values


def _json_object(value: Mapping[str, Any], label: str) -> dict[str, Any]:
    if any(not isinstance(name, str) for name in value):
        raise ParameterValidationError(f"{label} doit utiliser des clés textuelles.")
    try:
        decoded = json.loads(canonical_json(dict(value)))
    except (TypeError, ValueError) as exc:
        raise ParameterValidationError(f"{label} doit être sérialisable en JSON canonique.") from exc
    if not isinstance(decoded, dict):
        raise ParameterValidationError(f"{label} doit être un objet JSON.")
    return decoded


def _validate_property_schema(schema: Any) -> None:
    if not isinstance(schema, Mapping):
        raise ParameterValidationError("Chaque schéma de propriété doit être un objet JSON.")
    normalized = _json_object(schema, "Chaque schéma de propriété")
    if set(normalized) != PROPERTY_KEYS or normalized.get("type") not in SCALAR_TYPES:
        raise ParameterValidationError("Chaque propriété doit déclarer un type scalaire supporté.")


def _validate_scalar(value: Any, expected_type: str) -> None:
    valid = (
        (expected_type == "string" and isinstance(value, str))
        or (expected_type == "integer" and isinstance(value, int) and not isinstance(value, bool))
        or (expected_type == "number" and isinstance(value, (int, float)) and not isinstance(value, bool))
        or (expected_type == "boolean" and isinstance(value, bool))
        or (expected_type == "null" and value is None)
    )
    if not valid:
        raise ParameterValidationError("La valeur d’un paramètre ne respecte pas son type déclaré.")

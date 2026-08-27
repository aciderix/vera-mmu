"""Validated, project-local declarative catalogs for a VERA Project Profile (M11-A)."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
from typing import Any, Mapping

import yaml
from yaml.resolver import BaseResolver

from .identity import ProfileError, canonical_json, load_profile
from .parameter_validation import ParameterValidationError, validate_parameter_schema
from .workspace import Workspace, WorkspaceError, resolve_workspace


class ProjectCatalogError(ValueError):
    """Raised when a profile-referenced catalog is absent, unsafe, or malformed."""


CAPABILITY_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
CAPABILITY_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){0,2}$")
GATE_ID_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
CAPABILITY_KEYS = frozenset({"id", "name", "description", "kind", "version", "runner", "network_policy", "timeout_seconds", "parameter_schema", "yields_proof", "policy", "inputs", "outputs", "validator", "artifacts", "confirmation_required"})
GATE_KEYS = frozenset({"id", "name", "capability_id", "required", "expected"})
CAPABILITY_KINDS = frozenset({"ACTION", "CHECK", "ORACLE", "COLLECTOR", "GENERATOR", "QUERY"})
RUNNER_PROFILES = frozenset({"NOOP", "EVIDENCE_HASH", "EVIDENCE_FIELDS", "OBSERVED_PROCESS"})
NETWORK_POLICIES = frozenset({"DENY_NETWORK"})
PROJECT_POLICIES = frozenset({"READ_ONLY", "GENERATE", "NETWORK", "SENSITIVE"})
VALIDATORS = frozenset({"EVIDENCE_HASH", "EVIDENCE_FIELDS"})


class _CatalogYamlLoader(yaml.SafeLoader):
    """Safe YAML loader that refuses duplicate mapping keys."""


def _unique_mapping(loader: _CatalogYamlLoader, node: yaml.nodes.MappingNode, deep: bool = False) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ProjectCatalogError("Clé YAML dupliquée dans un catalogue VERA.")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_CatalogYamlLoader.add_constructor(BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


@dataclass(frozen=True)
class ProjectCatalogs:
    """Validated project catalog snapshots and their canonical hashes."""

    capabilities: dict[str, Any]
    gates: dict[str, Any]
    policies: dict[str, Any]
    capability_catalog_hash: str
    gate_catalog_hash: str
    policy_hash: str


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise ProjectCatalogError(f"{label} doit être un objet YAML à clés textuelles.")
    return dict(value)


def _catalog_path(workspace: Workspace, relative: Any, label: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise ProjectCatalogError(f"Chemin {label} invalide.")
    path = workspace.project_root / relative
    try:
        path.relative_to(workspace.runtime_dir)
    except ValueError as exc:
        raise ProjectCatalogError(f"{label} doit rester sous le runtime VERA.") from exc
    current = workspace.project_root
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            raise ProjectCatalogError(f"{label} symlinké refusé.")
    if not path.is_file():
        raise ProjectCatalogError(f"Catalogue {label} introuvable ou non régulier.")
    return path


def _load_yaml(workspace: Workspace, relative: Any, label: str) -> dict[str, Any]:
    path = _catalog_path(workspace, relative, label)
    try:
        if path.stat().st_size > 256_000:
            raise ProjectCatalogError(f"Catalogue {label} trop volumineux.")
        decoded = yaml.load(path.read_text(encoding="utf-8"), Loader=_CatalogYamlLoader)
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ProjectCatalogError(f"Lecture YAML du catalogue {label} impossible.") from exc
    return _mapping(decoded, f"catalogue {label}")


def _exact_catalog(value: dict[str, Any], label: str, expected_format: str, collection: str) -> dict[str, Any]:
    if set(value) != {"format", collection}:
        raise ProjectCatalogError(f"Catalogue {label} doit contenir exactement format et {collection}.")
    if value.get("format") != expected_format or not isinstance(value.get(collection), list):
        raise ProjectCatalogError(f"Format ou collection du catalogue {label} invalide.")
    return value


def _nonempty_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\x00" in value or len(value) > 4096:
        raise ProjectCatalogError(f"{label} doit être une chaîne canonique non vide.")
    return value


def _string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item == item.strip() and item and "\x00" not in item for item in value):
        raise ProjectCatalogError(f"{label} doit être une liste de chaînes canoniques.")
    if len(value) != len(set(value)):
        raise ProjectCatalogError(f"{label} ne doit pas contenir de doublon.")
    return list(value)


def _validate_capabilities(value: dict[str, Any]) -> dict[str, Any]:
    identifiers: set[str] = set()
    for index, item in enumerate(value["capabilities"]):
        capability = _mapping(item, f"capabilities[{index}]")
        if set(capability) != CAPABILITY_KEYS:
            raise ProjectCatalogError(f"capabilities[{index}] doit respecter le schéma fermé VERA.")
        identifier = _nonempty_text(capability.get("id"), f"capabilities[{index}].id")
        if CAPABILITY_ID_RE.fullmatch(identifier) is None or identifier in identifiers:
            raise ProjectCatalogError(f"capabilities[{index}].id invalide ou dupliqué.")
        identifiers.add(identifier)
        _nonempty_text(capability.get("name"), f"capabilities[{index}].name")
        _nonempty_text(capability.get("description"), f"capabilities[{index}].description")
        version = capability.get("version")
        if not isinstance(version, str) or CAPABILITY_VERSION_RE.fullmatch(version) is None:
            raise ProjectCatalogError(f"capabilities[{index}].version invalide.")
        if capability.get("kind") not in CAPABILITY_KINDS or capability.get("runner") not in RUNNER_PROFILES or capability.get("network_policy") not in NETWORK_POLICIES:
            raise ProjectCatalogError(f"capabilities[{index}] référence une kind, runner ou policy réseau inconnue.")
        if capability.get("policy") not in PROJECT_POLICIES or capability.get("validator") not in VALIDATORS:
            raise ProjectCatalogError(f"capabilities[{index}] référence une policy ou validator inconnu.")
        timeout = capability.get("timeout_seconds")
        if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 3600:
            raise ProjectCatalogError(f"capabilities[{index}].timeout_seconds hors borne.")
        if not isinstance(capability.get("yields_proof"), bool) or not isinstance(capability.get("confirmation_required"), bool):
            raise ProjectCatalogError(f"capabilities[{index}] exige des indicateurs booléens explicites.")
        try:
            validate_parameter_schema(_mapping(capability.get("parameter_schema"), f"capabilities[{index}].parameter_schema"))
        except ParameterValidationError as exc:
            raise ProjectCatalogError(f"capabilities[{index}].parameter_schema hors contrat fermé.") from exc
        for key in ("inputs", "outputs", "artifacts"):
            _string_list(capability.get(key), f"capabilities[{index}].{key}")
    return value


def _validate_gates(value: dict[str, Any], capabilities: Mapping[str, Any]) -> dict[str, Any]:
    capability_ids = {str(item["id"]) for item in capabilities["capabilities"]}
    identifiers: set[str] = set()
    for index, item in enumerate(value["gates"]):
        gate = _mapping(item, f"gates[{index}]")
        if set(gate) != GATE_KEYS:
            raise ProjectCatalogError(f"gates[{index}] doit respecter le schéma fermé VERA.")
        identifier = _nonempty_text(gate.get("id"), f"gates[{index}].id")
        if GATE_ID_RE.fullmatch(identifier) is None or identifier in identifiers:
            raise ProjectCatalogError(f"gates[{index}].id invalide ou dupliqué.")
        identifiers.add(identifier)
        _nonempty_text(gate.get("name"), f"gates[{index}].name")
        if gate.get("capability_id") not in capability_ids:
            raise ProjectCatalogError(f"gates[{index}].capability_id doit référencer une capability déclarée.")
        if not isinstance(gate.get("required"), bool):
            raise ProjectCatalogError(f"gates[{index}].required doit être booléen.")
        expected = _mapping(gate.get("expected"), f"gates[{index}].expected")
        if set(expected) != {"verdict"} or expected.get("verdict") not in {"PASS", "FAIL", "ERROR", "SKIPPED", "UNKNOWN"}:
            raise ProjectCatalogError(f"gates[{index}].expected doit déclarer un verdict VERA unique.")
    return value


def _policy_catalog(value: dict[str, Any]) -> dict[str, Any]:
    allowed = {"format", "filesystem", "network", "process", "git", "destructive", "promotion"}
    if set(value) != allowed or value.get("format") != "vera-policy-catalog/v1":
        raise ProjectCatalogError("Format ou clés du catalogue policies invalides.")
    for key in allowed - {"format"}:
        _mapping(value.get(key), f"policies.{key}")
    runners = value["process"].get("allowed_runners")
    if not isinstance(runners, list) or not all(isinstance(item, str) for item in runners) or len(runners) != len(set(runners)):
        raise ProjectCatalogError("policies.process.allowed_runners doit être une liste sans doublon de chaînes.")
    return value


def _hash(value: Mapping[str, Any]) -> str:
    try:
        return sha256(canonical_json(value).encode("utf-8")).hexdigest()
    except ProfileError as exc:
        raise ProjectCatalogError("Catalogue non sérialisable de façon canonique.") from exc


def load_project_catalogs(profile_path: str | Path) -> ProjectCatalogs:
    """Load all profile-referenced catalog files without executing any declaration."""
    try:
        profile = load_profile(profile_path)
        workspace = resolve_workspace(profile, profile_path)
    except (ProfileError, WorkspaceError) as exc:
        raise ProjectCatalogError("Profile ou workspace invalide pour les catalogues.") from exc
    capabilities = _validate_capabilities(
        _exact_catalog(
            _load_yaml(workspace, profile["capabilities"]["catalog"], "capabilities"),
            "capabilities",
            "vera-capability-catalog/v1",
            "capabilities",
        )
    )
    gates = _validate_gates(
        _exact_catalog(
            _load_yaml(workspace, profile["gates"]["catalog"], "gates"),
            "gates",
            "vera-gate-catalog/v1",
            "gates",
        ),
        capabilities,
    )
    policies = _policy_catalog(_load_yaml(workspace, profile["policies"]["file"], "policies"))
    return ProjectCatalogs(
        capabilities=capabilities,
        gates=gates,
        policies=policies,
        capability_catalog_hash=_hash(capabilities),
        gate_catalog_hash=_hash(gates),
        policy_hash=_hash(policies),
    )

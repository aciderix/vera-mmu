"""Validated, project-local declarative catalogs for a VERA Project Profile (M11-A)."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping

import yaml
from yaml.resolver import BaseResolver

from .identity import ProfileError, canonical_json, load_profile
from .workspace import Workspace, WorkspaceError, resolve_workspace


class ProjectCatalogError(ValueError):
    """Raised when a profile-referenced catalog is absent, unsafe, or malformed."""


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
    if not isinstance(value, Mapping):
        raise ProjectCatalogError(f"{label} doit être un objet YAML.")
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


def _policy_catalog(value: dict[str, Any]) -> dict[str, Any]:
    allowed = {"format", "filesystem", "network", "process", "git", "destructive", "promotion"}
    if set(value) != allowed or value.get("format") != "vera-policy-catalog/v1":
        raise ProjectCatalogError("Format ou clés du catalogue policies invalides.")
    for key in allowed - {"format"}:
        _mapping(value.get(key), f"policies.{key}")
    runners = value["process"].get("allowed_runners")
    if not isinstance(runners, list) or not all(isinstance(item, str) for item in runners):
        raise ProjectCatalogError("policies.process.allowed_runners doit être une liste de chaînes.")
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
    capabilities = _exact_catalog(
        _load_yaml(workspace, profile["capabilities"]["catalog"], "capabilities"),
        "capabilities",
        "vera-capability-catalog/v1",
        "capabilities",
    )
    gates = _exact_catalog(
        _load_yaml(workspace, profile["gates"]["catalog"], "gates"),
        "gates",
        "vera-gate-catalog/v1",
        "gates",
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

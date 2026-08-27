"""Canonical Project Profile and project identity primitives (M1, C02/C11)."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import re
from typing import Any, Mapping

import yaml

from .workspace import Workspace


PROJECT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
DECLARATION_ID_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
RESUME_SECTION_ID_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
CORE_KNOWLEDGE_TYPES = ("RULE", "DECISION", "OBSERVATION", "HYPOTHESIS", "STATE", "MEASUREMENT", "DISCOVERY", "ARCHITECTURE")
CORE_RELATION_TYPES = ("VERIFIED_BY", "SUPERSEDES", "INFORMED_BY", "BLOCKED_BY", "IMPLEMENTS", "DERIVED_FROM", "CONCERNS", "APPLIES_TO", "CAUSED_BY", "EVOLVES_TO")
DEFAULT_RESUME_SECTIONS = ("rules", "current_state", "validated_facts", "risks", "next_action")


class ProfileError(ValueError):
    """Raised when a Project Profile is syntactically or semantically invalid."""


@dataclass(frozen=True)
class ProfileIdentity:
    """Stable identity derived from normalized Project Profile semantics."""

    project_id: str
    profile_version: str
    profile_hash: str

    def as_dict(self) -> dict[str, str]:
        return {
            "project_id": self.project_id,
            "profile_version": self.profile_version,
            "profile_hash": self.profile_hash,
        }


@dataclass(frozen=True)
class ProjectIdentity:
    """Stable project binding for future stores, bundles, and resume contracts."""

    project_id: str
    profile_version: str
    profile_hash: str
    workspace_hash: str
    project_hash: str

    def as_dict(self) -> dict[str, str]:
        return {
            "project_id": self.project_id,
            "profile_version": self.profile_version,
            "profile_hash": self.profile_hash,
            "workspace_hash": self.workspace_hash,
            "project_hash": self.project_hash,
        }


def canonical_json(value: Any) -> str:
    """Serialize JSON-compatible values deterministically and reject unsafe YAML values."""
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ProfileError("Le profil contient une valeur non sérialisable de façon canonique.") from exc


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ProfileError(f"{label} doit être un objet YAML.")
    return dict(value)


def _require_string(mapping: Mapping[str, Any], key: str, label: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ProfileError(f"{label}.{key} doit être une chaîne non vide.")
    return value.strip()


def _require_relative_path(mapping: Mapping[str, Any], key: str, label: str, *, allow_dot: bool) -> str:
    value = _require_string(mapping, key, label)
    path = Path(value)
    if path.is_absolute() or PureWindowsPath(value).drive or ".." in path.parts or "\\" in value or "\x00" in value:
        raise ProfileError(f"{label}.{key} doit rester relatif et ne pas contenir de traversal.")
    if not allow_dot and path == Path("."):
        raise ProfileError(f"{label}.{key} doit désigner un sous-répertoire ou un fichier relatif.")
    return value


def _require_bool(mapping: Mapping[str, Any], key: str, label: str, default: bool) -> bool:
    value = mapping.get(key, default)
    if not isinstance(value, bool):
        raise ProfileError(f"{label}.{key} doit être booléen.")
    return value


def _require_declaration_ids(value: Any, label: str, defaults: tuple[str, ...]) -> list[str]:
    items = list(defaults) if value is None else value
    if not isinstance(items, list) or not items:
        raise ProfileError(f"{label} doit être une liste non vide de types déclarés.")
    normalized: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, str) or DECLARATION_ID_RE.fullmatch(item.strip()) is None:
            raise ProfileError(f"{label}[{index}] doit être un identifiant déclaratif majuscule valide.")
        item = item.strip()
        if item in normalized:
            raise ProfileError(f"{label} ne doit pas contenir de type dupliqué.")
        normalized.append(item)
    return normalized


def _require_runtime_path(value: Any, label: str, memory_dir: str, *, default: str) -> str:
    path = _require_relative_path({"value": default if value is None else value}, "value", label, allow_dot=False)
    runtime = Path(memory_dir)
    candidate = Path(path)
    if candidate.parts[: len(runtime.parts)] != runtime.parts:
        raise ProfileError(f"{label} doit rester sous storage.memory_dir.")
    return candidate.as_posix()


def _require_resume(value: Any) -> dict[str, Any]:
    source = _require_mapping({} if value is None else value, "resume")
    template = _require_string({"template": source.get("template", "engineering")}, "template", "resume")
    raw_sections = source.get("sections", list(DEFAULT_RESUME_SECTIONS))
    if not isinstance(raw_sections, list) or not raw_sections:
        raise ProfileError("resume.sections doit être une liste non vide.")
    sections: list[dict[str, Any]] = []
    ids: set[str] = set()
    for index, item in enumerate(raw_sections):
        source_item = {"id": item, "required": True} if isinstance(item, str) else _require_mapping(item, f"resume.sections[{index}]")
        section_id = _require_string(source_item, "id", f"resume.sections[{index}]")
        if RESUME_SECTION_ID_RE.fullmatch(section_id) is None:
            raise ProfileError(f"resume.sections[{index}].id doit être un identifiant de section valide.")
        if section_id in ids:
            raise ProfileError("resume.sections ne doit pas contenir de section dupliquée.")
        required = _require_bool(source_item, "required", f"resume.sections[{index}]", True)
        sections.append({"id": section_id, "required": required})
        ids.add(section_id)
    return {"template": template, "sections": sections}


def validate_profile(profile: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the small Core-owned contract and return normalized JSON data.

    Domain taxonomies, capabilities, gates, integrations and policies remain
    declarative. M1 validates only what is necessary to bind a project safely.
    """
    root = json.loads(canonical_json(_require_mapping(profile, "profile")))
    mmu = _require_mapping(root.get("mmu"), "mmu")
    project = _require_mapping(root.get("project"), "project")
    workspace = _require_mapping(root.get("workspace"), "workspace")
    storage = _require_mapping(root.get("storage"), "storage")
    identity = _require_mapping(root.get("identity", {}), "identity")

    version = _require_string(mmu, "version", "mmu")
    project_id = _require_string(project, "id", "project")
    project_name = _require_string(project, "name", "project")
    project_domain = _require_string(project, "domain", "project")
    workspace_root = _require_relative_path(workspace, "root", "workspace", allow_dot=True)
    memory_dir = _require_relative_path(storage, "memory_dir", "storage", allow_dot=False)
    sqlite_file = _require_relative_path(storage, "sqlite_file", "storage", allow_dot=False)
    artifacts_dir = _require_relative_path(storage, "artifacts_dir", "storage", allow_dot=False)

    additional_roots = workspace.get("additional_roots", [])
    if not isinstance(additional_roots, list):
        raise ProfileError("workspace.additional_roots doit être une liste.")
    normalized_additional: list[str] = []
    for index, value in enumerate(additional_roots):
        if not isinstance(value, str):
            raise ProfileError(f"workspace.additional_roots[{index}] doit être une chaîne.")
        normalized_additional.append(
            _require_relative_path({"value": value}, "value", f"workspace.additional_roots[{index}]", allow_dot=False)
        )

    for key in ("max_context_bytes", "max_resume_bytes"):
        if key in storage and (not isinstance(storage[key], int) or isinstance(storage[key], bool) or storage[key] < 1):
            raise ProfileError(f"storage.{key} doit être un entier strictement positif.")
    include_vcs_revision = _require_bool(identity, "include_vcs_revision", "identity", False)
    include_profile_hash = _require_bool(identity, "include_profile_hash", "identity", True)

    if not PROJECT_ID_RE.fullmatch(project_id):
        raise ProfileError("project.id doit contenir 2 à 64 caractères minuscules : a-z, 0-9 ou -.")
    if not version.startswith("2."):
        raise ProfileError("mmu.version doit appartenir à la famille 2.x.")

    root["mmu"] = {**mmu, "version": version}
    root["project"] = {**project, "id": project_id, "name": project_name, "domain": project_domain}
    root["workspace"] = {
        **workspace,
        "root": Path(workspace_root).as_posix(),
        "additional_roots": [Path(item).as_posix() for item in normalized_additional],
    }
    root["storage"] = {
        **storage,
        "memory_dir": Path(memory_dir).as_posix(),
        "sqlite_file": Path(sqlite_file).as_posix(),
        "artifacts_dir": Path(artifacts_dir).as_posix(),
    }
    root["identity"] = {
        **identity,
        "include_vcs_revision": include_vcs_revision,
        "include_profile_hash": include_profile_hash,
    }
    root["resume"] = _require_resume(root.get("resume"))
    root["knowledge"] = {"types": _require_declaration_ids(_require_mapping(root.get("knowledge", {}), "knowledge").get("types"), "knowledge.types", CORE_KNOWLEDGE_TYPES)}
    root["entities"] = {"types": _require_declaration_ids(_require_mapping(root.get("entities", {}), "entities").get("types"), "entities.types", ("COMPONENT",))}
    root["relations"] = {"types": _require_declaration_ids(_require_mapping(root.get("relations", {}), "relations").get("types"), "relations.types", CORE_RELATION_TYPES)}
    work = _require_mapping(root.get("work", {}), "work")
    root["work"] = {"enabled": _require_bool(work, "enabled", "work", True)}
    capabilities = _require_mapping(root.get("capabilities", {}), "capabilities")
    gates = _require_mapping(root.get("gates", {}), "gates")
    policies = _require_mapping(root.get("policies", {}), "policies")
    integrations = _require_mapping(root.get("integrations", {}), "integrations")
    root["capabilities"] = {"catalog": _require_runtime_path(capabilities.get("catalog"), "capabilities.catalog", memory_dir, default=f"{memory_dir}/capabilities.yaml")}
    root["gates"] = {"catalog": _require_runtime_path(gates.get("catalog"), "gates.catalog", memory_dir, default=f"{memory_dir}/gates.yaml")}
    root["policies"] = {"file": _require_runtime_path(policies.get("file"), "policies.file", memory_dir, default=f"{memory_dir}/policies.yaml")}
    root["integrations"] = {"agent_profiles": _require_runtime_path(integrations.get("agent_profiles"), "integrations.agent_profiles", memory_dir, default=f"{memory_dir}/agent-profiles.yaml")}
    return json.loads(canonical_json(root))


def load_profile(path: str | Path) -> dict[str, Any]:
    """Load one YAML profile safely and validate the Core-owned contract."""
    source = Path(path).expanduser()
    if not source.is_file():
        raise ProfileError(f"Profil introuvable : {source}")
    try:
        raw = yaml.safe_load(source.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ProfileError(f"Lecture YAML impossible : {source}") from exc
    return validate_profile(_require_mapping(raw, "profile"))


def profile_identity(profile: Mapping[str, Any]) -> ProfileIdentity:
    """Return an identity stable for equal normalized profile semantics."""
    normalized = validate_profile(profile)
    profile_hash = sha256(canonical_json(normalized).encode("utf-8")).hexdigest()
    mmu = _require_mapping(normalized["mmu"], "mmu")
    project = _require_mapping(normalized["project"], "project")
    return ProfileIdentity(
        project_id=str(project["id"]),
        profile_version=str(mmu["version"]),
        profile_hash=profile_hash,
    )


def _workspace_hash(normalized: Mapping[str, Any], workspace: Workspace | None) -> str:
    """Hash a portable workspace topology; VCS discovery is intentionally excluded."""
    if workspace is None:
        workspace_value = _require_mapping(normalized["workspace"], "workspace")
        storage_value = _require_mapping(normalized["storage"], "storage")
        material: dict[str, Any] = {
            "roots": [workspace_value["root"], *workspace_value["additional_roots"]],
            "runtime_dir": storage_value["memory_dir"],
        }
    else:
        try:
            roots = [root.relative_to(workspace.project_root).as_posix() for root in workspace.roots]
            runtime_dir = workspace.runtime_dir.relative_to(workspace.project_root).as_posix()
        except ValueError as exc:
            raise ProfileError("Le workspace résolu ne reste pas sous son projet.") from exc
        material = {"roots": roots, "runtime_dir": runtime_dir}
    return sha256(canonical_json(material).encode("utf-8")).hexdigest()


def project_identity(profile: Mapping[str, Any], workspace: Workspace | None = None) -> ProjectIdentity:
    """Bind profile and portable workspace topology without requiring Git or a path identity."""
    normalized = validate_profile(profile)
    profile_value = profile_identity(normalized)
    workspace_hash = _workspace_hash(normalized, workspace)
    material = {
        "project_id": profile_value.project_id,
        "profile_hash": profile_value.profile_hash,
        "profile_version": profile_value.profile_version,
        "workspace_hash": workspace_hash,
    }
    return ProjectIdentity(
        project_id=profile_value.project_id,
        profile_version=profile_value.profile_version,
        profile_hash=profile_value.profile_hash,
        workspace_hash=workspace_hash,
        project_hash=sha256(canonical_json(material).encode("utf-8")).hexdigest(),
    )

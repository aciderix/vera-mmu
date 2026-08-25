"""Canonical Project Profile loading and identity primitives.

This module intentionally has no dependency on an MCP transport, a domain pack,
or a project toolchain. It establishes a small, testable M1 boundary: a profile
is parsed safely, validated minimally, normalized as canonical JSON, and hashed.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Mapping

import yaml


PROJECT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")


class ProfileError(ValueError):
    """Raised when a Project Profile is syntactically or semantically invalid."""


@dataclass(frozen=True)
class ProfileIdentity:
    """Stable identity derived from a normalized Project Profile."""

    project_id: str
    profile_version: str
    profile_hash: str

    def as_dict(self) -> dict[str, str]:
        """Return a transport-neutral, deterministic representation."""
        return {
            "project_id": self.project_id,
            "profile_version": self.profile_version,
            "profile_hash": self.profile_hash,
        }


def canonical_json(value: Any) -> str:
    """Serialize only JSON-compatible values with a deterministic representation."""
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


def validate_profile(profile: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the minimal universal contract and return a deep-normalized mapping.

    This deliberately validates only Core-owned fields. Domain taxonomies,
    capabilities, gates, and integrations are left declarative for later layers.
    """
    root = _require_mapping(profile, "profile")
    mmu = _require_mapping(root.get("mmu"), "mmu")
    project = _require_mapping(root.get("project"), "project")
    workspace = _require_mapping(root.get("workspace"), "workspace")
    storage = _require_mapping(root.get("storage"), "storage")

    version = _require_string(mmu, "version", "mmu")
    project_id = _require_string(project, "id", "project")
    _require_string(project, "name", "project")
    _require_string(project, "domain", "project")
    workspace_root = _require_string(workspace, "root", "workspace")
    _require_string(storage, "memory_dir", "storage")
    _require_string(storage, "sqlite_file", "storage")
    _require_string(storage, "artifacts_dir", "storage")

    if not PROJECT_ID_RE.fullmatch(project_id):
        raise ProfileError("project.id doit contenir 2 à 64 caractères minuscules : a-z, 0-9 ou -.")
    if workspace_root.startswith("/") or ".." in Path(workspace_root).parts:
        raise ProfileError("workspace.root doit rester relatif et ne pas contenir '..'.")
    if not version.startswith("2."):
        raise ProfileError("mmu.version doit appartenir à la famille 2.x.")

    # Canonical JSON gives a deep copy while rejecting non-JSON YAML values,
    # including aliases that resolve to unsupported object types.
    return json.loads(canonical_json(root))


def load_profile(path: str | Path) -> dict[str, Any]:
    """Load one YAML profile safely and validate its minimal Core contract."""
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

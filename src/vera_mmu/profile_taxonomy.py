"""Editing the declared taxonomy, entities and relations of a project (§29.2, steps 5 to 7).

The Core declared these three sections and synchronised them into the store; nothing could ask it
to change them. This closes that, under the same cycle as every other sensitive write: preview,
freshness check, explicit confirmation, atomic write or refusal.

One refusal carries the module. A type that already carries knowledge, entities or relations
cannot be removed, because removing it would orphan what the project has recorded. That is
counted against the memory itself and refused **here**, in the Core — not greyed out in a screen.
A rule enforced only by an interface stops existing the moment anything else writes.

Identifiers stay declarative and uppercase. Their lowercase store form is derived by the Core
when the catalogue is synchronised; it is never typed by whoever edits the profile.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Mapping, Sequence
import os
import sqlite3

import yaml

from .identity import DECLARATION_ID_RE, ProfileError, canonical_json, load_profile
from .runtime import RuntimeLocator
from .store import StoreError
from .workspace import WorkspaceError, resolve_workspace


TAXONOMY_FORMAT = "vera-taxonomy-edit/v1"

# Each editable section: where it lives in the profile, and the table that would be orphaned.
_SECTIONS: dict[str, tuple[str, str, str, str]] = {
    "knowledge": ("knowledge", "types", "knowledge", "type_id"),
    "entities": ("entities", "types", "entity", "type_id"),
    "relations": ("relations", "types", "relation", "relation_type_id"),
}
# A project declaring no knowledge type cannot record anything at all.
_REQUIRED_SECTIONS = ("knowledge",)


class TaxonomyError(StoreError):
    """Raised when a taxonomy edit cannot be planned or applied exactly as reviewed."""


@dataclass(frozen=True)
class TaxonomyChange:
    """What one section would gain and lose."""

    section: str
    added: tuple[str, ...]
    removed: tuple[str, ...]
    declared: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "section": self.section,
            "added": list(self.added),
            "removed": list(self.removed),
            "declared": list(self.declared),
        }


@dataclass(frozen=True)
class TaxonomyPreview:
    """What an edit would change, reviewed before anything is written."""

    format: str
    profile_path: str
    changes: tuple[TaxonomyChange, ...]
    blockers: tuple[str, ...]
    status: str
    preview_hash: str
    mutation: str = "NONE"
    _content: str = field(default="", repr=False, compare=False)

    def as_dict(self) -> dict[str, object]:
        return {
            "format": self.format,
            "profile_path": self.profile_path,
            "changes": [item.as_dict() for item in self.changes],
            "blockers": list(self.blockers),
            "status": self.status,
            "preview_hash": self.preview_hash,
            "mutation": self.mutation,
        }


def preview_taxonomy_edit(
    profile_path: str | Path,
    *,
    knowledge_types: Sequence[str] | None = None,
    entity_types: Sequence[str] | None = None,
    relation_types: Sequence[str] | None = None,
) -> TaxonomyPreview:
    """Plan a taxonomy edit, counting what a removal would orphan. Writes nothing."""
    requested = {"knowledge": knowledge_types, "entities": entity_types, "relations": relation_types}
    named = {name: value for name, value in requested.items() if value is not None}
    if not named:
        raise TaxonomyError("Aucune section de taxonomie nommée : rien à prévisualiser.")

    path = _profile_path(profile_path)
    try:
        profile = load_profile(path)
    except (ProfileError, OSError, ValueError) as exc:
        raise TaxonomyError(f"Project Profile invalide : édition de taxonomie refusée ({exc}).") from exc

    candidate = deepcopy(profile)
    changes: list[TaxonomyChange] = []
    blockers: list[str] = []
    usage = _usage(profile, path)
    for section, values in sorted(named.items()):
        block, key, _, _ = _SECTIONS[section]
        declared = _normalize(section, values)
        current = tuple(str(item) for item in _current(profile, block, key))
        added = tuple(item for item in declared if item not in current)
        removed = tuple(item for item in current if item not in declared)
        for item in removed:
            count = usage.get(section, {}).get(item, 0)
            if count > 0:
                blockers.append(
                    f"`{item}` porte déjà {count} enregistrement(s) dans la mémoire du projet : "
                    f"le retirer les rendrait orphelins."
                )
        target = candidate.setdefault(block, {})
        if not isinstance(target, dict):
            raise TaxonomyError(f"Section `{block}` du Project Profile invalide.")
        target[key] = list(declared)
        changes.append(TaxonomyChange(section, added, removed, declared))

    ordered = tuple(changes)
    content = yaml.safe_dump(candidate, allow_unicode=True, default_flow_style=False, sort_keys=False)
    if blockers:
        status = "REFUSED"
    elif all(not item.added and not item.removed for item in ordered):
        status = "NOTHING_TO_CHANGE"
    else:
        status = "PREVIEW"
    payload = {
        "format": TAXONOMY_FORMAT,
        "profile_path": str(path),
        "current_profile_sha256": sha256(path.read_bytes()).hexdigest(),
        "changes": [item.as_dict() for item in ordered],
        "blockers": sorted(blockers),
        "status": status,
    }
    return TaxonomyPreview(
        format=TAXONOMY_FORMAT,
        profile_path=str(path),
        changes=ordered,
        blockers=tuple(sorted(blockers)),
        status=status,
        preview_hash=sha256(canonical_json(payload).encode("utf-8")).hexdigest(),
        _content=content,
    )


def apply_taxonomy_edit(profile_path: str | Path, preview: TaxonomyPreview, *, confirm: bool) -> dict[str, object]:
    """Write exactly the taxonomy the reviewed preview described, atomically."""
    if confirm is not True:
        raise TaxonomyError("Édition de taxonomie refusée sans confirmation explicite.")
    if not isinstance(preview, TaxonomyPreview):
        raise TaxonomyError("Preview d’édition de taxonomie invalide.")
    if preview.status == "REFUSED":
        raise TaxonomyError("Édition refusée : " + " ".join(preview.blockers))
    path = _profile_path(profile_path)
    if str(path) != preview.profile_path:
        raise TaxonomyError("Preview d’édition lié à un autre Project Profile.")
    if preview.status == "NOTHING_TO_CHANGE":
        return {"format": TAXONOMY_FORMAT, "status": "NOTHING_TO_CHANGE", "profile_path": str(path), "changes": []}

    current = preview_taxonomy_edit(
        path,
        **{  # Re-plan the very same edit and require the project to be unchanged since review.
            f"{'knowledge_types' if item.section == 'knowledge' else 'entity_types' if item.section == 'entities' else 'relation_types'}": list(item.declared)
            for item in preview.changes
        },
    )
    if current.preview_hash != preview.preview_hash:
        raise TaxonomyError("Preview d’édition périmé : le Project Profile a changé depuis sa relecture.")

    _write_atomic(path, preview._content)
    try:
        load_profile(path)
    except (ProfileError, OSError, ValueError) as exc:
        raise TaxonomyError(f"Profile écrit mais invalide après édition : {exc}") from exc
    return {
        "format": TAXONOMY_FORMAT,
        "status": "APPLIED",
        "profile_path": str(path),
        "changes": [item.as_dict() for item in preview.changes],
        "preview_hash": preview.preview_hash,
    }


def _profile_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_symlink() or not path.is_file() or path.parent.is_symlink():
        raise TaxonomyError("Project Profile ou son répertoire est ambigu.")
    return path.resolve(strict=True)


def _current(profile: Mapping[str, Any], block: str, key: str) -> Sequence[Any]:
    section = profile.get(block)
    if not isinstance(section, Mapping):
        return ()
    value = section.get(key)
    return value if isinstance(value, (list, tuple)) else ()


def _normalize(section: str, values: Sequence[str]) -> tuple[str, ...]:
    """Accept only declarative identifiers, in the order given, without duplicates."""
    if not isinstance(values, (list, tuple)):
        raise TaxonomyError(f"Section `{section}` : une liste d’identifiants est attendue.")
    normalized: list[str] = []
    for item in values:
        if not isinstance(item, str) or DECLARATION_ID_RE.fullmatch(item.strip()) is None:
            raise TaxonomyError(
                f"Section `{section}` : identifiant déclaratif invalide `{item}` — majuscules, chiffres et « _ » attendus."
            )
        candidate = item.strip()
        if candidate in normalized:
            raise TaxonomyError(f"Section `{section}` : identifiant en double `{candidate}`.")
        normalized.append(candidate)
    if not normalized and section in _REQUIRED_SECTIONS:
        raise TaxonomyError(
            f"Section `{section}` vide refusée : un projet sans type de connaissance ne peut rien mémoriser."
        )
    return tuple(normalized)


def _usage(profile: Mapping[str, Any], path: Path) -> dict[str, dict[str, int]]:
    """Count, per declared type, what the memory already records under it.

    The store's identifiers are the lowercase form the Core derives from the declaration, so the
    count is looked up on that form and reported against the declaration the operator typed.
    A project whose memory does not exist yet simply has nothing to orphan.
    """
    try:
        workspace = resolve_workspace(profile, path)
        database = RuntimeLocator.from_workspace(profile, workspace).sqlite_path
    except (WorkspaceError, ProfileError, OSError, ValueError):
        return {}
    if database.is_symlink() or not database.is_file():
        return {}
    counts: dict[str, dict[str, int]] = {}
    try:
        connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True, timeout=5.0)
    except sqlite3.Error:
        return {}
    try:
        for section, (block, key, table, column) in _SECTIONS.items():
            section_counts: dict[str, int] = {}
            for declared in _current(profile, block, key):
                identifier = str(declared)
                stored = identifier.strip().lower().replace("_", "-")
                try:
                    row = connection.execute(
                        f"SELECT COUNT(*) FROM {table} WHERE {column} = ?", (stored,)  # noqa: S608 - table names are module constants
                    ).fetchone()
                except sqlite3.Error:
                    # A table the schema has not created yet records nothing under any type.
                    continue
                section_counts[identifier] = int(row[0]) if row else 0
            counts[section] = section_counts
    finally:
        connection.close()
    return counts


def _write_atomic(path: Path, content: str) -> None:
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, prefix=".taxonomy-", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except OSError as exc:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise TaxonomyError("Écriture atomique du Project Profile impossible.") from exc

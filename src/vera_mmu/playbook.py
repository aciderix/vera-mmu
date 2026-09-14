"""The universal core laws and the project's own playbook, loaded and hashed.

The Core fixes a small, non-negotiable kernel of laws. Everything else a project wants to
impose on its agents lives in its own `playbook.md`, which this module reads from the project
runtime, bounds, and hashes so the compiled MCP instructions can carry it verbatim.

The playbook is authored content, not canonical memory: reading it never writes to the store,
and its text is never interpreted — it is quoted into the generated instructions as-is.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from .store import MemoryStore, StoreError


PLAYBOOK_FORMAT = "vera-project-playbook/v1"
PLAYBOOK_FILE_NAME = "playbook.md"
MAX_PLAYBOOK_BYTES = 65_536
# The eight laws the specification places in the Core. A profile or a Domain Pack may add to
# them; none may weaken one, and the generated instructions always state all eight.
# Stated in the language the generated doctrine already used, so one section reads as one
# voice; a project's own playbook keeps whatever language that project writes in.
CORE_LAWS = (
    "Never present as proven what is not proven.",
    "Never silently rewrite history.",
    "Always preserve provenance.",
    "Always distinguish search from exact read.",
    "Always respect the declared policies.",
    "Always keep evidence separate from claims.",
    "Always stop loudly on critical uncertainty.",
    "Never bypass a gate.",
)


class PlaybookError(StoreError):
    """Raised when the project playbook is absent, oversized, ambiguous or unreadable."""


@dataclass(frozen=True)
class ProjectPlaybook:
    """One project's authored rules, bounded and hashed, alongside the Core laws."""

    format: str
    project_id: str
    playbook_hash: str
    text: str
    core_laws: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "format": self.format,
            "project_id": self.project_id,
            "playbook_hash": self.playbook_hash,
            "core_laws": list(self.core_laws),
        }


def playbook_path(store: MemoryStore) -> Path:
    """Resolve the playbook inside the project runtime, refusing anything ambiguous."""
    if not isinstance(store, MemoryStore):
        raise PlaybookError("Store invalide pour le playbook projet.")
    candidate = store.locator.runtime_dir / PLAYBOOK_FILE_NAME
    if candidate.is_symlink():
        raise PlaybookError("Playbook symlinké refusé : la règle du projet doit vivre dans son runtime.")
    if not candidate.exists() or not candidate.is_file():
        raise PlaybookError(f"Playbook projet absent : `{PLAYBOOK_FILE_NAME}` est attendu dans le runtime VERA.")
    return candidate


def compile_project_playbook(store: MemoryStore) -> ProjectPlaybook:
    """Read, bound and hash the project playbook without interpreting a single line.

    An absent or oversized playbook is a refusal rather than an empty section: the generated
    instructions must never silently drop the rules a project chose to impose (invariant I014).
    """
    source = playbook_path(store)
    try:
        raw = source.read_bytes()
    except OSError as exc:
        raise PlaybookError("Playbook projet illisible.") from exc
    if not raw.strip():
        raise PlaybookError("Playbook projet vide : déclarer au moins une règle de travail.")
    if len(raw) > MAX_PLAYBOOK_BYTES:
        raise PlaybookError(f"Playbook projet au-delà de {MAX_PLAYBOOK_BYTES} octets.")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PlaybookError("Playbook projet non décodable en UTF-8.") from exc
    return ProjectPlaybook(
        format=PLAYBOOK_FORMAT,
        project_id=store.identity.project_id,
        playbook_hash=sha256(raw).hexdigest(),
        text=text,
        core_laws=CORE_LAWS,
    )

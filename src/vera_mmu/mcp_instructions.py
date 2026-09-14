"""Compilation déterministe des instructions MCP à partir d’un manifeste vérifié.

Le texte compose exactement les cinq sections que la spécification impose : doctrine Core,
playbook du projet, règles de capabilities, résumé des policies et protocole de reprise. Il est
hashé et lié au Profile Hash, de sorte qu’une instruction ne puisse jamais décrire un projet,
une capability ou une règle qui ne sont plus les siens.

Le playbook est cité verbatim, jamais interprété : la doctrine du Core et les règles du projet
restent deux couches distinctes et lisibles séparément.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from .mcp_manifest import MCPManifest, MCPManifestError, verify_mcp_manifest
from .playbook import PlaybookError, compile_project_playbook
from .profile_resume import ProfileResumeError, profile_resume_requirements
from .project_catalogs import ProjectCatalogError, load_project_catalogs
from .store import MemoryStore, StoreError


INSTRUCTIONS_FORMAT = "vera-mcp-instructions/v1"
_POLICY_SECTIONS = ("filesystem", "network", "process", "git", "destructive", "promotion")


class MCPInstructionsError(StoreError):
    """Les instructions MCP ne peuvent pas être dérivées du snapshot courant."""


@dataclass(frozen=True)
class MCPInstructions:
    """Vue textuelle canonique, liée à un manifeste MCP précis et au Profile Hash."""

    format: str
    project_id: str
    profile_hash: str
    mcp_build_hash: str
    playbook_hash: str
    instructions_hash: str
    text: str


def _capability_lines(manifest: MCPManifest) -> tuple[str, ...]:
    return tuple(
        "- "
        + " | ".join(
            (
                item.capability_id,
                item.kind,
                item.runner_profile,
                item.network_policy,
                str(item.timeout_seconds),
                item.adapter_id,
            )
        )
        for item in manifest.capabilities
    )


def _policy_lines(store: MemoryStore) -> tuple[str, ...]:
    """Summarize the declared policy catalog without restating its file verbatim."""
    try:
        policies = load_project_catalogs(store.workspace.profile_path).policies
    except (ProjectCatalogError, OSError, ValueError) as exc:
        raise MCPInstructionsError("Catalogue de policies illisible pour les instructions MCP.") from exc
    lines: list[str] = []
    for section in _POLICY_SECTIONS:
        value = policies.get(section)
        if isinstance(value, dict):
            rendered = ", ".join(f"{key}={value[key]}" for key in sorted(value))
        elif isinstance(value, list):
            rendered = ", ".join(str(item) for item in value) or "none"
        elif value is None:
            continue
        else:
            rendered = str(value)
        lines.append(f"- {section}: {rendered}")
    if not lines:
        raise MCPInstructionsError("Catalogue de policies vide pour les instructions MCP.")
    return tuple(lines)


def _resume_lines(store: MemoryStore) -> tuple[str, ...]:
    try:
        requirements = profile_resume_requirements(store)
    except ProfileResumeError as exc:
        raise MCPInstructionsError("Contrat de reprise illisible pour les instructions MCP.") from exc
    return (
        "- On start, call `mmu_boot` then `mmu_get_resume_status`.",
        "- If a contract is armed, read `mmu_get_resume_brief` and answer with `mmu_acknowledge_resume`.",
        "- The resume dossier requires exactly these sections, bounded in characters:",
        *(
            f"    - {item.identifier} ({item.minimum_characters}-{item.maximum_characters})"
            for item in requirements
        ),
        "- Never fabricate an absent section: missing context is declared, not invented.",
    )


def compile_mcp_instructions(store: MemoryStore, manifest: MCPManifest) -> MCPInstructions:
    """Compile une doctrine MCP stable depuis un manifeste déjà attesté.

    Une instruction ne peut jamais décrire une capability, policy ou identité qui n’est plus
    celle du store : la vérification du manifeste précède toute mise en texte.
    """
    if not isinstance(store, MemoryStore):
        raise MCPInstructionsError("Store invalide pour les instructions MCP.")
    try:
        verify_mcp_manifest(store, manifest)
    except MCPManifestError as exc:
        raise MCPInstructionsError("Manifeste MCP invalide pour les instructions.") from exc
    project_id = manifest.project_identity.get("project_id")
    profile_hash = manifest.project_identity.get("profile_hash")
    if not isinstance(project_id, str) or not project_id or not isinstance(profile_hash, str) or not profile_hash:
        raise MCPInstructionsError("Identité projet incomplète pour les instructions MCP.")
    capability_lines = _capability_lines(manifest)
    if not capability_lines:
        raise MCPInstructionsError("Manifeste MCP sans capability pour les instructions.")
    try:
        playbook = compile_project_playbook(store)
    except PlaybookError as exc:
        raise MCPInstructionsError(f"Playbook projet indisponible pour les instructions MCP : {exc}") from exc

    lines = (
        "VERA-MMU MCP instructions v1",
        f"Project: {project_id}",
        f"Profile SHA-256: {profile_hash}",
        f"Manifest SHA-256: {manifest.mcp_build_hash}",
        f"Playbook SHA-256: {playbook.playbook_hash}",
        "",
        "== CORE DOCTRINE ==",
        "Universal laws; a profile or a pack may strengthen them, never weaken one:",
        *(f"{index}. {law}" for index, law in enumerate(playbook.core_laws, start=1)),
        "",
        "Operational consequences:",
        "- Treat the SQLite store, persisted evidence, policies and gates as the source of truth.",
        "- FIND is not READ; do not infer proof or success from a lookup or a message.",
        "- Only an admitted PASS evidence may support a proof or a passing gate.",
        "- Never accept a client-supplied command, path, stdout, stderr, exit code, score, verdict or artifact.",
        "- Call only the declared MCP tools and capabilities; errors, FAIL, SKIPPED, ERROR and UNKNOWN remain fail-closed.",
        "",
        "== PROJECT PLAYBOOK ==",
        "Rules this project imposes on its own agents, quoted verbatim from its runtime:",
        "",
        playbook.text.rstrip("\n"),
        "",
        "== CAPABILITY RULES ==",
        "Only these declared capabilities are executable (id | kind | runner | network | timeout_seconds | adapter):",
        *capability_lines,
        "The active server rejects a stale manifest, an adapter mismatch and any capability absent from this snapshot.",
        "",
        "== POLICY SUMMARY ==",
        "Decisions declared by this project's policy catalog:",
        *_policy_lines(store),
        "",
        "== RESUME PROTOCOL ==",
        *_resume_lines(store),
    )
    text = "\n".join(lines) + "\n"
    return MCPInstructions(
        format=INSTRUCTIONS_FORMAT,
        project_id=project_id,
        profile_hash=profile_hash,
        mcp_build_hash=manifest.mcp_build_hash,
        playbook_hash=playbook.playbook_hash,
        instructions_hash=sha256(text.encode("utf-8")).hexdigest(),
        text=text,
    )

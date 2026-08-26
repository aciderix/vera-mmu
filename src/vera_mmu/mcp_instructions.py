"""Compilation déterministe des instructions MCP à partir d’un manifeste vérifié.

Le texte est une vue dérivée du snapshot M5-B : il ne charge pas de playbook, de Pack, de
fichier ou de runtime. Les spécialisations de domaine pourront ajouter leur propre couche
attestée sans modifier cette doctrine universelle.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from .mcp_manifest import MCPManifest, MCPManifestError, verify_mcp_manifest
from .store import MemoryStore, StoreError


INSTRUCTIONS_FORMAT = "vera-mcp-instructions/v1"


class MCPInstructionsError(StoreError):
    """Les instructions MCP ne peuvent pas être dérivées du snapshot courant."""


@dataclass(frozen=True)
class MCPInstructions:
    """Vue textuelle canonique et liée à un manifeste MCP précis."""

    format: str
    project_id: str
    mcp_build_hash: str
    instructions_hash: str
    text: str


def _capability_line(manifest: MCPManifest) -> tuple[str, ...]:
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


def compile_mcp_instructions(store: MemoryStore, manifest: MCPManifest) -> MCPInstructions:
    """Compile une doctrine MCP stable depuis un manifeste déjà attesté.

    Une instruction ne peut jamais décrire une capability, policy ou identité qui n’est plus
    celle du store : la vérification M5-B précède toute mise en texte.
    """
    if not isinstance(store, MemoryStore):
        raise MCPInstructionsError("Store invalide pour les instructions MCP.")
    try:
        verify_mcp_manifest(store, manifest)
    except MCPManifestError as exc:
        raise MCPInstructionsError("Manifeste MCP invalide pour les instructions.") from exc
    project_id = manifest.project_identity.get("project_id")
    if not isinstance(project_id, str) or not project_id:
        raise MCPInstructionsError("Identité projet absente des instructions MCP.")
    capability_lines = _capability_line(manifest)
    if not capability_lines:
        raise MCPInstructionsError("Manifeste MCP sans capability pour les instructions.")
    lines = (
        "VERA-MMU MCP instructions v1",
        f"Project: {project_id}",
        f"Manifest SHA-256: {manifest.mcp_build_hash}",
        "",
        "Core doctrine:",
        "- Treat the SQLite store, persisted evidence, policies and gates as the source of truth.",
        "- FIND is not READ; do not infer proof or success from a lookup or a message.",
        "- Only an admitted PASS evidence may support a proof or a passing gate.",
        "- Never accept a client-supplied command, path, stdout, stderr, exit code, score, verdict or artifact.",
        "- Call only the declared MCP tools and capabilities; errors, FAIL, SKIPPED, ERROR and UNKNOWN remain fail-closed.",
        "",
        "Declared capabilities (id | kind | runner | network | timeout_seconds | adapter):",
        *capability_lines,
        "",
        "The active server rejects a stale manifest, an adapter mismatch and any capability absent from this snapshot.",
    )
    text = "\n".join(lines) + "\n"
    return MCPInstructions(
        format=INSTRUCTIONS_FORMAT,
        project_id=project_id,
        mcp_build_hash=manifest.mcp_build_hash,
        instructions_hash=sha256(text.encode("utf-8")).hexdigest(),
        text=text,
    )

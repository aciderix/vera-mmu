"""Prévisualisation déterministe d’une configuration MCP project-localisée.

Ce module ne modifie pas ``.mcp.json`` et n’installe aucun hook. Il rend visible, sous le
runtime VERA, la configuration standard que pourra appliquer un installateur futur après
validation explicite. Le serveur configuré est l’entry point générique, donc fail-closed
sans hôte de Pack explicitement assemblé.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from .mcp_instructions import MCPInstructions, MCPInstructionsError, compile_mcp_instructions
from .mcp_manifest import MCPManifest, MCPManifestError, verify_mcp_manifest
from .store import MemoryStore, StoreError


INTEGRATION_FORMAT = "vera-mcp-integration/v1"


class MCPIntegrationError(StoreError):
    """La prévisualisation d’intégration MCP ne peut pas être compilée ou écrite."""


@dataclass(frozen=True)
class MCPIntegration:
    """Configuration MCP canonique, liée au manifest et aux instructions courants."""

    format: str
    project_id: str
    mcp_build_hash: str
    instructions_hash: str
    config_hash: str
    json_text: str


def _relative_profile_argument(store: MemoryStore) -> str:
    try:
        relative_profile = store.workspace.profile_path.relative_to(store.workspace.project_root).as_posix()
    except ValueError as exc:
        raise MCPIntegrationError("Le Project Profile doit rester dans le projet pour une intégration locale.") from exc
    if not relative_profile or relative_profile == "." or relative_profile.startswith("../"):
        raise MCPIntegrationError("Chemin relatif de Project Profile invalide.")
    return "${CLAUDE_PROJECT_DIR:-.}/" + relative_profile


def compile_mcp_integration(
    store: MemoryStore,
    manifest: MCPManifest,
    instructions: MCPInstructions,
) -> MCPIntegration:
    """Compile une config MCP JSON standard depuis les snapshots attestés.

    La config décrit l’entry point générique ``vmmu-mcp``. Elle ne fournit ni shell,
    chemin d’exécutable, adapter, verdict ni secret; elle reste donc sûre même avant le
    futur installateur de runtime Pack.
    """
    if not isinstance(store, MemoryStore):
        raise MCPIntegrationError("Store invalide pour l’intégration MCP.")
    if not isinstance(instructions, MCPInstructions):
        raise MCPIntegrationError("Instructions MCP invalides pour l’intégration.")
    try:
        verify_mcp_manifest(store, manifest)
        expected_instructions = compile_mcp_instructions(store, manifest)
    except (MCPManifestError, MCPInstructionsError) as exc:
        raise MCPIntegrationError("Snapshots MCP invalides pour l’intégration.") from exc
    if instructions != expected_instructions:
        raise MCPIntegrationError("Instructions MCP périmées, altérées ou liées à un autre manifeste.")
    project_id = manifest.project_identity.get("project_id")
    if not isinstance(project_id, str) or not project_id:
        raise MCPIntegrationError("Identité projet absente de l’intégration MCP.")
    server_id = f"vera-mmu-{project_id}"
    payload = {
        "mcpServers": {
            server_id: {
                "args": ["--profile", _relative_profile_argument(store)],
                "command": "vmmu-mcp",
                "env": {
                    "VERA_MCP_BUILD_HASH": manifest.mcp_build_hash,
                    "VERA_MCP_INSTRUCTIONS_HASH": instructions.instructions_hash,
                    "VERA_PROJECT_ID": project_id,
                },
            }
        }
    }
    json_text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    return MCPIntegration(
        format=INTEGRATION_FORMAT,
        project_id=project_id,
        mcp_build_hash=manifest.mcp_build_hash,
        instructions_hash=instructions.instructions_hash,
        config_hash=sha256(json_text.encode("utf-8")).hexdigest(),
        json_text=json_text,
    )


def write_mcp_integration_preview(store: MemoryStore, integration: MCPIntegration) -> Path:
    """Écrit une prévisualisation atomique et non-écrasante sous le runtime du projet."""
    if not isinstance(store, MemoryStore):
        raise MCPIntegrationError("Store invalide pour l’écriture d’intégration MCP.")
    if not isinstance(integration, MCPIntegration):
        raise MCPIntegrationError("Prévisualisation MCP invalide.")
    if integration.project_id != store.identity.project_id:
        raise MCPIntegrationError("Prévisualisation MCP liée à un autre projet.")
    target_dir = store.locator.runtime_dir / "generated"
    target = target_dir / "mcp.json"
    try:
        target_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(integration.json_text)
    except FileExistsError:
        raise
    except OSError as exc:
        raise MCPIntegrationError("Écriture de prévisualisation MCP impossible.") from exc
    return target

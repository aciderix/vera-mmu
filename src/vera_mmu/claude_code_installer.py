"""Installateur MCP Claude Code opt-in, attesté et limité à ``.mcp.json``.

Ce module applique uniquement la configuration MCP M5-F après confirmation explicite et
vérification des snapshots M5-B/E/F/G/H. Il ne crée aucun hook, script ou fichier
``.claude``. Une entrée serveur existante est préservée si elle est identique, sinon le
conflit est refusé sans écriture.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Mapping

from .claude_code_integration import (
    ClaudeCodeIntegrationError,
    ClaudeCodeIntegrationPlan,
    compile_claude_code_integration_plan,
)
from .mcp_hooks import MCPHookPlan, MCPHookPlanError, compile_mcp_hook_plan
from .mcp_instructions import MCPInstructions, MCPInstructionsError, compile_mcp_instructions
from .mcp_integration import MCPIntegration, MCPIntegrationError, compile_mcp_integration
from .mcp_manifest import MCPManifest, MCPManifestError, verify_mcp_manifest
from .store import MemoryStore, StoreError


class ClaudeCodeInstallError(StoreError):
    """L’installation MCP Claude Code ne peut pas être effectuée en sécurité."""


@dataclass(frozen=True)
class ClaudeCodeInstallResult:
    """Résultat borné de l’unique write-path M5-I."""

    status: str
    path: Path
    server_id: str
    config_hash: str


def _verified_snapshots(
    store: MemoryStore,
    manifest: MCPManifest,
    instructions: MCPInstructions,
    integration: MCPIntegration,
    hooks: MCPHookPlan,
    plan: ClaudeCodeIntegrationPlan,
) -> tuple[MCPIntegration, ClaudeCodeIntegrationPlan]:
    if not isinstance(store, MemoryStore):
        raise ClaudeCodeInstallError("Store invalide pour l’installation Claude Code.")
    if not isinstance(instructions, MCPInstructions) or not isinstance(integration, MCPIntegration):
        raise ClaudeCodeInstallError("Snapshots MCP invalides pour l’installation Claude Code.")
    if not isinstance(hooks, MCPHookPlan) or not isinstance(plan, ClaudeCodeIntegrationPlan):
        raise ClaudeCodeInstallError("Plan de hooks ou plan hôte invalides pour l’installation.")
    try:
        verify_mcp_manifest(store, manifest)
        expected_instructions = compile_mcp_instructions(store, manifest)
        expected_integration = compile_mcp_integration(store, manifest, expected_instructions)
        expected_hooks = compile_mcp_hook_plan(store, manifest, expected_instructions, expected_integration)
        expected_plan = compile_claude_code_integration_plan(
            store, manifest, expected_instructions, expected_integration, expected_hooks
        )
    except (
        MCPManifestError,
        MCPInstructionsError,
        MCPIntegrationError,
        MCPHookPlanError,
        ClaudeCodeIntegrationError,
    ) as exc:
        raise ClaudeCodeInstallError("Snapshots MCP invalides pour l’installation Claude Code.") from exc
    if instructions != expected_instructions:
        raise ClaudeCodeInstallError("Instructions MCP périmées, altérées ou étrangères.")
    if integration != expected_integration:
        raise ClaudeCodeInstallError("Configuration MCP périmée, altérée ou étrangère.")
    if hooks != expected_hooks:
        raise ClaudeCodeInstallError("Plan de hooks MCP périmé, altéré ou étranger.")
    if plan != expected_plan:
        raise ClaudeCodeInstallError("Plan Claude Code périmé, altéré ou étranger.")
    return expected_integration, expected_plan


def _target(store: MemoryStore) -> Path:
    root = store.workspace.project_root
    target = root / ".mcp.json"
    if target.parent != root:
        raise ClaudeCodeInstallError("Cible d’installation MCP hors racine projet.")
    if target.is_symlink():
        raise ClaudeCodeInstallError("La cible .mcp.json ne peut pas être un lien symbolique.")
    return target


def _load_existing(target: Path) -> dict[str, Any]:
    if not target.exists():
        return {}
    if not target.is_file():
        raise ClaudeCodeInstallError("La cible .mcp.json doit être un fichier régulier.")
    try:
        raw = target.read_text(encoding="utf-8")
        parsed = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClaudeCodeInstallError("La cible .mcp.json existante n’est pas un JSON lisible.") from exc
    if not isinstance(parsed, dict):
        raise ClaudeCodeInstallError("La cible .mcp.json doit contenir un objet JSON.")
    servers = parsed.get("mcpServers", {})
    if not isinstance(servers, dict):
        raise ClaudeCodeInstallError("mcpServers existant doit être un objet JSON.")
    return parsed


def _generated_server(integration: MCPIntegration) -> tuple[str, dict[str, Any]]:
    try:
        payload = json.loads(integration.json_text)
    except json.JSONDecodeError as exc:
        raise ClaudeCodeInstallError("Configuration MCP attestée illisible.") from exc
    if not isinstance(payload, dict) or set(payload) != {"mcpServers"}:
        raise ClaudeCodeInstallError("Configuration MCP attestée hors format fermé.")
    servers = payload.get("mcpServers")
    if not isinstance(servers, dict) or len(servers) != 1:
        raise ClaudeCodeInstallError("Configuration MCP attestée doit déclarer un seul serveur.")
    server_id, server = next(iter(servers.items()))
    if not isinstance(server_id, str) or not server_id or not isinstance(server, dict):
        raise ClaudeCodeInstallError("Serveur MCP attesté invalide.")
    return server_id, server


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _atomic_write(target: Path, text: str) -> None:
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=target.parent, prefix=".vera-mcp-", suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, target)
    except OSError as exc:
        try:
            temporary.unlink(missing_ok=True)  # type: ignore[name-defined]
        except (OSError, UnboundLocalError):
            pass
        raise ClaudeCodeInstallError("Écriture atomique de .mcp.json impossible.") from exc


def install_claude_code_mcp(
    store: MemoryStore,
    manifest: MCPManifest,
    instructions: MCPInstructions,
    integration: MCPIntegration,
    hooks: MCPHookPlan,
    plan: ClaudeCodeIntegrationPlan,
    *,
    confirm: bool,
) -> ClaudeCodeInstallResult:
    """Installe seulement le serveur MCP attesté après confirmation explicite.

    Aucun hook n’est traduit ni installé. Les autres serveurs et clés JSON sont préservés.
    """
    if confirm is not True:
        raise ClaudeCodeInstallError("Installation MCP refusée sans confirmation explicite.")
    verified_integration, verified_plan = _verified_snapshots(store, manifest, instructions, integration, hooks, plan)
    target = _target(store)
    existing = _load_existing(target)
    server_id, server = _generated_server(verified_integration)
    servers = existing.get("mcpServers", {})
    if not isinstance(servers, dict):
        raise ClaudeCodeInstallError("mcpServers existant doit être un objet JSON.")
    if server_id in servers:
        if servers[server_id] != server:
            raise ClaudeCodeInstallError("Conflit : le serveur MCP VERA existant diffère du snapshot attesté.")
        return ClaudeCodeInstallResult("UNCHANGED", target, server_id, verified_plan.config_hash)
    merged = dict(existing)
    merged_servers = dict(servers)
    merged_servers[server_id] = server
    merged["mcpServers"] = merged_servers
    _atomic_write(target, _canonical_json(merged))
    return ClaudeCodeInstallResult("INSTALLED", target, server_id, verified_plan.config_hash)

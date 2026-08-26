"""Plan de revue pour l’intégration Claude Code dérivé des snapshots MCP attestés.

Ce module n’écrit ni ``.mcp.json`` ni ``.claude``. Il expose à un futur installateur l’unique
cible MCP standard et rend explicite qu’un hook déclaratif ne peut pas devenir une commande
sans un adapter exécutable supplémentaire et testé.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from .mcp_hooks import MCPHookPlan, MCPHookPlanError, compile_mcp_hook_plan
from .mcp_instructions import MCPInstructions, MCPInstructionsError, compile_mcp_instructions
from .mcp_integration import MCPIntegration, MCPIntegrationError, compile_mcp_integration
from .mcp_manifest import MCPManifest, MCPManifestError, verify_mcp_manifest
from .store import MemoryStore, StoreError


CLAUDE_CODE_PLAN_FORMAT = "vera-claude-code-integration/v1"


class ClaudeCodeIntegrationError(StoreError):
    """Le plan Claude Code ne peut pas être compilé ou écrit de façon sûre."""


@dataclass(frozen=True)
class ClaudeCodeIntegrationPlan:
    """Plan de revue project-bound, non installable et non exécutable par lui-même."""

    format: str
    project_id: str
    mcp_build_hash: str
    instructions_hash: str
    config_hash: str
    hook_plan_hash: str
    plan_hash: str
    json_text: str


def compile_claude_code_integration_plan(
    store: MemoryStore,
    manifest: MCPManifest,
    instructions: MCPInstructions,
    integration: MCPIntegration,
    hooks: MCPHookPlan,
) -> ClaudeCodeIntegrationPlan:
    """Traduit les snapshots attestés en plan de revue Claude Code, sans write-path projet."""
    if not isinstance(store, MemoryStore):
        raise ClaudeCodeIntegrationError("Store invalide pour le plan Claude Code.")
    if not isinstance(instructions, MCPInstructions) or not isinstance(integration, MCPIntegration):
        raise ClaudeCodeIntegrationError("Snapshots MCP invalides pour le plan Claude Code.")
    if not isinstance(hooks, MCPHookPlan):
        raise ClaudeCodeIntegrationError("Plan de hooks MCP invalide pour le plan Claude Code.")
    try:
        verify_mcp_manifest(store, manifest)
        expected_instructions = compile_mcp_instructions(store, manifest)
        expected_integration = compile_mcp_integration(store, manifest, expected_instructions)
        expected_hooks = compile_mcp_hook_plan(store, manifest, expected_instructions, expected_integration)
    except (MCPManifestError, MCPInstructionsError, MCPIntegrationError, MCPHookPlanError) as exc:
        raise ClaudeCodeIntegrationError("Snapshots MCP invalides pour le plan Claude Code.") from exc
    if instructions != expected_instructions:
        raise ClaudeCodeIntegrationError("Instructions MCP périmées, altérées ou étrangères.")
    if integration != expected_integration:
        raise ClaudeCodeIntegrationError("Configuration MCP périmée, altérée ou étrangère.")
    if hooks != expected_hooks:
        raise ClaudeCodeIntegrationError("Plan de hooks MCP périmé, altéré ou étranger.")
    project_id = manifest.project_identity.get("project_id")
    if not isinstance(project_id, str) or not project_id:
        raise ClaudeCodeIntegrationError("Identité projet absente du plan Claude Code.")
    payload = {
        "claudeCodeIntegration": {
            "hooks": {
                "SessionStart": {
                    "reason": "DECLARATIVE_HOOK_REQUIRES_EXECUTABLE_ADAPTER",
                    "status": "UNTRANSLATED",
                }
            },
            "installation": {"mode": "REVIEW_REQUIRED", "writes": []},
            "mcpConfig": {"content_sha256": integration.config_hash, "target": ".mcp.json"},
        }
    }
    json_text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    return ClaudeCodeIntegrationPlan(
        format=CLAUDE_CODE_PLAN_FORMAT,
        project_id=project_id,
        mcp_build_hash=manifest.mcp_build_hash,
        instructions_hash=instructions.instructions_hash,
        config_hash=integration.config_hash,
        hook_plan_hash=hooks.hook_plan_hash,
        plan_hash=sha256(json_text.encode("utf-8")).hexdigest(),
        json_text=json_text,
    )


def write_claude_code_integration_preview(store: MemoryStore, plan: ClaudeCodeIntegrationPlan) -> Path:
    """Écrit le plan de revue en création exclusive sous le runtime du projet."""
    if not isinstance(store, MemoryStore):
        raise ClaudeCodeIntegrationError("Store invalide pour l’écriture du plan Claude Code.")
    if not isinstance(plan, ClaudeCodeIntegrationPlan):
        raise ClaudeCodeIntegrationError("Plan Claude Code invalide.")
    if plan.project_id != store.identity.project_id:
        raise ClaudeCodeIntegrationError("Plan Claude Code lié à un autre projet.")
    target_dir = store.locator.runtime_dir / "generated"
    target = target_dir / "claude-code-integration.json"
    try:
        target_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(plan.json_text)
    except FileExistsError:
        raise
    except OSError as exc:
        raise ClaudeCodeIntegrationError("Écriture du plan Claude Code impossible.") from exc
    return target

"""Plan déclaratif de hooks de session dérivé des snapshots MCP attestés.

Le plan décrit seulement un besoin d’intégration à un hôte compatible. Il ne contient aucune
commande, script, chemin d’exécutable ou action de reprise : ces éléments relèvent d’un
adapter d’intégration et d’un installateur explicitement validés dans une tranche ultérieure.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from .mcp_instructions import MCPInstructions, MCPInstructionsError, compile_mcp_instructions
from .mcp_integration import MCPIntegration, MCPIntegrationError, compile_mcp_integration
from .mcp_manifest import MCPManifest, MCPManifestError, verify_mcp_manifest
from .store import MemoryStore, StoreError


HOOK_PLAN_FORMAT = "vera-mcp-hooks/v1"


class MCPHookPlanError(StoreError):
    """Le plan de hook MCP ne peut pas être compilé ou écrit de façon sûre."""


@dataclass(frozen=True)
class MCPHookPlan:
    """Plan de cycle de session attesté mais non exécutable par lui-même."""

    format: str
    project_id: str
    mcp_build_hash: str
    instructions_hash: str
    config_hash: str
    hook_plan_hash: str
    json_text: str


def compile_mcp_hook_plan(
    store: MemoryStore,
    manifest: MCPManifest,
    instructions: MCPInstructions,
    integration: MCPIntegration,
) -> MCPHookPlan:
    """Compile un seul événement SessionStart sans commande ni installation.

    L’événement n’est pas un hook Claude exécutable. Il indique seulement à un futur adapter
    qu’il devra livrer les instructions MCP attestées lors de l’ouverture d’une session.
    """
    if not isinstance(store, MemoryStore):
        raise MCPHookPlanError("Store invalide pour le plan de hooks MCP.")
    if not isinstance(instructions, MCPInstructions) or not isinstance(integration, MCPIntegration):
        raise MCPHookPlanError("Snapshots d’instructions ou d’intégration invalides.")
    try:
        verify_mcp_manifest(store, manifest)
        expected_instructions = compile_mcp_instructions(store, manifest)
        expected_integration = compile_mcp_integration(store, manifest, expected_instructions)
    except (MCPManifestError, MCPInstructionsError, MCPIntegrationError) as exc:
        raise MCPHookPlanError("Snapshots MCP invalides pour le plan de hooks.") from exc
    if instructions != expected_instructions:
        raise MCPHookPlanError("Instructions MCP périmées, altérées ou étrangères.")
    if integration != expected_integration:
        raise MCPHookPlanError("Configuration MCP périmée, altérée ou étrangère.")
    project_id = manifest.project_identity.get("project_id")
    if not isinstance(project_id, str) or not project_id:
        raise MCPHookPlanError("Identité projet absente du plan de hooks MCP.")
    payload = {
        "hookPlan": {
            "SessionStart": {
                "delivery": "HOST_ADAPTER_REQUIRED",
                "instruction_source": "ATTESTED_MCP_INSTRUCTIONS",
                "mode": "DECLARATIVE_ONLY",
            }
        }
    }
    json_text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    return MCPHookPlan(
        format=HOOK_PLAN_FORMAT,
        project_id=project_id,
        mcp_build_hash=manifest.mcp_build_hash,
        instructions_hash=instructions.instructions_hash,
        config_hash=integration.config_hash,
        hook_plan_hash=sha256(json_text.encode("utf-8")).hexdigest(),
        json_text=json_text,
    )


def write_mcp_hook_plan_preview(store: MemoryStore, plan: MCPHookPlan) -> Path:
    """Écrit le plan en création exclusive sous le runtime, sans configurer d’hôte."""
    if not isinstance(store, MemoryStore):
        raise MCPHookPlanError("Store invalide pour l’écriture du plan de hooks.")
    if not isinstance(plan, MCPHookPlan):
        raise MCPHookPlanError("Plan de hooks MCP invalide.")
    if plan.project_id != store.identity.project_id:
        raise MCPHookPlanError("Plan de hooks MCP lié à un autre projet.")
    target_dir = store.locator.runtime_dir / "generated"
    target = target_dir / "hooks.json"
    try:
        target_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(plan.json_text)
    except FileExistsError:
        raise
    except OSError as exc:
        raise MCPHookPlanError("Écriture du plan de hooks MCP impossible.") from exc
    return target

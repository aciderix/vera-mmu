"""Cloud planning and preinstalled-runtime diagnosis for Claude Code.

M5-M.1 deliberately compiles and observes only.  It does not install packages, access the
network, launch a hook, write user settings, inspect secret values, or claim live-cloud readiness.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import shutil
from typing import Callable

from .claude_code_integration import ClaudeCodeIntegrationError, ClaudeCodeIntegrationPlan, compile_claude_code_integration_plan
from .claude_code_local import ClaudeCodeLocalError, ClaudeCodeLocalPlan, compile_claude_code_local_plan
from .lifecycle_adapters import LifecycleAdapterPlan, compile_lifecycle_adapter_plan
from .mcp_hooks import MCPHookPlan, MCPHookPlanError, compile_mcp_hook_plan
from .mcp_instructions import MCPInstructions, MCPInstructionsError, compile_mcp_instructions
from .mcp_integration import MCPIntegration, MCPIntegrationError, compile_mcp_integration
from .mcp_manifest import MCPManifest, MCPManifestError, compile_mcp_manifest, verify_mcp_manifest
from .store import MemoryStore, StoreError


CLAUDE_CODE_CLOUD_FORMAT = "vera-claude-code-cloud/v1"
PREINSTALLED_PROVIDER = "PREINSTALLED_VERA"
CLOUD_ENVIRONMENT = "CLAUDE_CODE_CLOUD"
CLOUD_MCP_ENTRYPOINT = "vmmu-claude-code-cloud-mcp"
_TRUST_STATUSES = frozenset(("TRUST_PENDING", "TRUSTED", "DISABLED", "UNVERIFIABLE"))


class ClaudeCodeCloudError(StoreError):
    """A Claude Code cloud plan or observation cannot be accepted safely."""


@dataclass(frozen=True)
class ClaudeCodeCloudPlan:
    """Canonical cloud declaration linked to all local/lifecycle snapshots."""

    format: str
    project_id: str
    mcp_build_hash: str
    instructions_hash: str
    config_hash: str
    hook_plan_hash: str
    review_plan_hash: str
    lifecycle_plan_hash: str
    local_plan_hash: str
    plan_hash: str
    json_text: str


@dataclass(frozen=True)
class ClaudeCodeCloudObservation:
    """Host-provided non-secret cloud facts; values are validated before diagnosis."""

    environment: str
    trust_status: str


@dataclass(frozen=True)
class ClaudeCodeCloudDoctorReport:
    """Read-only report for the M5-M.1 preinstalled-runtime mode."""

    status: str
    checks: tuple[tuple[str, str], ...]
    install_actions: tuple[str, ...]


def compile_claude_code_cloud_plan(
    store: MemoryStore,
    manifest: MCPManifest,
    instructions: MCPInstructions,
    integration: MCPIntegration,
    hooks: MCPHookPlan,
    review: ClaudeCodeIntegrationPlan,
    lifecycle: LifecycleAdapterPlan,
    local: ClaudeCodeLocalPlan,
    *,
    runtime_provider: str = PREINSTALLED_PROVIDER,
) -> ClaudeCodeCloudPlan:
    """Compile a non-sensitive cloud plan for an already provisioned VERA runtime."""
    if not isinstance(store, MemoryStore):
        raise ClaudeCodeCloudError("Store invalide pour le plan Claude cloud.")
    if runtime_provider != PREINSTALLED_PROVIDER:
        raise ClaudeCodeCloudError("M5-M.1 n’autorise que le provider runtime préinstallé.")
    try:
        verify_mcp_manifest(store, manifest)
        expected_instructions = compile_mcp_instructions(store, manifest)
        expected_integration = compile_mcp_integration(store, manifest, expected_instructions)
        expected_hooks = compile_mcp_hook_plan(store, manifest, expected_instructions, expected_integration)
        expected_review = compile_claude_code_integration_plan(
            store, manifest, expected_instructions, expected_integration, expected_hooks
        )
        expected_lifecycle = compile_lifecycle_adapter_plan(
            store,
            manifest,
            adapter_id="claude-code-local-v1",
            adapter_version="1.0.0",
            maximum_guard_mode="HARD",
        )
        expected_local = compile_claude_code_local_plan(
            store,
            manifest,
            expected_instructions,
            expected_integration,
            expected_hooks,
            expected_review,
            expected_lifecycle,
        )
    except (
        MCPManifestError,
        MCPInstructionsError,
        MCPIntegrationError,
        MCPHookPlanError,
        ClaudeCodeIntegrationError,
        ClaudeCodeLocalError,
        StoreError,
    ) as exc:
        raise ClaudeCodeCloudError("Snapshots invalides pour le plan Claude cloud.") from exc
    if (
        instructions != expected_instructions
        or integration != expected_integration
        or hooks != expected_hooks
        or review != expected_review
        or lifecycle != expected_lifecycle
        or local != expected_local
    ):
        raise ClaudeCodeCloudError("Snapshot Claude cloud périmé, altéré ou étranger.")
    server_id, profile_argument = _server_identity(integration)
    payload = {
        "claudeCodeCloud": {
            "localPlan": {"sha256": local.plan_hash},
            "mcpServer": {
                "args": ["--profile", profile_argument],
                "command": CLOUD_MCP_ENTRYPOINT,
                "env": {
                    "VERA_CLAUDE_CODE_CLOUD": "1",
                    "VERA_MCP_BUILD_HASH": manifest.mcp_build_hash,
                    "VERA_MCP_INSTRUCTIONS_HASH": instructions.instructions_hash,
                    "VERA_PROJECT_ID": store.identity.project_id,
                },
                "id": server_id,
            },
            "runtime": {"network": "FORBIDDEN", "provider": PREINSTALLED_PROVIDER},
            "secrets": {"mode": "EXTERNAL_ONLY", "requirements": []},
            "trust": {"mode": "PREVIEW_ONLY", "target": "$HOME/.claude/settings.json"},
        }
    }
    json_text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    return ClaudeCodeCloudPlan(
        format=CLAUDE_CODE_CLOUD_FORMAT,
        project_id=store.identity.project_id,
        mcp_build_hash=manifest.mcp_build_hash,
        instructions_hash=instructions.instructions_hash,
        config_hash=integration.config_hash,
        hook_plan_hash=hooks.hook_plan_hash,
        review_plan_hash=review.plan_hash,
        lifecycle_plan_hash=lifecycle.lifecycle_plan_hash,
        local_plan_hash=local.plan_hash,
        plan_hash=sha256(json_text.encode("utf-8")).hexdigest(),
        json_text=json_text,
    )


def inspect_claude_code_cloud(
    store: MemoryStore,
    manifest: MCPManifest,
    instructions: MCPInstructions,
    integration: MCPIntegration,
    hooks: MCPHookPlan,
    review: ClaudeCodeIntegrationPlan,
    lifecycle: LifecycleAdapterPlan,
    local: ClaudeCodeLocalPlan,
    plan: ClaudeCodeCloudPlan,
    *,
    observation: ClaudeCodeCloudObservation,
    command_lookup: Callable[[str], str | None] = shutil.which,
) -> ClaudeCodeCloudDoctorReport:
    """Diagnose only declared preinstalled runtime and host trust facts, with no side effects."""
    expected = compile_claude_code_cloud_plan(store, manifest, instructions, integration, hooks, review, lifecycle, local)
    if plan != expected:
        raise ClaudeCodeCloudError("Plan Claude cloud périmé, altéré ou étranger.")
    if not isinstance(observation, ClaudeCodeCloudObservation):
        raise ClaudeCodeCloudError("Observation Claude cloud invalide.")
    if observation.environment != CLOUD_ENVIRONMENT:
        raise ClaudeCodeCloudError("Observation hors environnement Claude Code cloud.")
    if observation.trust_status not in _TRUST_STATUSES:
        raise ClaudeCodeCloudError("Statut de trust Claude cloud invalide.")
    entrypoint = command_lookup(CLOUD_MCP_ENTRYPOINT)
    checks = (
        ("environment", "PASS"),
        ("runtime_provider", "PASS"),
        ("runtime_entrypoint", "PASS" if entrypoint else "MISSING"),
        ("trust", observation.trust_status),
        ("write_path", "NOT_DELIVERED"),
        ("network", "FORBIDDEN"),
        ("secrets", "EXTERNAL_ONLY"),
    )
    if not entrypoint:
        return ClaudeCodeCloudDoctorReport("RUNTIME_MISSING", checks, ())
    if observation.trust_status == "DISABLED":
        return ClaudeCodeCloudDoctorReport("DISABLED", checks, ())
    if observation.trust_status == "TRUST_PENDING":
        return ClaudeCodeCloudDoctorReport("TRUST_PENDING", checks, ())
    if observation.trust_status == "UNVERIFIABLE":
        return ClaudeCodeCloudDoctorReport("UNVERIFIABLE", checks, ())
    return ClaudeCodeCloudDoctorReport("RUNTIME_READY", checks, ())


def _server_identity(integration: MCPIntegration) -> tuple[str, str]:
    try:
        payload = json.loads(integration.json_text)
        servers = payload["mcpServers"]
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ClaudeCodeCloudError("Configuration MCP attestée illisible.") from exc
    if not isinstance(servers, dict) or len(servers) != 1:
        raise ClaudeCodeCloudError("Configuration MCP attestée doit contenir un serveur unique.")
    server_id, server = next(iter(servers.items()))
    if not isinstance(server_id, str) or not isinstance(server, dict):
        raise ClaudeCodeCloudError("Serveur MCP attesté invalide.")
    args = server.get("args")
    if not isinstance(args, list) or len(args) != 2 or args[0] != "--profile" or not isinstance(args[1], str):
        raise ClaudeCodeCloudError("Argument de profil MCP attesté invalide.")
    return server_id, args[1]

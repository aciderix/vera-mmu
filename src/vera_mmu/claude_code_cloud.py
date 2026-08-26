"""Cloud planning, staged lifecycle, and project-local host configuration for Claude Code.

M5-M.1 deliberately compiled and observed only; M5-M.2 added runtime-confined staging/hook/MCP;
M5-M.3a adds an explicitly confirmed project-local configuration merge.  This module never
installs packages, accesses the network, reads or writes user settings, inspects secret values,
or claims live-cloud readiness.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import sys
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Mapping, Sequence

from .claude_code_integration import ClaudeCodeIntegrationError, ClaudeCodeIntegrationPlan, compile_claude_code_integration_plan
from .claude_code_local import ClaudeCodeLocalError, ClaudeCodeLocalPlan, compile_claude_code_local_plan
from .lifecycle_adapters import LifecycleAdapterPlan, LifecycleAdapterRegistry, compile_lifecycle_adapter_plan
from .mcp_hooks import MCPHookPlan, MCPHookPlanError, compile_mcp_hook_plan
from .mcp_instructions import MCPInstructions, MCPInstructionsError, compile_mcp_instructions
from .mcp_integration import MCPIntegration, MCPIntegrationError, compile_mcp_integration
from .mcp_manifest import MCPManifest, MCPManifestError, compile_mcp_manifest, verify_mcp_manifest
from .mcp_server import DenyRuntimeAdapter, create_server
from .session_lifecycle import GuardDecision, ResumeDossierService, ResumeGuardService, ResumeSectionRequirement
from .store import MemoryStore, StoreError


CLAUDE_CODE_CLOUD_FORMAT = "vera-claude-code-cloud/v1"
PREINSTALLED_PROVIDER = "PREINSTALLED_VERA"
CLOUD_ENVIRONMENT = "CLAUDE_CODE_CLOUD"
CLOUD_MCP_ENTRYPOINT = "vmmu-claude-code-cloud-mcp"
CLOUD_HOOK_ENTRYPOINT = "vmmu-claude-code-cloud-hook"
CLAUDE_CODE_CLOUD_ADAPTER_ID = "claude-code-cloud-v1"
CLAUDE_CODE_CLOUD_ADAPTER_VERSION = "1.0.0"
CLAUDE_CODE_CLOUD_MAXIMUM_GUARD_MODE = "HARD"
CLOUD_RUNTIME_FORMAT = "vera-claude-code-cloud-runtime/v1"
CLOUD_HOST_CONFIG_FORMAT = "vera-claude-code-cloud-host-config/v1"
CLOUD_CONFIG_ENTRYPOINT = "vmmu-claude-code-cloud-config"
_CLOUD_USER_SCOPE_TARGET = "$HOME/.claude/settings.json"
_EVENTS = ("SessionStart", "PreToolUse", "PostToolUse", "PreCompact", "PostCompact", "Stop")
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


@dataclass(frozen=True)
class ClaudeCodeCloudStageResult:
    """Result of explicit project-runtime staging, never of trust or cloud setup."""

    status: str
    state_path: Path
    plan_hash: str


@dataclass(frozen=True)
class ClaudeCodeCloudHostConfigPreview:
    """Attested project-local host configuration; user-scope trust is deliberately absent."""

    status: str
    settings_path: Path
    mcp_path: Path
    state_path: Path
    settings_json_text: str
    mcp_json_text: str
    plan_hash: str
    user_scope_target: str
    user_scope_status: str


@dataclass(frozen=True)
class ClaudeCodeCloudHostConfigApplyResult:
    """Result of a confirmed project-local host configuration write only."""

    status: str
    settings_path: Path
    mcp_path: Path
    state_path: Path
    plan_hash: str
    user_scope_status: str


@dataclass(frozen=True)
class _CloudRuntime:
    manifest: MCPManifest
    instructions: MCPInstructions
    lifecycle: LifecycleAdapterPlan
    plan: ClaudeCodeCloudPlan


class ClaudeCodeCloudSessionAdapter:
    """Resolve the single staged cloud session; no client controls its identity."""

    adapter_id = CLAUDE_CODE_CLOUD_ADAPTER_ID
    adapter_version = CLAUDE_CODE_CLOUD_ADAPTER_VERSION
    maximum_guard_mode = CLAUDE_CODE_CLOUD_MAXIMUM_GUARD_MODE

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def session_identity(self) -> str | None:
        binding = _read_cloud_session(store=self.store)
        return None if binding is None else binding["session_id"]


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



def stage_claude_code_cloud_runtime(
    store: MemoryStore,
    manifest: MCPManifest,
    instructions: MCPInstructions,
    integration: MCPIntegration,
    hooks: MCPHookPlan,
    review: ClaudeCodeIntegrationPlan,
    local_lifecycle: LifecycleAdapterPlan,
    local: ClaudeCodeLocalPlan,
    plan: ClaudeCodeCloudPlan,
    *,
    confirm: bool,
) -> ClaudeCodeCloudStageResult:
    """Stage exactly one verified cloud plan under the project runtime after confirmation."""
    if confirm is not True:
        raise ClaudeCodeCloudError("Staging Claude cloud refusé sans confirmation explicite.")
    expected = compile_claude_code_cloud_plan(
        store, manifest, instructions, integration, hooks, review, local_lifecycle, local
    )
    if plan != expected:
        raise ClaudeCodeCloudError("Plan Claude cloud périmé, altéré ou étranger.")
    target = _cloud_runtime_path(store, create=True)
    existing = _read_optional_text(target)
    staged = _cloud_runtime_text(plan, manifest)
    if existing is not None and existing != staged:
        raise ClaudeCodeCloudError("État runtime Claude cloud divergent : refus sans écriture.")
    if existing == staged:
        return ClaudeCodeCloudStageResult("UNCHANGED", target, plan.plan_hash)
    _atomic_write(target, staged, ".vera-claude-cloud-")
    return ClaudeCodeCloudStageResult("STAGED", target, plan.plan_hash)


def preview_claude_code_cloud_host_config(
    store: MemoryStore,
    existing_settings: Mapping[str, Any],
    existing_mcp: Mapping[str, Any],
) -> ClaudeCodeCloudHostConfigPreview:
    """Compile a no-write project host preview from the only staged cloud runtime.

    The caller provides project-file snapshots explicitly.  This function never resolves a home
    directory, reads user settings, or treats a project declaration as a cloud trust decision.
    """
    if not isinstance(store, MemoryStore):
        raise ClaudeCodeCloudError("Store invalide pour le preview hôte Claude cloud.")
    settings = _json_object_copy(existing_settings, "settings Claude cloud")
    mcp = _json_object_copy(existing_mcp, "configuration MCP cloud")
    runtime = _load_staged_cloud_runtime(store)
    desired_hooks = _cloud_hook_commands(runtime.plan)
    desired_server = _cloud_mcp_server(runtime.plan)
    generic_server = _cloud_generic_server(store, runtime.manifest, runtime.instructions)
    merged_settings, _ = _merge_cloud_hooks(settings, desired_hooks)
    merged_mcp, _ = _merge_cloud_server(mcp, desired_server, generic_server)
    settings_text = _canonical_json(merged_settings)
    mcp_text = _canonical_json(merged_mcp)
    plan_hash = sha256((settings_text + "\\0" + mcp_text).encode("utf-8")).hexdigest()
    return ClaudeCodeCloudHostConfigPreview(
        status="PREVIEW",
        settings_path=_cloud_host_settings_path(store, create=False),
        mcp_path=_cloud_host_mcp_path(store),
        state_path=_cloud_host_state_path(store, create=False),
        settings_json_text=settings_text,
        mcp_json_text=mcp_text,
        plan_hash=plan_hash,
        user_scope_target=_CLOUD_USER_SCOPE_TARGET,
        user_scope_status="NOT_DELIVERED",
    )


def apply_claude_code_cloud_host_config(
    store: MemoryStore,
    preview: ClaudeCodeCloudHostConfigPreview,
    *,
    confirm: bool,
) -> ClaudeCodeCloudHostConfigApplyResult:
    """Write only a verified project preview after explicit confirmation.

    This deliberately has no user-scope argument or code path.  A future, separately approved
    operation must handle user-scope trust; this function cannot be repurposed for it.
    """
    if confirm is not True:
        raise ClaudeCodeCloudError("Application hôte Claude cloud refusée sans confirmation explicite.")
    if not isinstance(preview, ClaudeCodeCloudHostConfigPreview):
        raise ClaudeCodeCloudError("Preview hôte Claude cloud invalide.")
    settings_path = _cloud_host_settings_path(store, create=False)
    mcp_path = _cloud_host_mcp_path(store)
    state_path = _cloud_host_state_path(store, create=False)
    expected = preview_claude_code_cloud_host_config(
        store,
        _load_json_object(settings_path, "settings Claude cloud"),
        _load_json_object(mcp_path, "configuration MCP cloud"),
    )
    if preview != expected:
        raise ClaudeCodeCloudError("Preview hôte Claude cloud périmé, altéré ou divergent.")
    state_text = _cloud_host_state_text(preview)
    existing_state = _read_optional_text(state_path)
    if existing_state is not None and existing_state != state_text:
        raise ClaudeCodeCloudError("État hôte Claude cloud divergent : refus sans écriture.")
    settings_current = _read_optional_text(settings_path)
    mcp_current = _read_optional_text(mcp_path)
    if settings_current != preview.settings_json_text:
        _atomic_write(settings_path, preview.settings_json_text, ".vera-claude-cloud-settings-")
    if mcp_current != preview.mcp_json_text:
        _atomic_write(mcp_path, preview.mcp_json_text, ".vera-claude-cloud-mcp-")
    if existing_state != state_text:
        _atomic_write(state_path, state_text, ".vera-claude-cloud-host-")
    status = "UNCHANGED" if settings_current == preview.settings_json_text and mcp_current == preview.mcp_json_text and existing_state == state_text else "APPLIED_PROJECT_LOCAL"
    return ClaudeCodeCloudHostConfigApplyResult(
        status=status,
        settings_path=settings_path,
        mcp_path=mcp_path,
        state_path=state_path,
        plan_hash=preview.plan_hash,
        user_scope_status="NOT_DELIVERED",
    )


def handle_claude_code_cloud_hook(
    store: MemoryStore,
    lifecycle: LifecycleAdapterPlan,
    plan: ClaudeCodeCloudPlan,
    event: str,
    payload: Mapping[str, object],
) -> dict[str, object]:
    """Translate one fixed cloud host event into the Core lifecycle without setup semantics."""
    _verify_cloud_runtime(store, lifecycle, plan)
    if event not in _EVENTS or not isinstance(payload, Mapping):
        raise ClaudeCodeCloudError("Événement ou payload Claude cloud invalide.")
    session_id = _session_id(payload)
    _verify_cwd(store, payload.get("cwd"))
    guard = ResumeGuardService(store)
    if event == "SessionStart":
        _claim_cloud_session(store, session_id)
        source = payload.get("source")
        reason = "RESUME" if source == "resume" else "SESSION_OPEN" if source == "startup" else "CONTEXT_RESTORED"
        dossier = _compile_cloud_dossier(store)
        guard.arm(session_id, CLAUDE_CODE_CLOUD_ADAPTER_ID, reason, dossier, mode="HARD")
        return _context(event, "Resume Dossier VERA cloud — lire et acquitter via mmu_acknowledge_resume :\n" + dossier.json_text)
    if _read_cloud_session(store) != {"project_id": store.identity.project_id, "session_id": session_id}:
        raise ClaudeCodeCloudError("Session Claude cloud non liée au runtime courant.")
    if event == "PreToolUse":
        tool_name = payload.get("tool_name")
        if not isinstance(tool_name, str):
            raise ClaudeCodeCloudError("PreToolUse Claude cloud sans nom de tool.")
        if tool_name == _acknowledgement_tool_name(store):
            return _empty(event)
        outcome = guard.precheck(session_id, CLAUDE_CODE_CLOUD_ADAPTER_ID)
        if outcome.decision == GuardDecision.DENY:
            return _deny(event, outcome.reason)
        if outcome.decision == GuardDecision.ALLOW_WITH_NOTICE:
            return _context(event, outcome.reason)
        return _empty(event)
    if event == "PostToolUse":
        outcome = guard.precheck(session_id, CLAUDE_CODE_CLOUD_ADAPTER_ID)
        return _context(event, outcome.reason) if outcome.decision != GuardDecision.ALLOW else _empty(event)
    if event == "PreCompact":
        dossier = _compile_cloud_dossier(store)
        guard.arm(session_id, CLAUDE_CODE_CLOUD_ADAPTER_ID, "CONTEXT_PREPARE", dossier, mode="HARD")
        return _context(event, "VERA prépare la reprise cloud ; le dossier devra être acquitté après compaction.")
    if event == "PostCompact":
        dossier = _compile_cloud_dossier(store)
        guard.arm(session_id, CLAUDE_CODE_CLOUD_ADAPTER_ID, "CONTEXT_RESTORED", dossier, mode="HARD")
        return _context(event, "Resume Dossier VERA cloud — lire et acquitter via mmu_acknowledge_resume :\n" + dossier.json_text)
    outcome = guard.session_ending(session_id, CLAUDE_CODE_CLOUD_ADAPTER_ID, already_nudged=False)
    _release_cloud_session(store, session_id)
    return _context(event, outcome.reason) if outcome.decision == GuardDecision.NUDGE else _empty(event)


def claude_code_cloud_hook_main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for one cloud hook event; it never configures the cloud host."""
    parser = argparse.ArgumentParser(description="Hook lifecycle Claude Code cloud VERA-MMU")
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--event", choices=_EVENTS, required=True)
    args = parser.parse_args(argv)
    try:
        payload = json.loads(sys.stdin.read())
        if not isinstance(payload, dict):
            raise ClaudeCodeCloudError("Payload JSON de hook Claude cloud requis.")
        from .identity import load_profile

        with MemoryStore.open(load_profile(args.profile), args.profile) as store:
            runtime = _load_staged_cloud_runtime(store)
            response = handle_claude_code_cloud_hook(store, runtime.lifecycle, runtime.plan, args.event, payload)
    except (StoreError, json.JSONDecodeError) as exc:
        print(json.dumps(_deny(args.event, str(exc)), ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(response, ensure_ascii=False, sort_keys=True))
    return 0


def claude_code_cloud_mcp_main(argv: Sequence[str] | None = None) -> None:
    """Start the staged, deny-by-default cloud MCP runtime on stdio."""
    parser = argparse.ArgumentParser(description="Serveur MCP lifecycle Claude Code cloud VERA-MMU")
    parser.add_argument("--profile", type=Path, required=True)
    args = parser.parse_args(argv)
    from .identity import load_profile

    with MemoryStore.open(load_profile(args.profile), args.profile) as store:
        runtime = _load_staged_cloud_runtime(store)
        server = create_server(
            store,
            runtime_adapter=DenyRuntimeAdapter(),
            manifest=runtime.manifest,
            instructions=runtime.instructions,
            lifecycle_adapter_registry=LifecycleAdapterRegistry((ClaudeCodeCloudSessionAdapter(store),)),
            lifecycle_adapter_plan=runtime.lifecycle,
            actor="vera-claude-code-cloud",
        )
        server.run("stdio")


def _cloud_plan_payload(plan: ClaudeCodeCloudPlan) -> dict[str, Any]:
    if not isinstance(plan, ClaudeCodeCloudPlan) or plan.plan_hash != sha256(plan.json_text.encode("utf-8")).hexdigest():
        raise ClaudeCodeCloudError("Plan Claude cloud altéré.")
    try:
        payload = json.loads(plan.json_text)["claudeCodeCloud"]
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ClaudeCodeCloudError("Plan Claude cloud illisible.") from exc
    if not isinstance(payload, dict):
        raise ClaudeCodeCloudError("Plan Claude cloud hors format fermé.")
    return payload


def _cloud_hook_commands(plan: ClaudeCodeCloudPlan) -> dict[str, list[dict[str, object]]]:
    server = _cloud_mcp_server(plan)
    server_id = _cloud_plan_payload(plan).get("mcpServer", {}).get("id")
    profile_argument = server.get("args", [None, None])[1] if isinstance(server.get("args"), list) else None
    if not isinstance(server_id, str) or not server_id.startswith("vera-mmu-") or not isinstance(profile_argument, str):
        raise ClaudeCodeCloudError("Serveur MCP cloud attesté invalide pour les hooks.")

    def group(event: str, *, matcher: str | None = None) -> dict[str, object]:
        command = f'{CLOUD_HOOK_ENTRYPOINT} --profile "{profile_argument}" --event {event}'
        payload: dict[str, object] = {"hooks": [{"command": command, "timeout": 10, "type": "command"}]}
        if matcher is not None:
            payload["matcher"] = matcher
        return payload

    return {
        "PostCompact": [group("PostCompact")],
        "PostToolUse": [group("PostToolUse", matcher=f"mcp__{server_id}__mmu_acknowledge_resume")],
        "PreCompact": [group("PreCompact")],
        "PreToolUse": [group("PreToolUse")],
        "SessionStart": [group("SessionStart")],
        "Stop": [group("Stop")],
    }


def _cloud_mcp_server(plan: ClaudeCodeCloudPlan) -> dict[str, object]:
    payload = _cloud_plan_payload(plan)
    server = payload.get("mcpServer")
    if not isinstance(server, dict):
        raise ClaudeCodeCloudError("Serveur MCP cloud absent du plan attesté.")
    server_id = server.get("id")
    command = server.get("command")
    args = server.get("args")
    env = server.get("env")
    if not isinstance(server_id, str) or not server_id or command != CLOUD_MCP_ENTRYPOINT or not isinstance(args, list) or not isinstance(env, dict):
        raise ClaudeCodeCloudError("Serveur MCP cloud attesté invalide.")
    return {"id": server_id, "command": command, "args": list(args), "env": dict(env)}


def _cloud_generic_server(store: MemoryStore, manifest: MCPManifest, instructions: MCPInstructions) -> dict[str, object]:
    integration = compile_mcp_integration(store, manifest, instructions)
    try:
        servers = json.loads(integration.json_text)["mcpServers"]
        if not isinstance(servers, dict) or len(servers) != 1:
            raise ValueError("servers")
        server_id, server = next(iter(servers.items()))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ClaudeCodeCloudError("Serveur MCP générique attesté illisible.") from exc
    if not isinstance(server_id, str) or not isinstance(server, dict):
        raise ClaudeCodeCloudError("Serveur MCP générique attesté invalide.")
    return {"id": server_id, **server}


def _merge_cloud_hooks(existing: dict[str, Any], desired: object) -> tuple[dict[str, Any], bool]:
    if not isinstance(desired, dict):
        raise ClaudeCodeCloudError("Hooks Claude cloud attestés invalides.")
    existing_hooks = existing.get("hooks", {})
    if not isinstance(existing_hooks, dict):
        raise ClaudeCodeCloudError("hooks Claude cloud existant doit être un objet JSON.")
    merged = dict(existing)
    hooks = {key: list(value) if isinstance(value, list) else value for key, value in existing_hooks.items()}
    changed = False
    for event, groups in desired.items():
        if not isinstance(event, str) or not isinstance(groups, list):
            raise ClaudeCodeCloudError("Groupe de hook Claude cloud invalide.")
        current = hooks.get(event, [])
        if not isinstance(current, list):
            raise ClaudeCodeCloudError("Événement de hooks cloud existant doit être une liste.")
        for group in current:
            if _contains_vera_lifecycle_hook(group) and group not in groups:
                raise ClaudeCodeCloudError("Conflit : hook lifecycle VERA existant divergent.")
        additions = [group for group in groups if group not in current]
        if additions:
            hooks[event] = [*current, *additions]
            changed = True
    if changed:
        merged["hooks"] = hooks
    return merged, changed


def _contains_vera_lifecycle_hook(group: object) -> bool:
    if not isinstance(group, dict):
        return False
    handlers = group.get("hooks")
    return isinstance(handlers, list) and any(
        isinstance(handler, dict) and isinstance(handler.get("command"), str) and handler["command"].startswith("vmmu-claude-code-")
        for handler in handlers
    )


def _merge_cloud_server(existing: dict[str, Any], desired: object, generic: Mapping[str, object]) -> tuple[dict[str, Any], bool]:
    if not isinstance(desired, dict):
        raise ClaudeCodeCloudError("Serveur MCP Claude cloud attesté invalide.")
    server_id = desired.get("id")
    server = {key: value for key, value in desired.items() if key != "id"}
    generic_server = {key: value for key, value in generic.items() if key != "id"}
    if not isinstance(server_id, str) or not server_id:
        raise ClaudeCodeCloudError("Identifiant serveur MCP Claude cloud invalide.")
    servers = existing.get("mcpServers", {})
    if not isinstance(servers, dict):
        raise ClaudeCodeCloudError("mcpServers cloud existant doit être un objet JSON.")
    current = servers.get(server_id)
    if current == server:
        return existing, False
    if current is not None and current != generic_server:
        raise ClaudeCodeCloudError("Conflit : serveur MCP VERA cloud existant divergent.")
    merged = dict(existing)
    merged_servers = dict(servers)
    merged_servers[server_id] = server
    merged["mcpServers"] = merged_servers
    return merged, True


def _json_object_copy(value: Mapping[str, Any], label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ClaudeCodeCloudError(f"{label} doit être un objet JSON.")
    try:
        copied = json.loads(json.dumps(dict(value), ensure_ascii=False))
    except (TypeError, ValueError) as exc:
        raise ClaudeCodeCloudError(f"{label} non sérialisable en JSON.") from exc
    if not isinstance(copied, dict):
        raise ClaudeCodeCloudError(f"{label} doit être un objet JSON.")
    return copied


def _cloud_host_settings_path(store: MemoryStore, *, create: bool) -> Path:
    directory = store.workspace.project_root / ".claude"
    if directory.is_symlink():
        raise ClaudeCodeCloudError("Répertoire .claude cloud symlinké refusé.")
    if create:
        _safe_parent(directory, "répertoire .claude cloud")
    elif directory.exists() and not directory.is_dir():
        raise ClaudeCodeCloudError("Répertoire .claude cloud ambigu ou non régulier.")
    target = directory / "settings.json"
    if target.is_symlink():
        raise ClaudeCodeCloudError("La cible .claude/settings.json cloud ne peut pas être un lien symbolique.")
    return target


def _cloud_host_mcp_path(store: MemoryStore) -> Path:
    target = store.workspace.project_root / ".mcp.json"
    if target.is_symlink():
        raise ClaudeCodeCloudError("La cible .mcp.json cloud ne peut pas être un lien symbolique.")
    return target


def _cloud_host_state_path(store: MemoryStore, *, create: bool) -> Path:
    target = store.locator.runtime_dir / "generated" / "claude-code-cloud-host-config.json"
    if target.parent.is_symlink():
        raise ClaudeCodeCloudError("Runtime hôte cloud symlinké refusé.")
    if create:
        _safe_parent(target.parent, "runtime hôte cloud")
    elif target.parent.exists() and not target.parent.is_dir():
        raise ClaudeCodeCloudError("Runtime hôte cloud ambigu ou non régulier.")
    if target.is_symlink():
        raise ClaudeCodeCloudError("État hôte Claude cloud symlinké refusé.")
    return target


def _load_json_object(target: Path, label: str) -> dict[str, Any]:
    if not target.exists():
        return {}
    if target.is_symlink() or not target.is_file():
        raise ClaudeCodeCloudError(f"La cible {label} doit être un fichier régulier.")
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClaudeCodeCloudError(f"La cible {label} n’est pas un JSON lisible.") from exc
    if not isinstance(value, dict):
        raise ClaudeCodeCloudError(f"La cible {label} doit contenir un objet JSON.")
    return value


def _cloud_host_state_text(preview: ClaudeCodeCloudHostConfigPreview) -> str:
    if preview.plan_hash != sha256((preview.settings_json_text + "\\0" + preview.mcp_json_text).encode("utf-8")).hexdigest():
        raise ClaudeCodeCloudError("Preview hôte Claude cloud altéré.")
    return _canonical_json(
        {
            "cloudHostConfig": {
                "format": CLOUD_HOST_CONFIG_FORMAT,
                "mcpSha256": sha256(preview.mcp_json_text.encode("utf-8")).hexdigest(),
                "planHash": preview.plan_hash,
                "settingsSha256": sha256(preview.settings_json_text.encode("utf-8")).hexdigest(),
                "userScope": "NOT_DELIVERED",
            }
        }
    )


def _verify_cloud_runtime(store: MemoryStore, lifecycle: LifecycleAdapterPlan, plan: ClaudeCodeCloudPlan) -> None:
    runtime = _load_staged_cloud_runtime(store)
    if lifecycle != runtime.lifecycle or plan != runtime.plan:
        raise ClaudeCodeCloudError("Plan lifecycle Claude cloud périmé, altéré ou étranger.")


def _cloud_runtime_path(store: MemoryStore, *, create: bool) -> Path:
    target = store.locator.runtime_dir / "generated" / "claude-code-cloud-runtime.json"
    if target.parent.is_symlink():
        raise ClaudeCodeCloudError("Runtime généré cloud symlinké refusé.")
    if create:
        _safe_parent(target.parent, "runtime cloud généré")
    elif target.parent.exists() and not target.parent.is_dir():
        raise ClaudeCodeCloudError("Runtime cloud généré ambigu ou non régulier.")
    if target.is_symlink():
        raise ClaudeCodeCloudError("État runtime Claude cloud symlinké refusé.")
    return target


def _cloud_runtime_text(plan: ClaudeCodeCloudPlan, manifest: MCPManifest) -> str:
    if not isinstance(plan, ClaudeCodeCloudPlan) or plan.plan_hash != sha256(plan.json_text.encode("utf-8")).hexdigest():
        raise ClaudeCodeCloudError("Plan Claude cloud altéré.")
    bindings = [{"adapter_id": item.adapter_id, "capability_id": item.capability_id} for item in manifest.capabilities]
    if not bindings:
        raise ClaudeCodeCloudError("Manifeste cloud sans bindings d’adapter.")
    return json.dumps(
        {
            "cloudRuntime": {
                "adapterBindings": bindings,
                "format": CLOUD_RUNTIME_FORMAT,
                "plan": json.loads(plan.json_text)["claudeCodeCloud"],
                "planHash": plan.plan_hash,
            }
        },
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    ) + "\n"


def _load_staged_cloud_runtime(store: MemoryStore) -> _CloudRuntime:
    raw = _read_optional_text(_cloud_runtime_path(store, create=False))
    if raw is None:
        raise ClaudeCodeCloudError("Adapter Claude cloud non staged : état attesté absent.")
    try:
        envelope = json.loads(raw)["cloudRuntime"]
        if not isinstance(envelope, dict) or envelope.get("format") != CLOUD_RUNTIME_FORMAT:
            raise ValueError("format")
        plan_payload = envelope["plan"]
        plan_hash = envelope["planHash"]
        server_env = plan_payload["mcpServer"]["env"]
        raw_bindings = envelope["adapterBindings"]
        if not isinstance(raw_bindings, list):
            raise ValueError("bindings")
        bindings = {str(item["capability_id"]): str(item["adapter_id"]) for item in raw_bindings}
        if not bindings or len(bindings) != len(raw_bindings):
            raise ValueError("bindings")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ClaudeCodeCloudError("État runtime Claude cloud hors format fermé.") from exc
    manifest = compile_mcp_manifest(store, adapter_bindings=bindings)
    instructions = compile_mcp_instructions(store, manifest)
    integration = compile_mcp_integration(store, manifest, instructions)
    hooks = compile_mcp_hook_plan(store, manifest, instructions, integration)
    review = compile_claude_code_integration_plan(store, manifest, instructions, integration, hooks)
    local_lifecycle = compile_lifecycle_adapter_plan(
        store, manifest, adapter_id="claude-code-local-v1", adapter_version="1.0.0", maximum_guard_mode="HARD"
    )
    local = compile_claude_code_local_plan(store, manifest, instructions, integration, hooks, review, local_lifecycle)
    plan = compile_claude_code_cloud_plan(store, manifest, instructions, integration, hooks, review, local_lifecycle, local)
    if plan.plan_hash != plan_hash or plan_payload != json.loads(plan.json_text)["claudeCodeCloud"]:
        raise ClaudeCodeCloudError("État runtime Claude cloud périmé ou altéré.")
    expected_env = json.loads(plan.json_text)["claudeCodeCloud"]["mcpServer"]["env"]
    if server_env != expected_env:
        raise ClaudeCodeCloudError("Environnement MCP cloud staged divergent.")
    lifecycle = compile_lifecycle_adapter_plan(
        store,
        manifest,
        adapter_id=CLAUDE_CODE_CLOUD_ADAPTER_ID,
        adapter_version=CLAUDE_CODE_CLOUD_ADAPTER_VERSION,
        maximum_guard_mode=CLAUDE_CODE_CLOUD_MAXIMUM_GUARD_MODE,
    )
    return _CloudRuntime(manifest, instructions, lifecycle, plan)


def _session_id(payload: Mapping[str, object]) -> str:
    value = payload.get("session_id")
    if not isinstance(value, str) or not value or len(value) > 256 or "/" in value or "\\" in value:
        raise ClaudeCodeCloudError("Identité de session Claude cloud absente ou invalide.")
    return value


def _verify_cwd(store: MemoryStore, value: object) -> None:
    if not isinstance(value, str) or not value:
        raise ClaudeCodeCloudError("Répertoire courant Claude cloud absent.")
    try:
        Path(value).resolve(strict=False).relative_to(store.workspace.project_root.resolve(strict=False))
    except ValueError as exc:
        raise ClaudeCodeCloudError("Répertoire courant Claude cloud hors projet VERA.") from exc


def _cloud_session_path(store: MemoryStore) -> Path:
    target = store.locator.runtime_dir / "lifecycle" / "claude-code-cloud-session.json"
    _safe_parent(target.parent, "runtime lifecycle cloud")
    if target.is_symlink():
        raise ClaudeCodeCloudError("Liaison de session Claude cloud symlinkée refusée.")
    return target


def _read_cloud_session(store: MemoryStore) -> dict[str, str] | None:
    target = _cloud_session_path(store)
    if not target.exists():
        return None
    if not target.is_file():
        raise ClaudeCodeCloudError("Liaison de session Claude cloud non régulière.")
    try:
        parsed = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClaudeCodeCloudError("Liaison de session Claude cloud illisible.") from exc
    if not isinstance(parsed, dict) or set(parsed) != {"project_id", "session_id"}:
        raise ClaudeCodeCloudError("Liaison de session Claude cloud ambiguë.")
    if parsed.get("project_id") != store.identity.project_id or not isinstance(parsed.get("session_id"), str):
        raise ClaudeCodeCloudError("Liaison de session Claude cloud étrangère ou invalide.")
    return {"project_id": store.identity.project_id, "session_id": str(parsed["session_id"])}


def _claim_cloud_session(store: MemoryStore, session_id: str) -> None:
    existing = _read_cloud_session(store)
    candidate = {"project_id": store.identity.project_id, "session_id": session_id}
    if existing is not None and existing != candidate:
        raise ClaudeCodeCloudError("Conflit : une autre session Claude cloud est déjà active pour ce projet.")
    if existing is None:
        _atomic_write(_cloud_session_path(store), _canonical_json(candidate), ".vera-claude-cloud-session-")


def _release_cloud_session(store: MemoryStore, session_id: str) -> None:
    target = _cloud_session_path(store)
    binding = _read_cloud_session(store)
    if binding is not None and binding["session_id"] == session_id:
        try:
            target.unlink()
        except OSError as exc:
            raise ClaudeCodeCloudError("Libération de session Claude cloud impossible.") from exc


def _compile_cloud_dossier(store: MemoryStore):
    return ResumeDossierService(store).compile(
        (
            ResumeSectionRequirement("working-rules", 12, 512),
            ResumeSectionRequirement("current-state", 12, 512),
        ),
        {
            "working-rules": "Mesurer les faits avant toute conclusion.",
            "current-state": "La garde Claude cloud attend un acquittement.",
        },
    )


def _acknowledgement_tool_name(store: MemoryStore) -> str:
    return f"mcp__vera-mmu-{store.identity.project_id}__mmu_acknowledge_resume"


def _context(event: str, text: str) -> dict[str, object]:
    return {"hookSpecificOutput": {"additionalContext": text[:12_000], "hookEventName": event}}


def _empty(event: str) -> dict[str, object]:
    return {"hookSpecificOutput": {"hookEventName": event}}


def _deny(event: str, reason: str) -> dict[str, object]:
    return {"hookSpecificOutput": {"hookEventName": event, "permissionDecision": "deny", "permissionDecisionReason": reason}}


def _safe_parent(directory: Path, label: str) -> None:
    if directory.is_symlink():
        raise ClaudeCodeCloudError(f"{label} symlinké refusé.")
    try:
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    except OSError as exc:
        raise ClaudeCodeCloudError(f"Création de {label} impossible.") from exc
    if not directory.is_dir() or directory.is_symlink():
        raise ClaudeCodeCloudError(f"{label} ambigu ou non régulier.")


def _read_optional_text(target: Path) -> str | None:
    if not target.exists():
        return None
    if target.is_symlink() or not target.is_file():
        raise ClaudeCodeCloudError("État Claude cloud non régulier.")
    try:
        return target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ClaudeCodeCloudError("État Claude cloud illisible.") from exc


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _atomic_write(target: Path, text: str, prefix: str) -> None:
    _safe_parent(target.parent, "répertoire cible cloud")
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=target.parent, prefix=prefix, suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, target)
    except OSError as exc:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
        raise ClaudeCodeCloudError("Écriture atomique Claude cloud impossible.") from exc


def claude_code_cloud_config_main(argv: Sequence[str] | None = None) -> int:
    """Preview, or explicitly apply, the project-only Claude cloud configuration."""
    parser = argparse.ArgumentParser(description="Configuration hôte Claude Code cloud VERA-MMU")
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--apply-project", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args(argv)
    try:
        from .identity import load_profile

        with MemoryStore.open(load_profile(args.profile), args.profile) as store:
            preview = preview_claude_code_cloud_host_config(
                store,
                _load_json_object(_cloud_host_settings_path(store, create=False), "settings Claude cloud"),
                _load_json_object(_cloud_host_mcp_path(store), "configuration MCP cloud"),
            )
            if args.apply_project:
                result = apply_claude_code_cloud_host_config(store, preview, confirm=args.confirm)
                payload = {
                    "ok": True,
                    "mcpPath": str(result.mcp_path),
                    "planHash": result.plan_hash,
                    "settingsPath": str(result.settings_path),
                    "statePath": str(result.state_path),
                    "status": result.status,
                    "userScope": result.user_scope_status,
                }
            else:
                payload = {
                    "mcpPath": str(preview.mcp_path),
                    "ok": True,
                    "planHash": preview.plan_hash,
                    "settingsPath": str(preview.settings_path),
                    "status": preview.status,
                    "userScope": preview.user_scope_status,
                    "userScopeTarget": preview.user_scope_target,
                }
    except StoreError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


def claude_code_cloud_stage_main(argv: Sequence[str] | None = None) -> int:
    """Stage a deny-by-default cloud runtime from the project catalogue after confirmation."""
    parser = argparse.ArgumentParser(description="Staging runtime Claude Code cloud VERA-MMU")
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args(argv)
    try:
        from .identity import load_profile

        with MemoryStore.open(load_profile(args.profile), args.profile) as store:
            manifest = compile_mcp_manifest(store, adapter_bindings=_cloud_deny_bindings(store))
            instructions = compile_mcp_instructions(store, manifest)
            integration = compile_mcp_integration(store, manifest, instructions)
            hooks = compile_mcp_hook_plan(store, manifest, instructions, integration)
            review = compile_claude_code_integration_plan(store, manifest, instructions, integration, hooks)
            local_lifecycle = compile_lifecycle_adapter_plan(
                store, manifest, adapter_id="claude-code-local-v1", adapter_version="1.0.0", maximum_guard_mode="HARD"
            )
            local = compile_claude_code_local_plan(store, manifest, instructions, integration, hooks, review, local_lifecycle)
            plan = compile_claude_code_cloud_plan(store, manifest, instructions, integration, hooks, review, local_lifecycle, local)
            result = stage_claude_code_cloud_runtime(
                store, manifest, instructions, integration, hooks, review, local_lifecycle, local, plan, confirm=args.confirm
            )
    except StoreError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps({"ok": True, "planHash": result.plan_hash, "statePath": str(result.state_path), "status": result.status}, ensure_ascii=False, sort_keys=True))
    return 0


def _cloud_deny_bindings(store: MemoryStore) -> dict[str, str]:
    rows = store.connection.execute(
        "SELECT capability_id FROM capability_policy WHERE decision = 'ALLOW' ORDER BY capability_id"
    ).fetchall()
    bindings = {str(row["capability_id"]): "cloud-deny-v1" for row in rows}
    if not bindings:
        raise ClaudeCodeCloudError("Aucune capability ALLOW à stage pour Claude cloud.")
    return bindings


if __name__ == "__main__":
    raise SystemExit(claude_code_cloud_hook_main())

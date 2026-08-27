"""Codex host adapter with a bounded lifecycle guarantee.

This module maps the universal resume lifecycle to the documented Codex project-hook and
project-MCP surfaces.  It deliberately promises a hard guard only for documented local tool
paths, never for hosted tools, hook trust, or a real Codex session that has not been observed.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile
import tomllib
from typing import Any, Mapping, Sequence

from .lifecycle_adapters import LifecycleAdapterPlan, LifecycleAdapterRegistry, compile_lifecycle_adapter_plan
from .mcp_hooks import MCPHookPlan, MCPHookPlanError, compile_mcp_hook_plan
from .mcp_instructions import MCPInstructions, MCPInstructionsError, compile_mcp_instructions
from .mcp_integration import MCPIntegration, MCPIntegrationError, compile_mcp_integration
from .mcp_manifest import MCPManifest, MCPManifestError, compile_mcp_manifest, verify_mcp_manifest
from .mcp_server import DenyRuntimeAdapter, create_server
from .profile_resume import compile_profile_resume_dossier, profile_resume_sections
from .session_lifecycle import GuardDecision, ResumeDossierService, ResumeGuardService, ResumeSectionRequirement
from .store import MemoryStore, StoreError


CODEX_FORMAT = "vera-codex-adapter/v1"
CODEX_RUNTIME_FORMAT = "vera-codex-runtime/v1"
CODEX_HOST_CONFIG_FORMAT = "vera-codex-host-config/v1"
CODEX_ADAPTER_ID = "codex-v1"
CODEX_ADAPTER_VERSION = "1.0.0"
CODEX_MAXIMUM_GUARD_MODE = "HARD"
CODEX_MCP_ENTRYPOINT = "vmmu-codex-mcp"
CODEX_HOOK_ENTRYPOINT = "vmmu-codex-hook"
CODEX_CONFIG_ENTRYPOINT = "vmmu-codex-config"
CODEX_TOOL_COVERAGE = "PARTIAL_LOCAL_TOOLS"
_EVENTS = ("SessionStart", "PreToolUse", "PostToolUse", "PreCompact", "PostCompact", "Stop")


class CodexAdapterError(StoreError):
    """A Codex runtime, lifecycle event, or configuration cannot be trusted."""


@dataclass(frozen=True)
class CodexPlan:
    """Canonical Codex-specific declaration bound to generic VERA snapshots."""

    format: str
    project_id: str
    mcp_build_hash: str
    instructions_hash: str
    config_hash: str
    hook_plan_hash: str
    lifecycle_plan_hash: str
    plan_hash: str
    json_text: str


@dataclass(frozen=True)
class CodexStageResult:
    status: str
    state_path: Path
    plan_hash: str


@dataclass(frozen=True)
class CodexHostConfigPreview:
    status: str
    hooks_path: Path
    config_path: Path
    state_path: Path
    hooks_json_text: str
    config_toml_text: str
    plan_hash: str
    coverage: str


@dataclass(frozen=True)
class CodexHostConfigApplyResult:
    status: str
    hooks_path: Path
    config_path: Path
    state_path: Path
    plan_hash: str
    coverage: str


@dataclass(frozen=True)
class _CodexRuntime:
    manifest: MCPManifest
    instructions: MCPInstructions
    lifecycle: LifecycleAdapterPlan
    plan: CodexPlan


class CodexSessionAdapter:
    """Resolve the single staged Codex session; the MCP client never supplies it."""

    adapter_id = CODEX_ADAPTER_ID
    adapter_version = CODEX_ADAPTER_VERSION
    maximum_guard_mode = CODEX_MAXIMUM_GUARD_MODE

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def session_identity(self) -> str | None:
        binding = _read_codex_session(self.store)
        return None if binding is None else binding["session_id"]


def compile_codex_plan(
    store: MemoryStore,
    manifest: MCPManifest,
    instructions: MCPInstructions,
    integration: MCPIntegration,
    hooks: MCPHookPlan,
    lifecycle: LifecycleAdapterPlan,
) -> CodexPlan:
    """Compile a project-bound Codex plan without probing or configuring the host."""
    if not isinstance(store, MemoryStore):
        raise CodexAdapterError("Store invalide pour le plan Codex.")
    try:
        verify_mcp_manifest(store, manifest)
        expected_instructions = compile_mcp_instructions(store, manifest)
        expected_integration = compile_mcp_integration(store, manifest, expected_instructions)
        expected_hooks = compile_mcp_hook_plan(store, manifest, expected_instructions, expected_integration)
        expected_lifecycle = compile_lifecycle_adapter_plan(
            store,
            manifest,
            adapter_id=CODEX_ADAPTER_ID,
            adapter_version=CODEX_ADAPTER_VERSION,
            maximum_guard_mode=CODEX_MAXIMUM_GUARD_MODE,
        )
    except (MCPManifestError, MCPInstructionsError, MCPIntegrationError, MCPHookPlanError, StoreError) as exc:
        raise CodexAdapterError("Snapshots invalides pour le plan Codex.") from exc
    if instructions != expected_instructions or integration != expected_integration or hooks != expected_hooks or lifecycle != expected_lifecycle:
        raise CodexAdapterError("Snapshot Codex périmé, altéré ou étranger.")
    server_id, profile_argument = _server_identity(integration)
    profile_path = _profile_path_for_host(store, profile_argument)
    payload = {
        "codex": {
            "coverage": {"toolGuard": CODEX_TOOL_COVERAGE, "hostedTools": "NOT_INTERCEPTED", "sessionStartMcp": "RACE_NOT_GATE"},
            "hooks": {"events": list(_EVENTS), "trust": "HOST_REVIEW_REQUIRED"},
            "mcpServer": {
                "args": ["--profile", str(profile_path)],
                "command": CODEX_MCP_ENTRYPOINT,
                "cwd": str(store.workspace.project_root.resolve(strict=False)),
                "enabledTools": ["mmu_acknowledge_resume"],
                "id": server_id,
            },
            "runtime": {"network": "FORBIDDEN", "provider": "PREINSTALLED_VERA"},
        }
    }
    json_text = _canonical_json(payload)
    return CodexPlan(
        format=CODEX_FORMAT,
        project_id=store.identity.project_id,
        mcp_build_hash=manifest.mcp_build_hash,
        instructions_hash=instructions.instructions_hash,
        config_hash=integration.config_hash,
        hook_plan_hash=hooks.hook_plan_hash,
        lifecycle_plan_hash=lifecycle.lifecycle_plan_hash,
        plan_hash=sha256(json_text.encode("utf-8")).hexdigest(),
        json_text=json_text,
    )


def stage_codex_runtime(
    store: MemoryStore,
    manifest: MCPManifest,
    instructions: MCPInstructions,
    integration: MCPIntegration,
    hooks: MCPHookPlan,
    lifecycle: LifecycleAdapterPlan,
    plan: CodexPlan,
    *,
    confirm: bool,
) -> CodexStageResult:
    """Stage exactly one verified plan under VERA runtime after explicit confirmation."""
    if confirm is not True:
        raise CodexAdapterError("Staging Codex refusé sans confirmation explicite.")
    expected = compile_codex_plan(store, manifest, instructions, integration, hooks, lifecycle)
    if plan != expected:
        raise CodexAdapterError("Plan Codex périmé, altéré ou étranger.")
    target = _codex_runtime_path(store, create=True)
    staged = _codex_runtime_text(plan, manifest)
    current = _read_optional_text(target)
    if current is not None and current != staged:
        raise CodexAdapterError("État runtime Codex divergent : refus sans écriture.")
    if current == staged:
        return CodexStageResult("UNCHANGED", target, plan.plan_hash)
    _atomic_write(target, staged, ".vera-codex-runtime-")
    return CodexStageResult("STAGED", target, plan.plan_hash)


def preview_codex_host_config(
    store: MemoryStore,
    existing_hooks: Mapping[str, Any],
    existing_config_toml: str,
) -> CodexHostConfigPreview:
    """Compile a no-write project preview for `.codex/hooks.json` and `config.toml`."""
    if not isinstance(store, MemoryStore):
        raise CodexAdapterError("Store invalide pour le preview Codex.")
    hooks = _json_object_copy(existing_hooks, "hooks Codex")
    runtime = _load_staged_codex_runtime(store)
    desired_hooks = _codex_hook_commands(runtime.plan)
    merged_hooks, _ = _merge_codex_hooks(hooks, desired_hooks)
    merged_config, _ = _merge_codex_config(existing_config_toml, _codex_mcp_server(runtime.plan))
    hooks_text = _canonical_json(merged_hooks)
    plan_hash = sha256((hooks_text + "\0" + merged_config).encode("utf-8")).hexdigest()
    return CodexHostConfigPreview(
        status="PREVIEW",
        hooks_path=_codex_hooks_path(store, create=False),
        config_path=_codex_config_path(store, create=False),
        state_path=_codex_host_state_path(store, create=False),
        hooks_json_text=hooks_text,
        config_toml_text=merged_config,
        plan_hash=plan_hash,
        coverage=CODEX_TOOL_COVERAGE,
    )


def apply_codex_host_config(
    store: MemoryStore,
    preview: CodexHostConfigPreview,
    *,
    confirm: bool,
) -> CodexHostConfigApplyResult:
    """Apply a verified project-local Codex preview, never user/system configuration."""
    if confirm is not True:
        raise CodexAdapterError("Application Codex refusée sans confirmation explicite.")
    if not isinstance(preview, CodexHostConfigPreview) or preview.coverage != CODEX_TOOL_COVERAGE:
        raise CodexAdapterError("Preview Codex invalide.")
    hooks_path = _codex_hooks_path(store, create=False)
    config_path = _codex_config_path(store, create=False)
    state_path = _codex_host_state_path(store, create=False)
    expected = preview_codex_host_config(
        store,
        _load_json_object(hooks_path, "hooks Codex"),
        _read_optional_text(config_path) or "",
    )
    if preview != expected:
        raise CodexAdapterError("Preview Codex périmé, altéré ou divergent.")
    receipt = _codex_host_state_text(preview)
    existing_receipt = _read_optional_text(state_path)
    if existing_receipt is not None and existing_receipt != receipt:
        raise CodexAdapterError("État configuration Codex divergent : refus sans écriture.")
    current_hooks = _read_optional_text(hooks_path)
    current_config = _read_optional_text(config_path)
    if current_hooks != preview.hooks_json_text:
        _atomic_write(hooks_path, preview.hooks_json_text, ".vera-codex-hooks-")
    if current_config != preview.config_toml_text:
        _atomic_write(config_path, preview.config_toml_text, ".vera-codex-config-")
    if existing_receipt != receipt:
        _atomic_write(state_path, receipt, ".vera-codex-host-")
    status = "UNCHANGED" if current_hooks == preview.hooks_json_text and current_config == preview.config_toml_text and existing_receipt == receipt else "APPLIED_PROJECT_LOCAL"
    return CodexHostConfigApplyResult(status, hooks_path, config_path, state_path, preview.plan_hash, CODEX_TOOL_COVERAGE)


def handle_codex_hook(
    store: MemoryStore,
    lifecycle: LifecycleAdapterPlan,
    plan: CodexPlan,
    event: str,
    payload: Mapping[str, object],
) -> dict[str, object]:
    """Translate documented Codex hooks to universal lifecycle transitions only."""
    _verify_codex_runtime(store, lifecycle, plan)
    if event not in _EVENTS or not isinstance(payload, Mapping):
        raise CodexAdapterError("Événement ou payload Codex invalide.")
    session_id = _session_id(payload)
    _verify_cwd(store, payload.get("cwd"))
    guard = ResumeGuardService(store)
    if event == "SessionStart":
        _claim_codex_session(store, session_id)
        source = payload.get("source")
        reason = "RESUME" if source == "resume" else "SESSION_OPEN" if source == "startup" else "CONTEXT_RESTORED"
        dossier = _compile_codex_dossier(store)
        guard.arm(session_id, CODEX_ADAPTER_ID, reason, dossier, mode="HARD")
        return _context("Resume Dossier VERA Codex — lire et acquitter via mmu_acknowledge_resume :\n" + dossier.json_text)
    if _read_codex_session(store) != {"project_id": store.identity.project_id, "session_id": session_id}:
        raise CodexAdapterError("Session Codex non liée au runtime courant.")
    if event == "PreToolUse":
        tool_name = payload.get("tool_name")
        if not isinstance(tool_name, str):
            raise CodexAdapterError("PreToolUse Codex sans nom de tool.")
        if tool_name in _acknowledgement_tool_names(store):
            return {}
        outcome = guard.precheck(session_id, CODEX_ADAPTER_ID)
        if outcome.decision == GuardDecision.DENY:
            return {"decision": "block", "systemMessage": outcome.reason}
        if outcome.decision == GuardDecision.ALLOW_WITH_NOTICE:
            return {"systemMessage": outcome.reason}
        return {}
    if event == "PostToolUse":
        outcome = guard.precheck(session_id, CODEX_ADAPTER_ID)
        return {"systemMessage": outcome.reason} if outcome.decision != GuardDecision.ALLOW else {}
    if event == "PreCompact":
        dossier = _compile_codex_dossier(store)
        guard.arm(session_id, CODEX_ADAPTER_ID, "CONTEXT_PREPARE", dossier, mode="HARD")
        return {"systemMessage": "VERA prépare la reprise Codex ; le dossier devra être acquitté après compaction."}
    if event == "PostCompact":
        dossier = _compile_codex_dossier(store)
        guard.arm(session_id, CODEX_ADAPTER_ID, "CONTEXT_RESTORED", dossier, mode="HARD")
        return _context("Resume Dossier VERA Codex — lire et acquitter via mmu_acknowledge_resume :\n" + dossier.json_text)
    outcome = guard.session_ending(session_id, CODEX_ADAPTER_ID, already_nudged=False)
    _release_codex_session(store, session_id)
    return {"systemMessage": outcome.reason} if outcome.decision == GuardDecision.NUDGE else {}


def codex_stage_main(argv: Sequence[str] | None = None) -> int:
    """Stage the deny-by-default Codex runtime from the declared project catalogue."""
    parser = argparse.ArgumentParser(description="Staging runtime Codex VERA-MMU")
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args(argv)
    try:
        from .identity import load_profile

        with MemoryStore.open(load_profile(args.profile), args.profile) as store:
            manifest = compile_mcp_manifest(store, adapter_bindings=_codex_deny_bindings(store))
            instructions = compile_mcp_instructions(store, manifest)
            integration = compile_mcp_integration(store, manifest, instructions)
            hooks = compile_mcp_hook_plan(store, manifest, instructions, integration)
            lifecycle = compile_lifecycle_adapter_plan(
                store, manifest, adapter_id=CODEX_ADAPTER_ID, adapter_version=CODEX_ADAPTER_VERSION,
                maximum_guard_mode=CODEX_MAXIMUM_GUARD_MODE,
            )
            plan = compile_codex_plan(store, manifest, instructions, integration, hooks, lifecycle)
            result = stage_codex_runtime(store, manifest, instructions, integration, hooks, lifecycle, plan, confirm=args.confirm)
    except StoreError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps({"ok": True, "planHash": result.plan_hash, "statePath": str(result.state_path), "status": result.status}, ensure_ascii=False, sort_keys=True))
    return 0


def _codex_deny_bindings(store: MemoryStore) -> dict[str, str]:
    rows = store.connection.execute(
        "SELECT capability_id FROM capability_policy WHERE decision = 'ALLOW' ORDER BY capability_id"
    ).fetchall()
    bindings = {str(row["capability_id"]): "codex-deny-v1" for row in rows}
    if not bindings:
        raise CodexAdapterError("Aucune capability ALLOW à stage pour Codex.")
    return bindings


def codex_hook_main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hook lifecycle Codex VERA-MMU")
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--event", choices=_EVENTS, required=True)
    args = parser.parse_args(argv)
    try:
        payload = json.loads(sys.stdin.read())
        if not isinstance(payload, dict):
            raise CodexAdapterError("Payload JSON de hook Codex requis.")
        from .identity import load_profile

        with MemoryStore.open(load_profile(args.profile), args.profile) as store:
            runtime = _load_staged_codex_runtime(store)
            response = handle_codex_hook(store, runtime.lifecycle, runtime.plan, args.event, payload)
    except (StoreError, json.JSONDecodeError) as exc:
        print(json.dumps({"decision": "block", "systemMessage": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(response, ensure_ascii=False, sort_keys=True))
    return 0


def codex_mcp_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Serveur MCP lifecycle Codex VERA-MMU")
    parser.add_argument("--profile", type=Path, required=True)
    args = parser.parse_args(argv)
    from .identity import load_profile

    with MemoryStore.open(load_profile(args.profile), args.profile) as store:
        runtime = _load_staged_codex_runtime(store)
        server = create_server(
            store,
            runtime_adapter=DenyRuntimeAdapter(),
            manifest=runtime.manifest,
            instructions=runtime.instructions,
            lifecycle_adapter_registry=LifecycleAdapterRegistry((CodexSessionAdapter(store),)),
            lifecycle_adapter_plan=runtime.lifecycle,
            actor="vera-codex",
        )
        server.run("stdio")


def codex_config_main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Configuration Codex project-local VERA-MMU")
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--apply-project", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args(argv)
    try:
        from .identity import load_profile

        with MemoryStore.open(load_profile(args.profile), args.profile) as store:
            preview = preview_codex_host_config(
                store,
                _load_json_object(_codex_hooks_path(store, create=False), "hooks Codex"),
                _read_optional_text(_codex_config_path(store, create=False)) or "",
            )
            if args.apply_project:
                result = apply_codex_host_config(store, preview, confirm=args.confirm)
                payload: dict[str, object] = {
                    "configPath": str(result.config_path), "coverage": result.coverage, "hooksPath": str(result.hooks_path),
                    "ok": True, "planHash": result.plan_hash, "statePath": str(result.state_path), "status": result.status,
                }
            else:
                payload = {
                    "configPath": str(preview.config_path), "coverage": preview.coverage, "hooksPath": str(preview.hooks_path),
                    "ok": True, "planHash": preview.plan_hash, "status": preview.status,
                }
    except StoreError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


def _server_identity(integration: MCPIntegration) -> tuple[str, str]:
    try:
        servers = json.loads(integration.json_text)["mcpServers"]
        if not isinstance(servers, dict) or len(servers) != 1:
            raise ValueError("servers")
        server_id, server = next(iter(servers.items()))
        args = server["args"]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise CodexAdapterError("Configuration MCP attestée illisible.") from exc
    if not isinstance(server_id, str) or not server_id or not isinstance(args, list) or len(args) != 2 or args[0] != "--profile" or not isinstance(args[1], str):
        raise CodexAdapterError("Identité MCP attestée invalide.")
    return server_id, args[1]


def _profile_path_for_host(store: MemoryStore, argument: str) -> Path:
    prefix = "${CLAUDE_PROJECT_DIR:-.}/"
    candidate = argument[len(prefix):] if argument.startswith(prefix) else argument
    value = Path(candidate)
    if value.is_absolute() or ".." in value.parts:
        raise CodexAdapterError("Profil MCP attesté hors racine projet.")
    target = (store.workspace.project_root / value).resolve(strict=False)
    try:
        target.relative_to(store.workspace.project_root.resolve(strict=False))
    except ValueError as exc:
        raise CodexAdapterError("Profil MCP attesté hors projet.") from exc
    return target


def _codex_plan_payload(plan: CodexPlan) -> dict[str, Any]:
    if not isinstance(plan, CodexPlan) or plan.plan_hash != sha256(plan.json_text.encode("utf-8")).hexdigest():
        raise CodexAdapterError("Plan Codex altéré.")
    try:
        payload = json.loads(plan.json_text)["codex"]
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise CodexAdapterError("Plan Codex illisible.") from exc
    if not isinstance(payload, dict):
        raise CodexAdapterError("Plan Codex hors format fermé.")
    return payload


def _codex_mcp_server(plan: CodexPlan) -> dict[str, object]:
    server = _codex_plan_payload(plan).get("mcpServer")
    if not isinstance(server, dict):
        raise CodexAdapterError("Serveur MCP Codex absent du plan.")
    server_id = server.get("id")
    command = server.get("command")
    args = server.get("args")
    cwd = server.get("cwd")
    tools = server.get("enabledTools")
    if not isinstance(server_id, str) or not server_id or command != CODEX_MCP_ENTRYPOINT or not isinstance(args, list) or not all(isinstance(item, str) for item in args) or not isinstance(cwd, str) or not isinstance(tools, list) or tools != ["mmu_acknowledge_resume"]:
        raise CodexAdapterError("Serveur MCP Codex attesté invalide.")
    return {"id": server_id, "command": command, "args": list(args), "cwd": cwd, "enabledTools": list(tools)}


def _codex_hook_commands(plan: CodexPlan) -> dict[str, list[dict[str, object]]]:
    server = _codex_mcp_server(plan)
    args = server["args"]
    if not isinstance(args, list) or len(args) != 2:
        raise CodexAdapterError("Arguments hook Codex invalides.")
    profile = args[1]
    if not isinstance(profile, str):
        raise CodexAdapterError("Profil hook Codex invalide.")

    def group(event: str, matcher: str | None = None) -> dict[str, object]:
        handler: dict[str, object] = {
            "type": "command", "command": f'{CODEX_HOOK_ENTRYPOINT} --profile {json.dumps(profile)} --event {event}', "timeout": 10,
        }
        if event in {"SessionStart", "PostCompact"}:
            handler["additionalContextLimit"] = 5000
        payload: dict[str, object] = {"hooks": [handler]}
        if matcher is not None:
            payload["matcher"] = matcher
        return payload

    return {
        "SessionStart": [group("SessionStart", "startup|resume|clear|compact")],
        "PreToolUse": [group("PreToolUse", "*")],
        "PostToolUse": [group("PostToolUse", f"mcp__{server['id']}__mmu_acknowledge_resume")],
        "PreCompact": [group("PreCompact", "manual|auto")],
        "PostCompact": [group("PostCompact", "manual|auto")],
        "Stop": [group("Stop")],
    }


def _merge_codex_hooks(existing: dict[str, Any], desired: Mapping[str, list[dict[str, object]]]) -> tuple[dict[str, Any], bool]:
    hooks = existing.get("hooks", {})
    if not isinstance(hooks, dict):
        raise CodexAdapterError("hooks Codex existant doit être un objet JSON.")
    merged = dict(existing)
    result = {key: list(value) if isinstance(value, list) else value for key, value in hooks.items()}
    changed = False
    for event, groups in desired.items():
        current = result.get(event, [])
        if not isinstance(current, list):
            raise CodexAdapterError("Événement de hooks Codex existant doit être une liste.")
        for group in current:
            if _contains_codex_lifecycle_hook(group) and group not in groups:
                raise CodexAdapterError("Conflit : hook lifecycle VERA Codex existant divergent.")
        additions = [group for group in groups if group not in current]
        if additions:
            result[event] = [*current, *additions]
            changed = True
    if changed:
        merged["hooks"] = result
    return merged, changed


def _contains_codex_lifecycle_hook(group: object) -> bool:
    if not isinstance(group, dict):
        return False
    handlers = group.get("hooks")
    return isinstance(handlers, list) and any(isinstance(item, dict) and isinstance(item.get("command"), str) and item["command"].startswith(CODEX_HOOK_ENTRYPOINT) for item in handlers)


def _merge_codex_config(existing_text: str, server: Mapping[str, object]) -> tuple[str, bool]:
    if not isinstance(existing_text, str):
        raise CodexAdapterError("Configuration TOML Codex invalide.")
    try:
        parsed = tomllib.loads(existing_text) if existing_text else {}
    except tomllib.TOMLDecodeError as exc:
        raise CodexAdapterError("Configuration TOML Codex illisible.") from exc
    if not isinstance(parsed, dict):
        raise CodexAdapterError("Configuration TOML Codex doit être un objet.")
    servers = parsed.get("mcp_servers", {})
    if not isinstance(servers, dict):
        raise CodexAdapterError("mcp_servers Codex doit être une table TOML.")
    server_id = server.get("id")
    desired = {
        "command": server.get("command"), "args": server.get("args"), "cwd": server.get("cwd"),
        "enabled": True, "required": False, "enabled_tools": server.get("enabledTools"),
        "default_tools_approval_mode": "prompt", "startup_timeout_sec": 10, "tool_timeout_sec": 30,
    }
    if not isinstance(server_id, str) or not server_id:
        raise CodexAdapterError("Identifiant MCP Codex invalide.")
    current = servers.get(server_id)
    if current is not None:
        if current != desired:
            raise CodexAdapterError("Conflit : serveur MCP VERA Codex existant divergent.")
        return existing_text if existing_text.endswith("\n") else existing_text + "\n", False
    for name, item in servers.items():
        if isinstance(item, dict) and item.get("command") == CODEX_MCP_ENTRYPOINT:
            raise CodexAdapterError("Conflit : autre serveur VERA Codex déjà déclaré.")
    table = "\n".join((
        f'[mcp_servers.{json.dumps(server_id)}]',
        f'command = {json.dumps(str(desired["command"]))}',
        f'args = {json.dumps(desired["args"], ensure_ascii=False)}',
        f'cwd = {json.dumps(str(desired["cwd"]))}',
        "enabled = true",
        "required = false",
        f'enabled_tools = {json.dumps(desired["enabled_tools"], ensure_ascii=False)}',
        'default_tools_approval_mode = "prompt"',
        "startup_timeout_sec = 10",
        "tool_timeout_sec = 30",
        "",
    ))
    prefix = existing_text.rstrip("\n")
    return (prefix + "\n\n" if prefix else "") + table, True


def _codex_runtime_path(store: MemoryStore, *, create: bool) -> Path:
    target = store.locator.runtime_dir / "generated" / "codex-runtime.json"
    if target.is_symlink():
        raise CodexAdapterError("État runtime Codex symlinké refusé.")
    if create:
        _safe_parent(target.parent, "runtime Codex")
    return target


def _codex_runtime_text(plan: CodexPlan, manifest: MCPManifest) -> str:
    payload = _codex_plan_payload(plan)
    bindings = [
        {"adapter_id": capability.adapter_id, "capability_id": capability.capability_id}
        for capability in manifest.capabilities
    ]
    return _canonical_json({"codexRuntime": {"adapterBindings": bindings, "format": CODEX_RUNTIME_FORMAT, "plan": payload, "planHash": plan.plan_hash}})


def _load_staged_codex_runtime(store: MemoryStore) -> _CodexRuntime:
    raw = _read_optional_text(_codex_runtime_path(store, create=False))
    if raw is None:
        raise CodexAdapterError("Adapter Codex non staged : état attesté absent.")
    try:
        envelope = json.loads(raw)["codexRuntime"]
        if not isinstance(envelope, dict) or envelope.get("format") != CODEX_RUNTIME_FORMAT:
            raise ValueError("format")
        plan_payload = envelope["plan"]
        plan_hash = envelope["planHash"]
        bindings_raw = envelope["adapterBindings"]
        if not isinstance(bindings_raw, list):
            raise ValueError("bindings")
        bindings = {str(item["capability_id"]): str(item["adapter_id"]) for item in bindings_raw}
        if not bindings or len(bindings) != len(bindings_raw):
            raise ValueError("bindings")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise CodexAdapterError("État runtime Codex hors format fermé.") from exc
    manifest = compile_mcp_manifest(store, adapter_bindings=bindings)
    instructions = compile_mcp_instructions(store, manifest)
    integration = compile_mcp_integration(store, manifest, instructions)
    hooks = compile_mcp_hook_plan(store, manifest, instructions, integration)
    lifecycle = compile_lifecycle_adapter_plan(store, manifest, adapter_id=CODEX_ADAPTER_ID, adapter_version=CODEX_ADAPTER_VERSION, maximum_guard_mode=CODEX_MAXIMUM_GUARD_MODE)
    plan = compile_codex_plan(store, manifest, instructions, integration, hooks, lifecycle)
    if plan.plan_hash != plan_hash or plan_payload != json.loads(plan.json_text)["codex"]:
        raise CodexAdapterError("État runtime Codex périmé ou altéré.")
    return _CodexRuntime(manifest, instructions, lifecycle, plan)


def _verify_codex_runtime(store: MemoryStore, lifecycle: LifecycleAdapterPlan, plan: CodexPlan) -> None:
    runtime = _load_staged_codex_runtime(store)
    if lifecycle != runtime.lifecycle or plan != runtime.plan:
        raise CodexAdapterError("Lifecycle Codex étranger au runtime staged.")


def _codex_hooks_path(store: MemoryStore, *, create: bool) -> Path:
    directory = store.workspace.project_root / ".codex"
    if directory.is_symlink():
        raise CodexAdapterError("Répertoire .codex symlinké refusé.")
    if create:
        _safe_parent(directory, "répertoire .codex")
    elif directory.exists() and not directory.is_dir():
        raise CodexAdapterError("Répertoire .codex ambigu ou non régulier.")
    target = directory / "hooks.json"
    if target.is_symlink():
        raise CodexAdapterError("hooks.json Codex symlinké refusé.")
    return target


def _codex_config_path(store: MemoryStore, *, create: bool) -> Path:
    target = _codex_hooks_path(store, create=create).with_name("config.toml")
    if target.is_symlink():
        raise CodexAdapterError("config.toml Codex symlinké refusé.")
    return target


def _codex_host_state_path(store: MemoryStore, *, create: bool) -> Path:
    target = store.locator.runtime_dir / "generated" / "codex-host-config.json"
    if target.is_symlink():
        raise CodexAdapterError("État configuration Codex symlinké refusé.")
    if create:
        _safe_parent(target.parent, "runtime configuration Codex")
    return target


def _codex_host_state_text(preview: CodexHostConfigPreview) -> str:
    return _canonical_json({"codexHostConfig": {"configSha256": sha256(preview.config_toml_text.encode("utf-8")).hexdigest(), "format": CODEX_HOST_CONFIG_FORMAT, "hooksSha256": sha256(preview.hooks_json_text.encode("utf-8")).hexdigest(), "planHash": preview.plan_hash}})


def _session_id(payload: Mapping[str, object]) -> str:
    value = payload.get("session_id")
    if not isinstance(value, str) or not value or len(value) > 256 or "/" in value or "\\" in value:
        raise CodexAdapterError("Identité de session Codex absente ou invalide.")
    return value


def _verify_cwd(store: MemoryStore, value: object) -> None:
    if not isinstance(value, str) or not value:
        raise CodexAdapterError("Répertoire courant Codex absent.")
    try:
        Path(value).resolve(strict=False).relative_to(store.workspace.project_root.resolve(strict=False))
    except ValueError as exc:
        raise CodexAdapterError("Répertoire courant Codex hors projet VERA.") from exc


def _codex_session_path(store: MemoryStore) -> Path:
    target = store.locator.runtime_dir / "lifecycle" / "codex-session.json"
    _safe_parent(target.parent, "runtime lifecycle Codex")
    if target.is_symlink():
        raise CodexAdapterError("Liaison session Codex symlinkée refusée.")
    return target


def _read_codex_session(store: MemoryStore) -> dict[str, str] | None:
    target = _codex_session_path(store)
    if not target.exists():
        return None
    if not target.is_file():
        raise CodexAdapterError("Liaison session Codex non régulière.")
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexAdapterError("Liaison session Codex illisible.") from exc
    if not isinstance(payload, dict) or set(payload) != {"project_id", "session_id"} or payload.get("project_id") != store.identity.project_id or not isinstance(payload.get("session_id"), str):
        raise CodexAdapterError("Liaison session Codex ambiguë, étrangère ou invalide.")
    return {"project_id": store.identity.project_id, "session_id": str(payload["session_id"])}


def _claim_codex_session(store: MemoryStore, session_id: str) -> None:
    existing = _read_codex_session(store)
    candidate = {"project_id": store.identity.project_id, "session_id": session_id}
    if existing is not None and existing != candidate:
        raise CodexAdapterError("Conflit : une autre session Codex est déjà active pour ce projet.")
    if existing is None:
        _atomic_write(_codex_session_path(store), _canonical_json(candidate), ".vera-codex-session-")


def _release_codex_session(store: MemoryStore, session_id: str) -> None:
    target = _codex_session_path(store)
    binding = _read_codex_session(store)
    if binding is not None and binding["session_id"] == session_id:
        try:
            target.unlink()
        except OSError as exc:
            raise CodexAdapterError("Libération session Codex impossible.") from exc


def _compile_codex_dossier(store: MemoryStore):
    return compile_profile_resume_dossier(store, profile_resume_sections(store, "La garde Codex attend un acquittement avant toute action contrôlée."))


def _acknowledgement_tool_names(store: MemoryStore) -> frozenset[str]:
    server_id = f"vera-mmu-{store.identity.project_id}"
    return frozenset(("mmu_acknowledge_resume", f"mcp__{server_id}__mmu_acknowledge_resume"))


def _context(text: str) -> dict[str, object]:
    """Codex accepts bounded additional context for lifecycle hook events."""
    return {"additionalContext": text[:12_000], "systemMessage": "VERA lifecycle context injected."}


def _load_json_object(target: Path, label: str) -> dict[str, Any]:
    raw = _read_optional_text(target)
    if raw is None:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CodexAdapterError(f"{label} illisible.") from exc
    return _json_object_copy(parsed, label)


def _json_object_copy(value: Mapping[str, Any], label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise CodexAdapterError(f"{label} doit être un objet JSON.")
    try:
        copied = json.loads(json.dumps(dict(value), ensure_ascii=False))
    except (TypeError, ValueError) as exc:
        raise CodexAdapterError(f"{label} non sérialisable en JSON.") from exc
    if not isinstance(copied, dict):
        raise CodexAdapterError(f"{label} doit être un objet JSON.")
    return copied


def _read_optional_text(target: Path) -> str | None:
    if not target.exists():
        return None
    if target.is_symlink() or not target.is_file():
        raise CodexAdapterError("État Codex non régulier.")
    try:
        return target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise CodexAdapterError("État Codex illisible.") from exc


def _safe_parent(directory: Path, label: str) -> None:
    if directory.is_symlink():
        raise CodexAdapterError(f"{label} symlinké refusé.")
    try:
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    except OSError as exc:
        raise CodexAdapterError(f"Création de {label} impossible.") from exc
    if not directory.is_dir() or directory.is_symlink():
        raise CodexAdapterError(f"{label} ambigu ou non régulier.")


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _atomic_write(target: Path, text: str, prefix: str) -> None:
    _safe_parent(target.parent, "répertoire cible Codex")
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
        raise CodexAdapterError("Écriture atomique Codex impossible.") from exc


if __name__ == "__main__":
    raise SystemExit(codex_hook_main())

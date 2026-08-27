"""Claude Code local lifecycle adapter: attested plan, fixed hooks, opt-in install, and doctor.

This module is intentionally local-only.  It never touches user/home settings, performs no
network/bootstrap/synchronization, and never selects a Domain Pack or executes a capability.
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
from .lifecycle_adapters import LifecycleAdapterPlan, LifecycleAdapterRegistry, compile_lifecycle_adapter_plan
from .mcp_hooks import MCPHookPlan, MCPHookPlanError, compile_mcp_hook_plan
from .mcp_instructions import MCPInstructions, MCPInstructionsError, compile_mcp_instructions
from .mcp_integration import MCPIntegration, MCPIntegrationError, compile_mcp_integration
from .mcp_manifest import MCPManifest, MCPManifestError, compile_mcp_manifest, verify_mcp_manifest
from .mcp_server import DenyRuntimeAdapter, create_server
from .session_lifecycle import GuardDecision, ResumeDossierService, ResumeGuardService, ResumeSectionRequirement
from .profile_resume import compile_profile_resume_dossier, profile_resume_sections
from .store import MemoryStore, StoreError


CLAUDE_CODE_LOCAL_FORMAT = "vera-claude-code-local/v1"
CLAUDE_CODE_LOCAL_ADAPTER_ID = "claude-code-local-v1"
CLAUDE_CODE_LOCAL_ADAPTER_VERSION = "1.0.0"
CLAUDE_CODE_LOCAL_MAXIMUM_GUARD_MODE = "HARD"
HOOK_ENTRYPOINT = "vmmu-claude-code-local-hook"
MCP_ENTRYPOINT = "vmmu-claude-code-local-mcp"
_EVENTS = ("SessionStart", "PreToolUse", "PostToolUse", "PreCompact", "PostCompact", "Stop")


class ClaudeCodeLocalError(StoreError):
    """The local Claude lifecycle adapter cannot be compiled, installed, or invoked safely."""


@dataclass(frozen=True)
class ClaudeCodeLocalPlan:
    """Canonical local-only host plan, bound to all upstream snapshots and adapter bindings."""

    format: str
    project_id: str
    mcp_build_hash: str
    instructions_hash: str
    config_hash: str
    hook_plan_hash: str
    review_plan_hash: str
    lifecycle_plan_hash: str
    adapter_bindings: tuple[tuple[str, str], ...]
    plan_hash: str
    json_text: str


@dataclass(frozen=True)
class ClaudeCodeLocalInstallResult:
    status: str
    settings_path: Path
    mcp_path: Path
    state_path: Path
    plan_hash: str


@dataclass(frozen=True)
class ClaudeCodeLocalDoctorReport:
    status: str
    checks: tuple[tuple[str, str], ...]
    install_actions: tuple[str, ...]


class ClaudeCodeLocalSessionAdapter:
    """Read the single active Claude local session recorded by a verified SessionStart hook."""

    adapter_id = CLAUDE_CODE_LOCAL_ADAPTER_ID
    adapter_version = CLAUDE_CODE_LOCAL_ADAPTER_VERSION
    maximum_guard_mode = CLAUDE_CODE_LOCAL_MAXIMUM_GUARD_MODE

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def session_identity(self) -> str | None:
        binding = _read_session_binding(self.store)
        return None if binding is None else binding["session_id"]


def compile_claude_code_local_plan(
    store: MemoryStore,
    manifest: MCPManifest,
    instructions: MCPInstructions,
    integration: MCPIntegration,
    hooks: MCPHookPlan,
    review: ClaudeCodeIntegrationPlan,
    lifecycle: LifecycleAdapterPlan,
) -> ClaudeCodeLocalPlan:
    """Compile the only local Claude adapter plan from fully verified snapshots."""
    if not isinstance(store, MemoryStore):
        raise ClaudeCodeLocalError("Store invalide pour l’adapter Claude local.")
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
            adapter_id=CLAUDE_CODE_LOCAL_ADAPTER_ID,
            adapter_version=CLAUDE_CODE_LOCAL_ADAPTER_VERSION,
            maximum_guard_mode=CLAUDE_CODE_LOCAL_MAXIMUM_GUARD_MODE,
        )
    except (MCPManifestError, MCPInstructionsError, MCPIntegrationError, MCPHookPlanError, ClaudeCodeIntegrationError, StoreError) as exc:
        raise ClaudeCodeLocalError("Snapshots invalides pour l’adapter Claude local.") from exc
    if (
        instructions != expected_instructions
        or integration != expected_integration
        or hooks != expected_hooks
        or review != expected_review
        or lifecycle != expected_lifecycle
    ):
        raise ClaudeCodeLocalError("Snapshot Claude local périmé, altéré ou étranger.")
    bindings = tuple((item.capability_id, item.adapter_id) for item in manifest.capabilities)
    server_id, generic_server = _single_server(integration)
    profile_argument = _profile_argument(generic_server)
    local_server = {
        "args": ["--profile", profile_argument],
        "command": MCP_ENTRYPOINT,
        "env": {
            "VERA_CLAUDE_CODE_LOCAL": "1",
            "VERA_MCP_BUILD_HASH": manifest.mcp_build_hash,
            "VERA_MCP_INSTRUCTIONS_HASH": instructions.instructions_hash,
            "VERA_PROJECT_ID": store.identity.project_id,
        },
    }
    hook_commands = _hook_commands(store, server_id, profile_argument)
    payload = {
        "claudeCodeLocal": {
            "adapter": {
                "id": CLAUDE_CODE_LOCAL_ADAPTER_ID,
                "maximum_guard_mode": CLAUDE_CODE_LOCAL_MAXIMUM_GUARD_MODE,
                "version": CLAUDE_CODE_LOCAL_ADAPTER_VERSION,
            },
            "adapterBindings": [{"adapter_id": adapter_id, "capability_id": capability_id} for capability_id, adapter_id in bindings],
            "hooks": hook_commands,
            "installation": {"mcpTarget": ".mcp.json", "mode": "OPT_IN", "settingsTarget": ".claude/settings.json"},
            "mcpServer": {"id": server_id, **local_server},
        }
    }
    json_text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    return ClaudeCodeLocalPlan(
        format=CLAUDE_CODE_LOCAL_FORMAT,
        project_id=store.identity.project_id,
        mcp_build_hash=manifest.mcp_build_hash,
        instructions_hash=instructions.instructions_hash,
        config_hash=integration.config_hash,
        hook_plan_hash=hooks.hook_plan_hash,
        review_plan_hash=review.plan_hash,
        lifecycle_plan_hash=lifecycle.lifecycle_plan_hash,
        adapter_bindings=bindings,
        plan_hash=sha256(json_text.encode("utf-8")).hexdigest(),
        json_text=json_text,
    )


def handle_claude_code_local_hook(
    store: MemoryStore,
    lifecycle: LifecycleAdapterPlan,
    plan: ClaudeCodeLocalPlan,
    event: str,
    payload: Mapping[str, object],
) -> dict[str, object]:
    """Translate one fixed Claude event into the local Core lifecycle without shell semantics."""
    _verify_local_plan(store, lifecycle, plan)
    if event not in _EVENTS or not isinstance(payload, Mapping):
        raise ClaudeCodeLocalError("Événement ou payload Claude local invalide.")
    session_id = payload.get("session_id")
    if not isinstance(session_id, str) or not session_id or len(session_id) > 256 or "/" in session_id or "\\" in session_id:
        raise ClaudeCodeLocalError("Identité de session Claude locale absente ou invalide.")
    _verify_cwd(store, payload.get("cwd"))
    guard = ResumeGuardService(store)
    if event == "SessionStart":
        _claim_session(store, session_id)
        source = payload.get("source")
        reason = "RESUME" if source == "resume" else "SESSION_OPEN" if source == "startup" else "CONTEXT_RESTORED"
        dossier = _compile_resume_dossier(store)
        guard.arm(session_id, CLAUDE_CODE_LOCAL_ADAPTER_ID, reason, dossier, mode="HARD")
        return _context(event, "Resume Dossier VERA — lire et acquitter via mmu_acknowledge_resume :\n" + dossier.json_text)
    if _read_session_binding(store) != {"project_id": store.identity.project_id, "session_id": session_id}:
        raise ClaudeCodeLocalError("Session Claude locale non liée au runtime courant.")
    if event == "PreToolUse":
        tool_name = payload.get("tool_name")
        if not isinstance(tool_name, str):
            raise ClaudeCodeLocalError("PreToolUse Claude sans nom de tool.")
        if tool_name == _acknowledgement_tool_name(store):
            return _empty(event)
        outcome = guard.precheck(session_id, CLAUDE_CODE_LOCAL_ADAPTER_ID)
        if outcome.decision == GuardDecision.DENY:
            return _deny(event, outcome.reason)
        if outcome.decision == GuardDecision.ALLOW_WITH_NOTICE:
            return _context(event, outcome.reason)
        return _empty(event)
    if event == "PostToolUse":
        outcome = guard.precheck(session_id, CLAUDE_CODE_LOCAL_ADAPTER_ID)
        return _context(event, outcome.reason) if outcome.decision != GuardDecision.ALLOW else _empty(event)
    if event == "PreCompact":
        dossier = _compile_resume_dossier(store)
        guard.arm(session_id, CLAUDE_CODE_LOCAL_ADAPTER_ID, "CONTEXT_PREPARE", dossier, mode="HARD")
        return _context(event, "VERA prépare la reprise de contexte ; le dossier devra être acquitté après compaction.")
    if event == "PostCompact":
        dossier = _compile_resume_dossier(store)
        guard.arm(session_id, CLAUDE_CODE_LOCAL_ADAPTER_ID, "CONTEXT_RESTORED", dossier, mode="HARD")
        return _context(event, "Resume Dossier VERA — lire et acquitter via mmu_acknowledge_resume :\n" + dossier.json_text)
    outcome = guard.session_ending(session_id, CLAUDE_CODE_LOCAL_ADAPTER_ID, already_nudged=False)
    _release_session(store, session_id)
    return _context(event, outcome.reason) if outcome.decision == GuardDecision.NUDGE else _empty(event)


def install_claude_code_local(
    store: MemoryStore,
    manifest: MCPManifest,
    instructions: MCPInstructions,
    integration: MCPIntegration,
    hooks: MCPHookPlan,
    review: ClaudeCodeIntegrationPlan,
    lifecycle: LifecycleAdapterPlan,
    plan: ClaudeCodeLocalPlan,
    *,
    confirm: bool,
) -> ClaudeCodeLocalInstallResult:
    """Install only the attested project-local hooks and local VERA MCP server after confirmation."""
    if confirm is not True:
        raise ClaudeCodeLocalError("Installation Claude locale refusée sans confirmation explicite.")
    expected = compile_claude_code_local_plan(store, manifest, instructions, integration, hooks, review, lifecycle)
    if plan != expected:
        raise ClaudeCodeLocalError("Plan Claude local périmé, altéré ou étranger.")
    settings_path = _settings_target(store)
    mcp_path = _mcp_target(store)
    state_path = _installation_state_path(store)
    settings = _load_json_object(settings_path, "settings Claude")
    mcp = _load_json_object(mcp_path, "configuration MCP")
    desired_hooks = _plan_payload(plan)["hooks"]
    desired_server = _plan_payload(plan)["mcpServer"]
    generic_server = _single_server(integration)[1]
    merged_settings, settings_changed = _merge_hooks(settings, desired_hooks)
    merged_mcp, mcp_changed = _merge_local_server(mcp, desired_server, generic_server)
    existing_state = _read_optional_text(state_path)
    if existing_state is not None and existing_state != plan.json_text:
        raise ClaudeCodeLocalError("État d’installation lifecycle local divergent : refus sans écriture.")
    if not settings_changed and not mcp_changed and existing_state == plan.json_text:
        return ClaudeCodeLocalInstallResult("UNCHANGED", settings_path, mcp_path, state_path, plan.plan_hash)
    if settings_changed:
        _atomic_write(settings_path, _canonical_json(merged_settings), ".vera-claude-settings-")
    if mcp_changed:
        _atomic_write(mcp_path, _canonical_json(merged_mcp), ".vera-claude-mcp-")
    if existing_state is None:
        _atomic_write(state_path, plan.json_text, ".vera-claude-state-")
    return ClaudeCodeLocalInstallResult("INSTALLED", settings_path, mcp_path, state_path, plan.plan_hash)


def inspect_claude_code_local(
    store: MemoryStore,
    manifest: MCPManifest,
    instructions: MCPInstructions,
    integration: MCPIntegration,
    hooks: MCPHookPlan,
    review: ClaudeCodeIntegrationPlan,
    lifecycle: LifecycleAdapterPlan,
    plan: ClaudeCodeLocalPlan,
    *,
    command_lookup: Callable[[str], str | None] = shutil.which,
) -> ClaudeCodeLocalDoctorReport:
    """Observe exact local installation state; never install, approve, or repair."""
    expected = compile_claude_code_local_plan(store, manifest, instructions, integration, hooks, review, lifecycle)
    if plan != expected:
        raise ClaudeCodeLocalError("Plan Claude local périmé, altéré ou étranger.")
    checks: list[tuple[str, str]] = []
    settings_path = _settings_target(store, create=False)
    mcp_path = _mcp_target(store)
    state_path = _installation_state_path(store, create=False)
    expected_payload = _plan_payload(plan)
    settings = _load_json_object(settings_path, "settings Claude")
    mcp = _load_json_object(mcp_path, "configuration MCP")
    hooks_ok = _hooks_installed(settings, expected_payload["hooks"])
    server_ok = _server_installed(mcp, expected_payload["mcpServer"])
    state_ok = _read_optional_text(state_path) == plan.json_text
    checks.extend((("hooks", "PASS" if hooks_ok else "MISSING"), ("mcp", "PASS" if server_ok else "MISSING"), ("state", "PASS" if state_ok else "MISSING")))
    if not hooks_ok and not server_ok and not state_ok:
        return ClaudeCodeLocalDoctorReport("NOT_INSTALLED", tuple(checks), ())
    hook_entrypoint = command_lookup(HOOK_ENTRYPOINT)
    mcp_entrypoint = command_lookup(MCP_ENTRYPOINT)
    checks.extend((("hook_entrypoint", "PASS" if hook_entrypoint else "MISSING"), ("mcp_entrypoint", "PASS" if mcp_entrypoint else "MISSING")))
    if hooks_ok and server_ok and state_ok and hook_entrypoint and mcp_entrypoint:
        return ClaudeCodeLocalDoctorReport("READY", tuple(checks), ())
    return ClaudeCodeLocalDoctorReport("DEGRADED", tuple(checks), ())


def _verify_local_plan(store: MemoryStore, lifecycle: LifecycleAdapterPlan, plan: ClaudeCodeLocalPlan) -> None:
    bindings = dict(plan.adapter_bindings)
    try:
        manifest = compile_mcp_manifest(store, adapter_bindings=bindings)
        instructions = compile_mcp_instructions(store, manifest)
        integration = compile_mcp_integration(store, manifest, instructions)
        hooks = compile_mcp_hook_plan(store, manifest, instructions, integration)
        review = compile_claude_code_integration_plan(store, manifest, instructions, integration, hooks)
        expected_lifecycle = compile_lifecycle_adapter_plan(
            store,
            manifest,
            adapter_id=CLAUDE_CODE_LOCAL_ADAPTER_ID,
            adapter_version=CLAUDE_CODE_LOCAL_ADAPTER_VERSION,
            maximum_guard_mode=CLAUDE_CODE_LOCAL_MAXIMUM_GUARD_MODE,
        )
        expected = compile_claude_code_local_plan(store, manifest, instructions, integration, hooks, review, expected_lifecycle)
    except StoreError as exc:
        raise ClaudeCodeLocalError("Plan lifecycle Claude local invérifiable.") from exc
    if lifecycle != expected_lifecycle or plan != expected:
        raise ClaudeCodeLocalError("Plan lifecycle Claude local périmé, altéré ou étranger.")


def _single_server(integration: MCPIntegration) -> tuple[str, dict[str, object]]:
    try:
        payload = json.loads(integration.json_text)
        servers = payload["mcpServers"]
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ClaudeCodeLocalError("Configuration MCP attestée illisible.") from exc
    if not isinstance(servers, dict) or len(servers) != 1:
        raise ClaudeCodeLocalError("Configuration MCP attestée doit contenir un serveur unique.")
    identifier, server = next(iter(servers.items()))
    if not isinstance(identifier, str) or not isinstance(server, dict):
        raise ClaudeCodeLocalError("Serveur MCP attesté invalide.")
    return identifier, dict(server)


def _profile_argument(server: Mapping[str, object]) -> str:
    args = server.get("args")
    if not isinstance(args, list) or len(args) != 2 or args[0] != "--profile" or not isinstance(args[1], str):
        raise ClaudeCodeLocalError("Argument de profil MCP attesté invalide.")
    return args[1]


def _hook_commands(store: MemoryStore, server_id: str, profile_argument: str) -> dict[str, list[dict[str, object]]]:
    if not server_id.startswith("vera-mmu-"):
        raise ClaudeCodeLocalError("Identifiant serveur VERA local invalide.")
    def group(event: str, *, matcher: str | None = None) -> dict[str, object]:
        command = f'{HOOK_ENTRYPOINT} --profile "{profile_argument}" --event {event}'
        handler: dict[str, object] = {"command": command, "timeout": 10, "type": "command"}
        payload: dict[str, object] = {"hooks": [handler]}
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


def _compile_resume_dossier(store: MemoryStore):
    return compile_profile_resume_dossier(store, profile_resume_sections(store, "La garde Claude locale attend un acquittement avant toute action contrôlée."))


def _context(event: str, text: str) -> dict[str, object]:
    bounded = text[:12_000]
    return {"hookSpecificOutput": {"additionalContext": bounded, "hookEventName": event}}


def _empty(event: str) -> dict[str, object]:
    return {"hookSpecificOutput": {"hookEventName": event}}


def _deny(event: str, reason: str) -> dict[str, object]:
    return {"hookSpecificOutput": {"hookEventName": event, "permissionDecision": "deny", "permissionDecisionReason": reason}}


def _verify_cwd(store: MemoryStore, value: object) -> None:
    if not isinstance(value, str) or not value:
        raise ClaudeCodeLocalError("Répertoire courant Claude local absent.")
    try:
        Path(value).resolve(strict=False).relative_to(store.workspace.project_root.resolve(strict=False))
    except ValueError as exc:
        raise ClaudeCodeLocalError("Répertoire courant Claude hors projet VERA.") from exc


def _session_binding_path(store: MemoryStore) -> Path:
    target = store.locator.runtime_dir / "lifecycle" / "claude-code-local-session.json"
    _safe_parent(target.parent, "runtime lifecycle")
    if target.is_symlink():
        raise ClaudeCodeLocalError("Liaison de session Claude symlinkée refusée.")
    return target


def _read_session_binding(store: MemoryStore) -> dict[str, str] | None:
    target = _session_binding_path(store)
    if not target.exists():
        return None
    if not target.is_file():
        raise ClaudeCodeLocalError("Liaison de session Claude non régulière.")
    try:
        parsed = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClaudeCodeLocalError("Liaison de session Claude illisible.") from exc
    if not isinstance(parsed, dict) or set(parsed) != {"project_id", "session_id"}:
        raise ClaudeCodeLocalError("Liaison de session Claude ambiguë.")
    if parsed.get("project_id") != store.identity.project_id or not isinstance(parsed.get("session_id"), str):
        raise ClaudeCodeLocalError("Liaison de session Claude étrangère ou invalide.")
    return {"project_id": store.identity.project_id, "session_id": str(parsed["session_id"])}


def _claim_session(store: MemoryStore, session_id: str) -> None:
    existing = _read_session_binding(store)
    candidate = {"project_id": store.identity.project_id, "session_id": session_id}
    if existing is not None and existing != candidate:
        raise ClaudeCodeLocalError("Conflit : une autre session Claude locale est déjà active pour ce projet.")
    if existing is None:
        _atomic_write(_session_binding_path(store), _canonical_json(candidate), ".vera-claude-session-")


def _release_session(store: MemoryStore, session_id: str) -> None:
    target = _session_binding_path(store)
    binding = _read_session_binding(store)
    if binding is not None and binding["session_id"] == session_id:
        try:
            target.unlink()
        except OSError as exc:
            raise ClaudeCodeLocalError("Libération de session Claude locale impossible.") from exc


def _acknowledgement_tool_name(store: MemoryStore) -> str:
    return f"mcp__vera-mmu-{store.identity.project_id}__mmu_acknowledge_resume"


def _settings_target(store: MemoryStore, *, create: bool = True) -> Path:
    directory = store.workspace.project_root / ".claude"
    if directory.is_symlink():
        raise ClaudeCodeLocalError("Répertoire .claude symlinké refusé.")
    if create:
        _safe_parent(directory, "répertoire .claude")
    elif directory.exists() and not directory.is_dir():
        raise ClaudeCodeLocalError("Répertoire .claude ambigu ou non régulier.")
    target = directory / "settings.json"
    if target.is_symlink():
        raise ClaudeCodeLocalError("La cible .claude/settings.json ne peut pas être un lien symbolique.")
    return target


def _mcp_target(store: MemoryStore) -> Path:
    target = store.workspace.project_root / ".mcp.json"
    if target.is_symlink():
        raise ClaudeCodeLocalError("La cible .mcp.json ne peut pas être un lien symbolique.")
    return target


def _installation_state_path(store: MemoryStore, *, create: bool = True) -> Path:
    target = store.locator.runtime_dir / "generated" / "claude-code-local-install.json"
    if target.parent.is_symlink():
        raise ClaudeCodeLocalError("Runtime généré symlinké refusé.")
    if create:
        _safe_parent(target.parent, "runtime généré")
    elif target.parent.exists() and not target.parent.is_dir():
        raise ClaudeCodeLocalError("Runtime généré ambigu ou non régulier.")
    if target.is_symlink():
        raise ClaudeCodeLocalError("État d’installation Claude local symlinké refusé.")
    return target


def _safe_parent(directory: Path, label: str) -> None:
    if directory.is_symlink():
        raise ClaudeCodeLocalError(f"{label} symlinké refusé.")
    try:
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    except OSError as exc:
        raise ClaudeCodeLocalError(f"Création de {label} impossible.") from exc
    if not directory.is_dir() or directory.is_symlink():
        raise ClaudeCodeLocalError(f"{label} ambigu ou non régulier.")


def _load_json_object(target: Path, label: str) -> dict[str, Any]:
    if not target.exists():
        return {}
    if not target.is_file():
        raise ClaudeCodeLocalError(f"La cible {label} doit être un fichier régulier.")
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClaudeCodeLocalError(f"La cible {label} n’est pas un JSON lisible.") from exc
    if not isinstance(value, dict):
        raise ClaudeCodeLocalError(f"La cible {label} doit contenir un objet JSON.")
    return value


def _read_optional_text(target: Path) -> str | None:
    if not target.exists():
        return None
    if not target.is_file() or target.is_symlink():
        raise ClaudeCodeLocalError("État d’installation Claude local non régulier.")
    try:
        return target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ClaudeCodeLocalError("État d’installation Claude local illisible.") from exc


def _plan_payload(plan: ClaudeCodeLocalPlan) -> dict[str, Any]:
    if not isinstance(plan, ClaudeCodeLocalPlan) or plan.plan_hash != sha256(plan.json_text.encode("utf-8")).hexdigest():
        raise ClaudeCodeLocalError("Plan Claude local altéré.")
    try:
        payload = json.loads(plan.json_text)
        result = payload["claudeCodeLocal"]
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ClaudeCodeLocalError("Plan Claude local illisible.") from exc
    if not isinstance(result, dict):
        raise ClaudeCodeLocalError("Plan Claude local hors format fermé.")
    return result


def _merge_hooks(existing: dict[str, Any], desired: object) -> tuple[dict[str, Any], bool]:
    if not isinstance(desired, dict):
        raise ClaudeCodeLocalError("Hooks Claude locaux attestés invalides.")
    existing_hooks = existing.get("hooks", {})
    if not isinstance(existing_hooks, dict):
        raise ClaudeCodeLocalError("hooks existant doit être un objet JSON.")
    merged = dict(existing)
    hooks = {key: list(value) if isinstance(value, list) else value for key, value in existing_hooks.items()}
    changed = False
    for event, groups in desired.items():
        if not isinstance(event, str) or not isinstance(groups, list):
            raise ClaudeCodeLocalError("Groupe de hook Claude local invalide.")
        current = hooks.get(event, [])
        if not isinstance(current, list):
            raise ClaudeCodeLocalError("Événement de hooks existant doit être une liste.")
        for group in current:
            if _contains_vera_hook(group) and group not in groups:
                raise ClaudeCodeLocalError("Conflit : hook VERA Claude local existant divergent.")
        additions = [group for group in groups if group not in current]
        if additions:
            hooks[event] = [*current, *additions]
            changed = True
    if changed:
        merged["hooks"] = hooks
    return merged, changed


def _contains_vera_hook(group: object) -> bool:
    if not isinstance(group, dict):
        return False
    handlers = group.get("hooks")
    return isinstance(handlers, list) and any(
        isinstance(handler, dict) and isinstance(handler.get("command"), str) and handler["command"].startswith(HOOK_ENTRYPOINT + " ")
        for handler in handlers
    )


def _merge_local_server(existing: dict[str, Any], desired: object, generic: Mapping[str, object]) -> tuple[dict[str, Any], bool]:
    if not isinstance(desired, dict):
        raise ClaudeCodeLocalError("Serveur MCP Claude local attesté invalide.")
    server_id = desired.get("id")
    server = {key: value for key, value in desired.items() if key != "id"}
    if not isinstance(server_id, str) or not server_id:
        raise ClaudeCodeLocalError("Identifiant serveur MCP Claude local invalide.")
    servers = existing.get("mcpServers", {})
    if not isinstance(servers, dict):
        raise ClaudeCodeLocalError("mcpServers existant doit être un objet JSON.")
    current = servers.get(server_id)
    if current == server:
        return existing, False
    if current is not None and current != generic:
        raise ClaudeCodeLocalError("Conflit : serveur MCP VERA existant divergent.")
    merged = dict(existing)
    merged_servers = dict(servers)
    merged_servers[server_id] = server
    merged["mcpServers"] = merged_servers
    return merged, True


def _hooks_installed(settings: Mapping[str, object], desired: object) -> bool:
    return isinstance(desired, dict) and isinstance(settings.get("hooks"), dict) and all(
        isinstance(settings["hooks"].get(event), list) and all(group in settings["hooks"][event] for group in groups)
        for event, groups in desired.items()
    )


def _server_installed(mcp: Mapping[str, object], desired: object) -> bool:
    if not isinstance(desired, dict):
        return False
    server_id = desired.get("id")
    server = {key: value for key, value in desired.items() if key != "id"}
    servers = mcp.get("mcpServers")
    return isinstance(server_id, str) and isinstance(servers, dict) and servers.get(server_id) == server


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _atomic_write(target: Path, text: str, prefix: str) -> None:
    _safe_parent(target.parent, "répertoire cible")
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
        raise ClaudeCodeLocalError("Écriture atomique Claude locale impossible.") from exc


def _load_installed_plan(store: MemoryStore) -> ClaudeCodeLocalPlan:
    raw = _read_optional_text(_installation_state_path(store))
    if raw is None:
        raise ClaudeCodeLocalError("Adapter Claude local non installé : état attesté absent.")
    try:
        payload = json.loads(raw)["claudeCodeLocal"]
        bindings = tuple((str(item["capability_id"]), str(item["adapter_id"])) for item in payload["adapterBindings"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ClaudeCodeLocalError("État d’installation Claude local hors format fermé.") from exc
    manifest = compile_mcp_manifest(store, adapter_bindings=dict(bindings))
    instructions = compile_mcp_instructions(store, manifest)
    integration = compile_mcp_integration(store, manifest, instructions)
    hooks = compile_mcp_hook_plan(store, manifest, instructions, integration)
    review = compile_claude_code_integration_plan(store, manifest, instructions, integration, hooks)
    lifecycle = compile_lifecycle_adapter_plan(
        store,
        manifest,
        adapter_id=CLAUDE_CODE_LOCAL_ADAPTER_ID,
        adapter_version=CLAUDE_CODE_LOCAL_ADAPTER_VERSION,
        maximum_guard_mode=CLAUDE_CODE_LOCAL_MAXIMUM_GUARD_MODE,
    )
    plan = compile_claude_code_local_plan(store, manifest, instructions, integration, hooks, review, lifecycle)
    if plan.json_text != raw:
        raise ClaudeCodeLocalError("État d’installation Claude local périmé ou altéré.")
    return plan


def claude_code_local_hook_main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hook lifecycle Claude Code local VERA-MMU")
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--event", choices=_EVENTS, required=True)
    args = parser.parse_args(argv)
    try:
        payload = json.loads(sys.stdin.read())
        if not isinstance(payload, dict):
            raise ClaudeCodeLocalError("Payload JSON de hook Claude requis.")
        from .identity import load_profile
        with MemoryStore.open(load_profile(args.profile), args.profile) as store:
            plan = _load_installed_plan(store)
            manifest = compile_mcp_manifest(store, adapter_bindings=dict(plan.adapter_bindings))
            lifecycle = compile_lifecycle_adapter_plan(
                store,
                manifest,
                adapter_id=CLAUDE_CODE_LOCAL_ADAPTER_ID,
                adapter_version=CLAUDE_CODE_LOCAL_ADAPTER_VERSION,
                maximum_guard_mode=CLAUDE_CODE_LOCAL_MAXIMUM_GUARD_MODE,
            )
            response = handle_claude_code_local_hook(store, lifecycle, plan, args.event, payload)
    except (StoreError, json.JSONDecodeError) as exc:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": args.event, "permissionDecision": "deny", "permissionDecisionReason": str(exc)}}, ensure_ascii=False))
        return 2
    print(json.dumps(response, ensure_ascii=False, sort_keys=True))
    return 0


def claude_code_local_mcp_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Serveur MCP lifecycle Claude Code local VERA-MMU")
    parser.add_argument("--profile", type=Path, required=True)
    args = parser.parse_args(argv)
    from .identity import load_profile
    with MemoryStore.open(load_profile(args.profile), args.profile) as store:
        plan = _load_installed_plan(store)
        manifest = compile_mcp_manifest(store, adapter_bindings=dict(plan.adapter_bindings))
        instructions = compile_mcp_instructions(store, manifest)
        lifecycle = compile_lifecycle_adapter_plan(
            store,
            manifest,
            adapter_id=CLAUDE_CODE_LOCAL_ADAPTER_ID,
            adapter_version=CLAUDE_CODE_LOCAL_ADAPTER_VERSION,
            maximum_guard_mode=CLAUDE_CODE_LOCAL_MAXIMUM_GUARD_MODE,
        )
        server = create_server(
            store,
            runtime_adapter=DenyRuntimeAdapter(),
            manifest=manifest,
            instructions=instructions,
            lifecycle_adapter_registry=LifecycleAdapterRegistry((ClaudeCodeLocalSessionAdapter(store),)),
            lifecycle_adapter_plan=lifecycle,
            actor="vera-claude-code-local",
        )
        server.run("stdio")


if __name__ == "__main__":
    raise SystemExit(claude_code_local_hook_main())

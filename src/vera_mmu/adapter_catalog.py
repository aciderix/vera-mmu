"""Immutable catalog of installed VERA adapter entry points for trusted callers."""
from __future__ import annotations

from contextlib import redirect_stdout
from dataclasses import dataclass
from io import StringIO
import json
from typing import Mapping

from .store import StoreError


@dataclass(frozen=True)
class AdapterSpec:
    coverage: str
    runtime: str
    config: str
    stage_entry: str
    configure_entry: str


ADAPTER_CATALOG: Mapping[str, AdapterSpec] = {
    "claude-code-local": AdapterSpec("COMPACTION_AWARE", "claude-code-local-runtime.json", ".claude/settings.json", "vera_mmu.claude_code_local:claude_code_local_stage_main", "vera_mmu.claude_code_local:claude_code_local_config_main"),
    "claude-code-cloud": AdapterSpec("CLOUD_STAGED_NOT_LIVE", "claude-code-cloud-runtime.json", ".claude/settings.json + .mcp.json", "vera_mmu.claude_code_cloud:claude_code_cloud_stage_main", "vera_mmu.claude_code_cloud:claude_code_cloud_config_main"),
    "codex": AdapterSpec("PARTIAL_LOCAL_TOOLS", "codex-runtime.json", ".codex/hooks.json + .codex/config.toml", "vera_mmu.codex_adapter:codex_stage_main", "vera_mmu.codex_adapter:codex_config_main"),
    "gemini": AdapterSpec("TOOL_GUARD_NO_POST_COMPACTION", "gemini-cli-runtime.json", ".gemini/settings.json", "vera_mmu.gemini_adapter:gemini_stage_main", "vera_mmu.gemini_adapter:gemini_config_main"),
    "antigravity": AdapterSpec("TURN_GUARD_HARD", "antigravity-runtime.json", ".antigravity/settings.json", "vera_mmu.antigravity_adapter:antigravity_stage_main", "vera_mmu.antigravity_adapter:antigravity_config_main"),
    "generic-mcp": AdapterSpec("MCP_ONLY", "generic-mcp-runtime.json", ".mcp.json", "vera_mmu.generic_mcp_adapter:generic_mcp_stage_main", "vera_mmu.generic_mcp_adapter:generic_mcp_config_main"),
}


def adapter_spec(adapter: str) -> AdapterSpec:
    value = ADAPTER_CATALOG.get(adapter)
    if value is None:
        raise StoreError(f"Adapter inconnu : {adapter}.")
    return value


def call_adapter(entry: str, args: list[str]) -> int:
    module_name, function_name = entry.split(":", 1)
    module = __import__(module_name, fromlist=[function_name])
    function = getattr(module, function_name)
    if not callable(function):
        raise StoreError("Entry point d’adapter invalide.")
    return int(function(args))


def call_adapter_json(entry: str, args: list[str]) -> tuple[int, dict[str, object]]:
    stream = StringIO()
    with redirect_stdout(stream):
        code = call_adapter(entry, args)
    try:
        payload = json.loads(stream.getvalue())
    except json.JSONDecodeError as exc:
        raise StoreError("Réponse adapter non JSON.") from exc
    if not isinstance(payload, dict):
        raise StoreError("Réponse adapter non objet.")
    return code, payload

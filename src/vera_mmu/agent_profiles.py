"""Declarative, bounded agent-profile manifests; adapters remain installed code."""
from __future__ import annotations
from dataclasses import dataclass
import json,re
from typing import Any,Mapping
from .store import StoreError
PROFILE_FORMAT="vera-agent-profile/v1"
_ID=re.compile(r"[a-z][a-z0-9-]{1,63}")
_ALLOWED={"claude-code-local":("COMPACTION_AWARE",("SessionStart","PreToolUse","PostToolUse","PreCompact","PostCompact","Stop")),"claude-code-cloud":("CLOUD_STAGED_NOT_LIVE",("SessionStart","PreToolUse","PostToolUse","PreCompact","PostCompact","Stop")),"codex":("PARTIAL_LOCAL_TOOLS",("SessionStart","PreToolUse","PostToolUse","PreCompact","PostCompact","Stop")),"gemini":("TOOL_GUARD_NO_POST_COMPACTION",("SessionStart","BeforeTool","AfterTool","PreCompress","SessionEnd")),"antigravity":("TURN_GUARD_HARD",("PreInvocation","PreToolUse","PostToolUse","Stop")),"generic-mcp":("MCP_ONLY",())}
_RANK={"MCP_ONLY":0,"TOOL_GUARD_NO_POST_COMPACTION":1,"PARTIAL_LOCAL_TOOLS":2,"TURN_GUARD_HARD":3,"COMPACTION_AWARE":4,"CLOUD_STAGED_NOT_LIVE":4}
class AgentProfileError(StoreError):pass
@dataclass(frozen=True)
class AgentProfile:
    format:str;id:str;label:str;adapter:str;mode:str;coverage:str;events:tuple[str,...]
    def as_dict(self)->dict[str,object]:return {"format":self.format,"id":self.id,"label":self.label,"adapter":self.adapter,"mode":self.mode,"coverage":self.coverage,"events":list(self.events)}
def validate_agent_profile(value:Mapping[str,Any])->AgentProfile:
    if not isinstance(value,Mapping):raise AgentProfileError("Agent Profile doit être un objet.")
    allowed={"id","label","adapter","mode","coverage","events"}
    if set(value)!=allowed:raise AgentProfileError("Agent Profile contient des champs interdits ou manquants.")
    profile_id=value["id"];label=value["label"];adapter=value["adapter"];mode=value["mode"];coverage=value["coverage"];events=value["events"]
    if not all(isinstance(x,str) and x for x in (profile_id,label,adapter,mode,coverage)) or _ID.fullmatch(profile_id) is None:raise AgentProfileError("Identité Agent Profile invalide.")
    if adapter not in _ALLOWED or mode not in {"local","cloud","universal"}:raise AgentProfileError("Adapter ou mode Agent Profile inconnu.")
    maximum,available=_ALLOWED[adapter]
    if coverage not in _RANK or _RANK[coverage]>_RANK[maximum]:raise AgentProfileError("Couverture Agent Profile supérieure aux capacités de l’adapter.")
    if not isinstance(events,list) or any(not isinstance(x,str) for x in events) or len(events)!=len(set(events)) or any(x not in available for x in events):raise AgentProfileError("Événements Agent Profile invalides pour l’adapter.")
    return AgentProfile(PROFILE_FORMAT,profile_id,label,adapter,mode,coverage,tuple(events))
def builtin_agent_profiles()->dict[str,AgentProfile]:
    raw=(
        {"id":"claude-code-local","label":"Claude Code local","adapter":"claude-code-local","mode":"local","coverage":"COMPACTION_AWARE","events":["SessionStart","PreToolUse","PostToolUse","PreCompact","PostCompact","Stop"]},
        {"id":"claude-code-cloud","label":"Claude Code cloud","adapter":"claude-code-cloud","mode":"cloud","coverage":"CLOUD_STAGED_NOT_LIVE","events":["SessionStart","PreToolUse","PostToolUse","PreCompact","PostCompact","Stop"]},
        {"id":"codex","label":"Codex","adapter":"codex","mode":"local","coverage":"PARTIAL_LOCAL_TOOLS","events":["SessionStart","PreToolUse","PostToolUse","PreCompact","PostCompact","Stop"]},
        {"id":"gemini","label":"Gemini CLI","adapter":"gemini","mode":"local","coverage":"TOOL_GUARD_NO_POST_COMPACTION","events":["SessionStart","BeforeTool","AfterTool","PreCompress","SessionEnd"]},
        {"id":"antigravity","label":"Antigravity","adapter":"antigravity","mode":"local","coverage":"TURN_GUARD_HARD","events":["PreInvocation","PreToolUse","PostToolUse","Stop"]},
        {"id":"generic-mcp","label":"MCP générique","adapter":"generic-mcp","mode":"universal","coverage":"MCP_ONLY","events":[]},)
    values=[validate_agent_profile(item) for item in raw];return {item.id:item for item in values}
def builtin_agent_profiles_json()->str:return json.dumps({"format":"vera-agent-profiles/v1","profiles":[item.as_dict() for item in builtin_agent_profiles().values()]},ensure_ascii=False,sort_keys=True,indent=2)+"\n"

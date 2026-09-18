"""Write the project playbook a VERA runtime always has in practice.

`vmmu init-project` always materializes `playbook.md`, so every real project carries one and
the compiled MCP instructions can quote it. Fixtures that hand-write a profile skip that step,
so this helper puts the file back where the runtime expects it.
"""
from __future__ import annotations

from pathlib import Path

from vera_mmu.agent_profiles import builtin_agent_profiles_json
from vera_mmu.identity import load_profile
from vera_mmu.workspace import resolve_workspace


PLAYBOOK_TEXT = """# Règles de travail — projet de test

## Lois VERA

1. Une observation n’est pas une preuve.
2. Les policies, gates, capabilities et chemins sont validés avant exécution.
3. Les erreurs restent fail-closed.
"""


_DECLARATIVE_DEFAULTS = {
    "capabilities.yaml": "format: vera-capability-catalog/v1\ncapabilities: []\n",
    "gates.yaml": "format: vera-gate-catalog/v1\ngates: []\n",
    "policies.yaml": (
        "format: vera-policy-catalog/v1\n"
        "filesystem: {read: allow, write: confirm}\n"
        "network: {default: deny}\n"
        "process: {allowed_runners: []}\n"
        "git: {commit: confirm, push: confirm}\n"
        "destructive: {default: confirm}\n"
        "promotion: {proven_requires: [admissible_pass, technical_validation]}\n"
    ),
}


def write_playbook(profile_path: Path | str, text: str = PLAYBOOK_TEXT) -> Path:
    """Materialize the declarative files a real VERA runtime always carries.

    Writes `playbook.md`, plus any declarative catalog the fixture has not written itself. A
    file already present is never overwritten, so a fixture that wants a specific catalog — or
    deliberately removes one to test a refusal — keeps full control.
    """
    source = Path(profile_path)
    workspace = resolve_workspace(load_profile(source), source)
    runtime = workspace.runtime_dir
    runtime.mkdir(parents=True, exist_ok=True)
    defaults = {**_DECLARATIVE_DEFAULTS, "agent-profiles.yaml": builtin_agent_profiles_json()}
    for name, content in defaults.items():
        candidate = runtime / name
        if not candidate.exists():
            candidate.write_text(content, encoding="utf-8")
    target = runtime / "playbook.md"
    target.write_text(text, encoding="utf-8")
    return target

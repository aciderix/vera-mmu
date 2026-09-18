"""What each MCP tool does to the project, so §34 can count it honestly.

§34 asks the Dashboard to show, before generation, how many tools are read-only, how many write,
how many are sensitive and how many use the network. Nothing classified them: the façade knew its
tool names and nothing else, so any count would have been invented at the screen.

**Why the classification is declared rather than derived from one marker.** `_mutating_call` looks
like the answer and is not: it means "report the memory-sync status afterwards", not "changes
something". `mmu_export_bundle` writes an archive and `mmu_sync_memory` commits to Git, and neither
goes through it. Deriving from that marker would have called both read-only — a count that reads
reassuringly and is false. What *is* derivable is the one-way relation, and a test pins it: every
tool that goes through `_mutating_call` must be declared `WRITE`.

**Sensitive has a definition, not a feeling.** A tool is sensitive when it writes **outside** the
project's VERA runtime, replaces canonical memory wholesale, or signs a `PROVEN` promotion. Three
tools meet it. Anything else would be a label applied by taste, and a count nobody can check.

**Network is empty, and that is a fact about the engine.** The Core holds no network path and
`capability_contract` constrains its network policy to `DENY_NETWORK` in SQL. The count is zero
because zero is true, not because the list was forgotten.
"""
from __future__ import annotations

from .mcp_manifest import TOOL_NAMES


READ_ONLY = "READ_ONLY"
WRITE = "WRITE"

# Every tool of the closed façade, by what it does to durable state.
TOOL_ACCESS: dict[str, str] = {
    # --- read-only: a projection, and nothing changes -----------------------
    "mmu_get_capability_catalog": READ_ONLY,
    "mmu_get_execution": READ_ONLY,
    "mmu_read_artifact": READ_ONLY,
    "mmu_evaluate_gate": READ_ONLY,
    "mmu_preview_project_documents": READ_ONLY,
    "mmu_doctor": READ_ONLY,
    "mmu_get_coverage_report": READ_ONLY,
    "mmu_get_documentation": READ_ONLY,
    "mmu_get_vcs_status": READ_ONLY,
    "mmu_boot": READ_ONLY,
    "mmu_get_front": READ_ONLY,
    "mmu_get_handoff": READ_ONLY,
    "mmu_find": READ_ONLY,
    "mmu_get_related": READ_ONLY,
    "mmu_list_executions": READ_ONLY,
    "mmu_list_evidence": READ_ONLY,
    "mmu_read": READ_ONLY,
    "mmu_read_batch": READ_ONLY,
    "mmu_get_resume_brief": READ_ONLY,
    "mmu_get_resume_status": READ_ONLY,
    "mmu_export": READ_ONLY,
    "mmu_import_bundle": READ_ONLY,
    "mmu_compile": READ_ONLY,
    "mmu_get_work_graph": READ_ONLY,
    "mmu_get_proofs": READ_ONLY,
    # --- write: durable state changes ---------------------------------------
    "mmu_run_capability": WRITE,
    "mmu_validate_evidence": WRITE,
    "mmu_decide_admission": WRITE,
    "mmu_acknowledge_resume": WRITE,
    "mmu_sync_capabilities": WRITE,
    "mmu_sync_knowledge_types": WRITE,
    "mmu_append_knowledge": WRITE,
    "mmu_replace_front": WRITE,
    "mmu_update_front": WRITE,
    "mmu_prepare_handoff": WRITE,
    "mmu_create_work_item": WRITE,
    "mmu_update_work_item": WRITE,
    "mmu_add_work_dependency": WRITE,
    "mmu_create_gate": WRITE,
    "mmu_declare_proof_policy": WRITE,
    "mmu_attach_proof": WRITE,
    "mmu_import_project_documents": WRITE,
    "mmu_repair": WRITE,
    # These two write without going through `_mutating_call`, which is exactly why the
    # classification is declared here rather than read off that marker.
    "mmu_export_bundle": WRITE,
    "mmu_sync_memory": WRITE,
    "mmu_restore": WRITE,
    "mmu_record_proof": WRITE,
}

# Writes outside the VERA runtime, replaces canonical memory, or signs a `PROVEN` promotion.
SENSITIVE_TOOLS = frozenset({"mmu_sync_memory", "mmu_restore", "mmu_record_proof"})
SENSITIVE_REASONS = {
    "mmu_sync_memory": "Écrit dans l’historique Git du projet, hors du runtime VERA.",
    "mmu_restore": "Remplace la mémoire canonique par celle d’un bundle vérifié.",
    "mmu_record_proof": "Signe une promotion `PROVEN` : la seule écriture qui crée un fait prouvé.",
}
# Empty because the Core holds no network path, not because nothing was listed.
NETWORK_TOOLS: frozenset[str] = frozenset()
NETWORK_REASON = (
    "Aucun outil réseau : le Core ne tient aucun chemin réseau et `capability_contract` contraint "
    "sa policy réseau à `DENY_NETWORK` en SQL."
)
# A project never adds a tool: it declares capabilities the closed façade runs.
PROJECT_TOOL_REASON = (
    "La façade MCP est fermée : un projet n’ajoute aucun outil, il déclare des capabilities que "
    "`mmu_run_capability` exécute."
)


class ToolClassError(ValueError):
    """Raised when a tool carries no class, which must never be silently allowed."""


def classify_tool(name: str) -> str:
    """Return what a tool does to durable state, or refuse rather than guess."""
    if not isinstance(name, str) or name not in TOOL_ACCESS:
        raise ToolClassError(f"Outil MCP non classé : {name!r}.")
    return TOOL_ACCESS[name]


def unclassified_tools() -> tuple[str, ...]:
    """Tools the manifest advertises that this module does not classify. Must stay empty."""
    return tuple(sorted(set(TOOL_NAMES) - set(TOOL_ACCESS)))


def undeclared_tools() -> tuple[str, ...]:
    """Tools classified here that the manifest does not advertise. Must stay empty."""
    return tuple(sorted(set(TOOL_ACCESS) - set(TOOL_NAMES)))


def tool_counts() -> dict[str, int]:
    """The tool figures §34 displays, counted from the closed façade itself."""
    return {
        "core_tools": len(TOOL_NAMES),
        "project_tools": 0,
        "read_only": sum(1 for name in TOOL_NAMES if TOOL_ACCESS[name] == READ_ONLY),
        "write": sum(1 for name in TOOL_NAMES if TOOL_ACCESS[name] == WRITE),
        "sensitive": len(SENSITIVE_TOOLS),
        "network": len(NETWORK_TOOLS),
    }

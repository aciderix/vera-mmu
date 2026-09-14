"""The ordered MCP compiler pipeline and the package it produces.

The specification fixes the stages a build runs through and requires a blocking static
validation before anything is handed back. Generation already produced the right artifacts, but
implicitly: nothing named the stages, nothing checked the outputs against one another, and no
single object gathered what a clean machine would need.

This module runs the stages in their declared order, records each one, refuses at the first
inconsistency, and only then produces the package. Every declarative input — profile, catalogs,
playbook, packs, adapter binding — reaches the package hash, so two identical inputs produce an
identical build and a changed rule changes the hash.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Mapping

from .documentation_generator import compile_project_documentation
from .identity import canonical_json
from .mcp_hooks import MCPHookPlan, compile_mcp_hook_plan
from .mcp_instructions import MCPInstructions, MCPInstructionsError, compile_mcp_instructions
from .mcp_integration import MCPIntegration, compile_mcp_integration
from .mcp_manifest import MCPManifest, MCPManifestError, compile_mcp_manifest
from .playbook import PlaybookError, ProjectPlaybook, compile_project_playbook
from .project_catalogs import ProjectCatalogError, ProjectCatalogs, load_project_catalogs
from .store import MemoryStore, StoreError


PACKAGE_FORMAT = "vera-mcp-package/v1"
TOOL_SCHEMA_FORMAT = "vera-mcp-tool-schemas/v1"
# The stages the specification fixes, in the order it fixes them. The pipeline runs exactly
# this sequence; a stage that cannot complete stops the build rather than degrading it.
COMPILER_STAGES = (
    "load",
    "normalize",
    "validate",
    "canonicalize",
    "compute_profile_hash",
    "resolve_capabilities",
    "resolve_gates",
    "resolve_policies",
    "resolve_integrations",
    "generate_tool_schemas",
    "generate_instructions",
    "generate_hooks",
    "generate_config",
    "generate_documentation",
    "run_static_validation",
    "produce_package",
)
_ADAPTER_BINDINGS = {
    "claude-code-local": "claude-code-local-deny-v1",
    "claude-code-cloud": "claude-code-cloud-deny-v1",
    "codex": "codex-deny-v1",
    "gemini": "gemini-deny-v1",
    "antigravity": "antigravity-deny-v1",
    "generic-mcp": "generic-mcp-deny-v1",
}
# Inputs a client must never be able to place in a generated package.
_FORBIDDEN_PACKAGE_KEYS = ("command", "argv", "shell", "interpreter", "cwd", "executable")


class MCPCompilerError(StoreError):
    """Raised when the MCP build cannot be completed exactly as specified."""


@dataclass(frozen=True)
class CompilerStage:
    """One completed pipeline stage and what it established."""

    name: str
    status: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {"name": self.name, "status": self.status, "detail": self.detail}


@dataclass(frozen=True)
class MCPPackage:
    """One reproducible MCP build: its inputs, its outputs and the stages that produced them."""

    format: str
    project_id: str
    adapter: str
    profile_hash: str
    manifest: MCPManifest
    instructions: MCPInstructions
    integration: MCPIntegration
    hook_plan: MCPHookPlan
    playbook: ProjectPlaybook
    catalogs: ProjectCatalogs
    outputs: dict[str, str]
    stages: tuple[CompilerStage, ...]
    package_hash: str
    input_hashes: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return {
            "format": self.format,
            "project_id": self.project_id,
            "adapter": self.adapter,
            "profile_hash": self.profile_hash,
            "mcp_build_hash": self.manifest.mcp_build_hash,
            "package_hash": self.package_hash,
            "input_hashes": dict(self.input_hashes),
            "stages": [stage.as_dict() for stage in self.stages],
            "outputs": dict(self.outputs),
        }


def _tool_schemas(manifest: MCPManifest) -> str:
    """Render the closed tool surface the package advertises.

    Only the manifest's own tool names and declared capability contracts appear; nothing here
    can name a command, an interpreter or a path.
    """
    return canonical_json(
        {
            "format": TOOL_SCHEMA_FORMAT,
            "tools": list(manifest.tool_names),
            "capabilities": [
                {
                    "capability_id": item.capability_id,
                    "kind": item.kind,
                    "version": item.version,
                    "parameter_schema": item.parameter_schema,
                    "runner_profile": item.runner_profile,
                    "network_policy": item.network_policy,
                    "timeout_seconds": item.timeout_seconds,
                    "yields_proof": item.yields_proof,
                }
                for item in manifest.capabilities
            ],
        }
    )


def _static_validation(
    manifest: MCPManifest,
    instructions: MCPInstructions,
    integration: MCPIntegration,
    outputs: Mapping[str, str],
    profile_hash: str,
) -> str:
    """Refuse a build whose outputs do not all describe the same project and the same snapshot.

    This is the blocking stage: a mismatch here means an artifact would ship bound to another
    build, which is exactly the silent drift the product exists to prevent (invariant I014).
    """
    if instructions.mcp_build_hash != manifest.mcp_build_hash:
        raise MCPCompilerError("Validation statique : instructions liées à un autre manifeste.")
    if instructions.profile_hash != profile_hash:
        raise MCPCompilerError("Validation statique : instructions liées à un autre Project Profile.")
    if manifest.mcp_build_hash not in outputs["instructions"]:
        raise MCPCompilerError("Validation statique : le manifeste n’est pas cité par les instructions.")
    if instructions.instructions_hash not in integration.json_text and manifest.mcp_build_hash not in integration.json_text:
        raise MCPCompilerError("Validation statique : la configuration hôte ne cite ni instructions ni manifeste.")
    declared = {item.capability_id for item in manifest.capabilities}
    if not declared:
        raise MCPCompilerError("Validation statique : aucune capability déclarée à exposer.")
    for capability_id in declared:
        if capability_id not in outputs["instructions"]:
            raise MCPCompilerError(f"Validation statique : capability `{capability_id}` absente des instructions.")
    rendered = json.dumps(outputs, ensure_ascii=False).lower()
    for forbidden in _FORBIDDEN_PACKAGE_KEYS:
        if f'"{forbidden}"' in rendered:
            raise MCPCompilerError(f"Validation statique : champ `{forbidden}` interdit dans un package MCP.")
    return (
        f"{len(declared)} capability(ies), {len(manifest.tool_names)} outil(s) ; "
        "manifeste, instructions, configuration et hooks liés au même build."
    )


def compile_mcp_package(store: MemoryStore, adapter: str) -> MCPPackage:
    """Run the specified pipeline end to end and produce one reproducible MCP package."""
    if not isinstance(store, MemoryStore):
        raise MCPCompilerError("Store invalide pour la compilation MCP.")
    binding = _ADAPTER_BINDINGS.get(adapter)
    if binding is None:
        raise MCPCompilerError(f"Adapter de compilation inconnu : {adapter}.")
    stages: list[CompilerStage] = []

    def record(name: str, detail: str) -> None:
        stages.append(CompilerStage(name, "PASS", detail))

    # load / normalize / validate — the declarative catalogs and the project playbook.
    try:
        catalogs = load_project_catalogs(store.workspace.profile_path)
    except (ProjectCatalogError, OSError, ValueError) as exc:
        raise MCPCompilerError("Catalogues du Project Profile invalides ou absents.") from exc
    record("load", f"Catalogues chargés depuis {store.workspace.profile_path.name}.")
    try:
        playbook = compile_project_playbook(store)
    except PlaybookError as exc:
        raise MCPCompilerError(f"Playbook projet indisponible : {exc}") from exc
    record("normalize", "Playbook projet borné et normalisé.")
    record("validate", "Catalogues capabilities, gates et policies validés contre leur schéma fermé.")

    # canonicalize / profile hash — what every later hash is derived from.
    input_hashes = {
        "capabilities": catalogs.capability_catalog_hash,
        "gates": catalogs.gate_catalog_hash,
        "policies": catalogs.policy_hash,
        "agent_profiles": catalogs.agent_profiles_hash,
        "playbook": playbook.playbook_hash,
    }
    record("canonicalize", "Entrées déclaratives réduites à leur forme canonique hashée.")
    profile_hash = store.identity.profile_hash
    record("compute_profile_hash", f"Profile hash {profile_hash[:12]}.")

    # resolve — capabilities, then the gates and policies that bound them.
    rows = store.connection.execute(
        "SELECT capability_id FROM capability_policy WHERE decision = 'ALLOW' ORDER BY capability_id"
    ).fetchall()
    bindings = {str(row["capability_id"]): binding for row in rows}
    if not bindings:
        raise MCPCompilerError("Compilation impossible : aucune capability ALLOW déclarée.")
    try:
        manifest = compile_mcp_manifest(store, adapter_bindings=bindings)
    except MCPManifestError as exc:
        raise MCPCompilerError(f"Manifeste MCP non compilable : {exc}") from exc
    record("resolve_capabilities", f"{len(manifest.capabilities)} capability(ies) ALLOW résolue(s).")
    record("resolve_gates", f"Catalogue de gates {catalogs.gate_catalog_hash[:12]} résolu.")
    record("resolve_policies", f"Catalogue de policies {catalogs.policy_hash[:12]} résolu.")
    record("resolve_integrations", f"Adapter `{adapter}` lié au runner déclaré `{binding}`.")

    # generate — schemas, instructions, hooks, host config, documentation.
    tool_schemas = _tool_schemas(manifest)
    record("generate_tool_schemas", f"{len(manifest.tool_names)} outil(s) exposé(s).")
    try:
        instructions = compile_mcp_instructions(store, manifest)
    except MCPInstructionsError as exc:
        raise MCPCompilerError(f"Instructions MCP non compilables : {exc}") from exc
    record("generate_instructions", f"Instructions {instructions.instructions_hash[:12]} en cinq sections.")
    integration = compile_mcp_integration(store, manifest, instructions)
    hooks = compile_mcp_hook_plan(store, manifest, instructions, integration)
    record("generate_hooks", f"Plan de hooks {hooks.hook_plan_hash[:12]}.")
    record("generate_config", f"Configuration hôte {integration.config_hash[:12]}.")
    documentation = compile_project_documentation(store, str(store.workspace.profile_path))
    documentation_text = canonical_json({"bundle_hash": documentation.bundle_hash, "documents": documentation.documents})
    record("generate_documentation", f"Documentation dérivée {documentation.bundle_hash[:12]}.")

    outputs = {
        "manifest": manifest.canonical_json,
        "instructions": instructions.text,
        "integration": integration.json_text,
        "hook_plan": hooks.json_text,
        "documentation": documentation_text,
        "tool_schemas": tool_schemas,
    }
    detail = _static_validation(manifest, instructions, integration, outputs, profile_hash)
    record("run_static_validation", detail)

    joined = "\0".join(
        (
            PACKAGE_FORMAT,
            adapter,
            profile_hash,
            *(input_hashes[key] for key in sorted(input_hashes)),
            *(outputs[key] for key in sorted(outputs)),
        )
    )
    package_hash = sha256(joined.encode("utf-8")).hexdigest()
    record("produce_package", f"Package {package_hash[:12]} produit sans écriture hôte.")
    return MCPPackage(
        format=PACKAGE_FORMAT,
        project_id=store.identity.project_id,
        adapter=adapter,
        profile_hash=profile_hash,
        manifest=manifest,
        instructions=instructions,
        integration=integration,
        hook_plan=hooks,
        playbook=playbook,
        catalogs=catalogs,
        outputs=outputs,
        stages=tuple(stages),
        package_hash=package_hash,
        input_hashes=input_hashes,
    )


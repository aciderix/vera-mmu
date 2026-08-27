"""Compilation déterministe d’un manifeste MCP VERA.

Ce module ne découvre, importe ni n’exécute de runtime. Il rend seulement traçable la
configuration déclarative que la façade MCP peut exposer : identité de projet, migrations,
capabilities autorisées, contrats, policies et identifiants d’adapters côté serveur.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Any, Mapping

from .identity import canonical_json
from .store import MemoryStore, StoreError


MANIFEST_FORMAT = "vera-mcp-manifest/v1"
TOOL_NAMES = (
    "mmu_get_capability_catalog",
    "mmu_run_capability",
    "mmu_get_execution",
    "mmu_read_artifact",
    "mmu_validate_evidence",
    "mmu_decide_admission",
    "mmu_evaluate_gate",
    "mmu_acknowledge_resume",
    "mmu_sync_memory",
    "mmu_export_bundle",
    "mmu_preview_project_documents",
    "mmu_import_project_documents",
    "mmu_doctor",
    "mmu_boot",
    "mmu_get_front",
    "mmu_get_handoff",
    "mmu_find",
    "mmu_get_related",
    "mmu_list_executions",
    "mmu_read",
    "mmu_read_batch",
)
_ADAPTER_ID_RE = re.compile(r"[a-z][a-z0-9-]{0,127}")


class MCPManifestError(StoreError):
    """Le manifeste ne peut pas être compilé ou vérifié de façon sûre."""


@dataclass(frozen=True)
class MCPManifestCapability:
    """Une capability MCP autorisée avec son adapter déclaré côté serveur."""

    capability_id: str
    name: str
    kind: str
    version: str
    parameter_schema: dict[str, object]
    metadata: dict[str, object]
    runner_profile: str
    network_policy: str
    timeout_seconds: int
    yields_proof: bool
    policy_decision: str
    adapter_id: str

    def as_dict(self) -> dict[str, object]:
        return {
            "adapter_id": self.adapter_id,
            "capability_id": self.capability_id,
            "kind": self.kind,
            "metadata": self.metadata,
            "name": self.name,
            "network_policy": self.network_policy,
            "parameter_schema": self.parameter_schema,
            "policy_decision": self.policy_decision,
            "runner_profile": self.runner_profile,
            "timeout_seconds": self.timeout_seconds,
            "version": self.version,
            "yields_proof": self.yields_proof,
        }


@dataclass(frozen=True)
class MCPManifest:
    """Snapshot immutable, project-bound et hashé de la façade MCP à exposer."""

    format: str
    project_identity: dict[str, str]
    migration_checksums: tuple[tuple[int, str], ...]
    tool_names: tuple[str, ...]
    capabilities: tuple[MCPManifestCapability, ...]
    mcp_build_hash: str
    canonical_json: str

    def as_dict(self) -> dict[str, object]:
        return {
            "capabilities": [item.as_dict() for item in self.capabilities],
            "format": self.format,
            "mcp_build_hash": self.mcp_build_hash,
            "migration_checksums": [
                {"sha256": checksum, "version": version}
                for version, checksum in self.migration_checksums
            ],
            "project_identity": dict(self.project_identity),
            "tool_names": list(self.tool_names),
        }


def _json_object(raw: object, field: str) -> dict[str, object]:
    try:
        value = json.loads(str(raw))
    except (TypeError, ValueError) as exc:
        raise MCPManifestError(f"{field} de capability illisible.") from exc
    if not isinstance(value, dict):
        raise MCPManifestError(f"{field} de capability non objet.")
    return value


def _normalize_bindings(adapter_bindings: Mapping[str, str]) -> dict[str, str]:
    if not isinstance(adapter_bindings, Mapping):
        raise MCPManifestError("Les bindings d’adapter doivent être un objet.")
    normalized: dict[str, str] = {}
    for capability_id, adapter_id in adapter_bindings.items():
        if not isinstance(capability_id, str) or not capability_id or "/" in capability_id:
            raise MCPManifestError("Capability de binding invalide.")
        if not isinstance(adapter_id, str) or _ADAPTER_ID_RE.fullmatch(adapter_id) is None:
            raise MCPManifestError("Identifiant d’adapter invalide : aucun chemin ou commande n’est admis.")
        normalized[capability_id] = adapter_id
    return normalized


def _declared_capabilities(store: MemoryStore) -> tuple[dict[str, object], ...]:
    rows = store.connection.execute(
        """
        SELECT capability.id, capability.name, capability.kind, capability.version,
               capability.parameter_schema_json, capability.metadata_json,
               contract.runner_profile, contract.network_policy, contract.timeout_seconds,
               contract.yields_proof, policy.decision AS policy_decision
        FROM capability
        JOIN capability_contract AS contract ON contract.capability_id = capability.id
        JOIN capability_policy AS policy ON policy.capability_id = capability.id
        WHERE policy.decision = 'ALLOW'
        ORDER BY capability.id
        """
    ).fetchall()
    return tuple(
        {
            "capability_id": str(row["id"]),
            "name": str(row["name"]),
            "kind": str(row["kind"]),
            "version": str(row["version"]),
            "parameter_schema": _json_object(row["parameter_schema_json"], "parameter_schema"),
            "metadata": _json_object(row["metadata_json"], "metadata"),
            "runner_profile": str(row["runner_profile"]),
            "network_policy": str(row["network_policy"]),
            "timeout_seconds": int(row["timeout_seconds"]),
            "yields_proof": bool(row["yields_proof"]),
            "policy_decision": str(row["policy_decision"]),
        }
        for row in rows
    )


def compile_mcp_manifest(
    store: MemoryStore,
    *,
    adapter_bindings: Mapping[str, str],
) -> MCPManifest:
    """Compile une configuration MCP complète sans exécuter de capability.

    I007/I008 imposent que toutes les capabilities visibles possèdent exactement un adapter
    symbolique. I011 lie le snapshot à l’identité complète du Store. I012 dérive le hash
    uniquement du contenu canonique, jamais de l’heure, du chemin local ou d’un résultat.
    """
    if not isinstance(store, MemoryStore):
        raise MCPManifestError("Store MCP invalide.")
    bindings = _normalize_bindings(adapter_bindings)
    declarations = _declared_capabilities(store)
    declared_ids = {str(item["capability_id"]) for item in declarations}
    if not declared_ids:
        raise MCPManifestError("Aucune capability ALLOW déclarée à compiler.")
    if set(bindings) != declared_ids:
        missing = sorted(declared_ids - set(bindings))
        extra = sorted(set(bindings) - declared_ids)
        raise MCPManifestError(
            f"Bindings d’adapter incomplets ou hors catalogue : manquants={missing}, extras={extra}."
        )
    capabilities = tuple(
        MCPManifestCapability(
            capability_id=str(item["capability_id"]),
            name=str(item["name"]),
            kind=str(item["kind"]),
            version=str(item["version"]),
            parameter_schema=dict(item["parameter_schema"]),
            metadata=dict(item["metadata"]),
            runner_profile=str(item["runner_profile"]),
            network_policy=str(item["network_policy"]),
            timeout_seconds=int(item["timeout_seconds"]),
            yields_proof=bool(item["yields_proof"]),
            policy_decision=str(item["policy_decision"]),
            adapter_id=bindings[str(item["capability_id"])],
        )
        for item in declarations
    )
    migration_checksums = tuple(sorted(store.migration_checksums.items()))
    payload: dict[str, Any] = {
        "capabilities": [item.as_dict() for item in capabilities],
        "format": MANIFEST_FORMAT,
        "migration_checksums": [
            {"sha256": checksum, "version": version}
            for version, checksum in migration_checksums
        ],
        "project_identity": store.identity.as_dict(),
        "tool_names": list(TOOL_NAMES),
    }
    serialized = canonical_json(payload)
    digest = sha256(serialized.encode("utf-8")).hexdigest()
    return MCPManifest(
        format=MANIFEST_FORMAT,
        project_identity=store.identity.as_dict(),
        migration_checksums=migration_checksums,
        tool_names=TOOL_NAMES,
        capabilities=capabilities,
        mcp_build_hash=digest,
        canonical_json=serialized,
    )


def verify_mcp_manifest(store: MemoryStore, manifest: MCPManifest) -> frozenset[str]:
    """Vérifie un snapshot MCP contre le store courant et retourne son catalogue autorisé.

    Le contrôle recompile la configuration à partir des déclarations persistées : aucun
    manifest étranger, ancien ou modifié ne peut configurer silencieusement une façade.
    """
    if not isinstance(manifest, MCPManifest):
        raise MCPManifestError("Manifeste MCP invalide.")
    bindings = {item.capability_id: item.adapter_id for item in manifest.capabilities}
    current = compile_mcp_manifest(store, adapter_bindings=bindings)
    if current.canonical_json != manifest.canonical_json or current.mcp_build_hash != manifest.mcp_build_hash:
        raise MCPManifestError("Manifeste MCP périmé, altéré ou lié à un autre projet.")
    if current.as_dict() != manifest.as_dict():
        raise MCPManifestError("Manifeste MCP incohérent avec sa forme canonique.")
    return frozenset(bindings)

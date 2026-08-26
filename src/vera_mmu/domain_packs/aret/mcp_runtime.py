"""Assemblage hôte du runtime MCP du Pack ARET.

Ce module appartient au Pack : il est le seul endroit où le registry générique reçoit un
adapter ARET. Le Core MCP reste indépendant d’ARET et conserve son démarrage fail-closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...mcp_adapters import RuntimeAdapterRegistry
from ...mcp_manifest import MCPManifest, compile_mcp_manifest
from ...mcp_server import MCPServer, create_server
from ...store import MemoryStore
from .mcp_adapter import AretClosedOracleMCPAdapter
from .oracle_contract import AretOracleContractError, oracle_spec


@dataclass(frozen=True)
class AretMCPRuntime:
    """Snapshot hôte : adapter, registry, manifeste et façade MCP déjà liés."""

    adapter: AretClosedOracleMCPAdapter
    registry: RuntimeAdapterRegistry
    manifest: MCPManifest
    server: MCPServer


def _aret_adapter_bindings(store: MemoryStore, adapter_id: str) -> dict[str, str]:
    """Retourne les seules capabilities ALLOW que ce Pack peut légitimement exécuter."""
    rows = store.connection.execute(
        """
        SELECT capability.id
        FROM capability
        JOIN capability_policy ON capability_policy.capability_id = capability.id
        WHERE capability_policy.decision = 'ALLOW'
        ORDER BY capability.id
        """
    ).fetchall()
    bindings: dict[str, str] = {}
    for row in rows:
        capability_id = str(row["id"])
        prefix = "aret-oracle-"
        if not capability_id.startswith(prefix):
            continue
        try:
            spec = oracle_spec(capability_id[len(prefix) :])
        except AretOracleContractError:
            continue
        if capability_id == f"{prefix}{spec.name}":
            bindings[capability_id] = adapter_id
    return bindings


def build_aret_mcp_runtime(
    repository: Path,
    store: MemoryStore,
    **adapter_options: Any,
) -> AretMCPRuntime:
    """Construit le runtime ARET seulement si tout le catalogue ALLOW est couvert.

    ``compile_mcp_manifest`` refuse les capabilities autorisées sans binding. Cet hôte ne
    peut donc pas exposer accidentellement une capability générique ou d’un autre Pack.
    """
    if not isinstance(store, MemoryStore):
        raise ValueError("Store VERA requis pour le runtime MCP ARET.")
    adapter = AretClosedOracleMCPAdapter(repository, **adapter_options)
    registry = RuntimeAdapterRegistry((adapter,))
    manifest = compile_mcp_manifest(store, adapter_bindings=_aret_adapter_bindings(store, adapter.adapter_id))
    server = create_server(store, adapter_registry=registry, manifest=manifest, actor="vera-mcp-aret")
    return AretMCPRuntime(adapter=adapter, registry=registry, manifest=manifest, server=server)

"""Façade MCP générique et fail-closed de VERA-MMU.

Le serveur ne connaît ni commande shell, ni oracle, ni Domain Pack. Un adapter déclaré par
le processus hôte est seul autorisé à produire une execution/evidence. Les entrées MCP
ne transportent jamais un verdict, stdout, code de sortie ou artifact.
"""

from __future__ import annotations

import argparse
import base64
from collections.abc import Callable, Mapping
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from mcp.server import MCPServer

from .admission import AdmissionService
from .assets import AssetService
from .evidence import EvidenceService
from .gates import GateService
from .identity import load_profile
from .mcp_adapters import RuntimeAdapterRegistry
from .mcp_instructions import MCPInstructions, compile_mcp_instructions
from .mcp_manifest import MCPManifest, verify_mcp_manifest
from .store import MemoryStore, StoreError
from .validators import ValidatorService


SERVER_NAME = "VERA-MMU"
SERVER_VERSION = "0.1.0"
DEFAULT_ASSET_VALIDATOR_ID = "mcp-asset-binding"
DEFAULT_ADMISSION_REASON = "Admission demandée par la façade MCP VERA."
SERVER_INSTRUCTIONS = """VERA-MMU expose une façade MCP fermée pour des capabilities déclarées.
Les tools transportent les résultats persistés du Core ; ils ne prennent jamais commande,
chemin externe, stdout, exit_code, score, verdict ni artifact à promouvoir. Une capability
est exécutée exclusivement par un adapter déclaré côté serveur. Toute erreur métier reste
structurée et n’est jamais transformée en succès."""


class MCPRuntimeAdapter(Protocol):
    """Contrat de runtime que seul le serveur hôte peut fournir."""

    def run(
        self,
        store: MemoryStore,
        capability_id: str,
        parameters: Mapping[str, object],
        *,
        execution_id: str,
        evidence_id: str,
        actor: str,
    ) -> Mapping[str, object]:
        """Crée l'execution/evidence persistées et retourne leurs références bornées."""


class DenyRuntimeAdapter:
    """Adapter de production par défaut : aucune exécution n’est implicite."""

    def run(
        self,
        store: MemoryStore,
        capability_id: str,
        parameters: Mapping[str, object],
        *,
        execution_id: str,
        evidence_id: str,
        actor: str,
    ) -> Mapping[str, object]:
        del store, capability_id, parameters, execution_id, evidence_id, actor
        raise StoreError("Aucun adapter de runtime n’est configuré pour ce serveur MCP.")


def _identifier(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}"


def _as_json(value: str, field: str) -> dict[str, object]:
    decoded = json.loads(value)
    if not isinstance(decoded, dict):
        raise StoreError(f"{field} persistant illisible.")
    return decoded


def _error(operation: str, exc: Exception) -> dict[str, object]:
    return {
        "ok": False,
        "operation": operation,
        "error": {"code": "VERA_ERROR", "message": str(exc)},
    }


def _call(operation: str, fn: Callable[[], Mapping[str, object]]) -> dict[str, object]:
    """Encapsule les refus métier sans convertir une erreur en succès MCP."""
    try:
        result = fn()
        return {"ok": True, "operation": operation, "result": dict(result)}
    except (StoreError, ValueError, TypeError, KeyError) as exc:
        return _error(operation, exc)
    except Exception:
        # Ne jamais renvoyer une trace ou une donnée inattendue au client.
        return _error(operation, StoreError("Erreur interne de la façade MCP VERA."))


def _catalog(store: MemoryStore, allowed_capability_ids: frozenset[str] | None = None) -> dict[str, object]:
    rows = store.connection.execute(
        """
        SELECT capability.id, capability.name, capability.kind, capability.version,
               capability.description, capability.parameter_schema_json, capability.metadata_json,
               contract.runner_profile, contract.network_policy, contract.timeout_seconds,
               contract.yields_proof, policy.decision AS policy_decision
        FROM capability
        JOIN capability_contract AS contract ON contract.capability_id = capability.id
        JOIN capability_policy AS policy ON policy.capability_id = capability.id
        WHERE policy.decision = 'ALLOW'
        ORDER BY capability.id
        """
    ).fetchall()
    capabilities: list[dict[str, object]] = []
    for row in rows:
        if allowed_capability_ids is not None and str(row["id"]) not in allowed_capability_ids:
            continue
        capabilities.append(
            {
                "id": str(row["id"]),
                "name": str(row["name"]),
                "kind": str(row["kind"]),
                "version": str(row["version"]),
                "description": str(row["description"]),
                "parameter_schema": _as_json(str(row["parameter_schema_json"]), "parameter_schema"),
                "metadata": _as_json(str(row["metadata_json"]), "metadata"),
                "runner_profile": str(row["runner_profile"]),
                "network_policy": str(row["network_policy"]),
                "timeout_seconds": int(row["timeout_seconds"]),
                "yields_proof": bool(row["yields_proof"]),
            }
        )
    return {"capabilities": capabilities}


def _execution(store: MemoryStore, execution_id: str) -> dict[str, object]:
    if not isinstance(execution_id, str) or not execution_id or "/" in execution_id:
        raise StoreError("Identifiant d’execution MCP invalide.")
    row = store.connection.execute(
        """
        SELECT id, capability_id, status, exit_code, parameters_json, environment_json,
               started_at, finished_at, artifact_hash, result_json, created_by
        FROM execution WHERE id = ?
        """,
        (execution_id,),
    ).fetchone()
    if row is None:
        raise StoreError("Execution MCP introuvable.")
    return {
        "execution_id": str(row["id"]),
        "capability_id": str(row["capability_id"]),
        "status": str(row["status"]),
        "exit_code": None if row["exit_code"] is None else int(row["exit_code"]),
        "parameters": _as_json(str(row["parameters_json"]), "parameters"),
        "environment": _as_json(str(row["environment_json"]), "environment"),
        "started_at": str(row["started_at"]),
        "finished_at": str(row["finished_at"]),
        "artifact_hash": None if row["artifact_hash"] is None else str(row["artifact_hash"]),
        "result": _as_json(str(row["result_json"]), "result"),
        "created_by": str(row["created_by"]),
    }


def create_server(
    store: MemoryStore,
    runtime_adapter: MCPRuntimeAdapter | None = None,
    *,
    adapter_registry: RuntimeAdapterRegistry | None = None,
    manifest: MCPManifest | None = None,
    instructions: MCPInstructions | None = None,
    asset_validator_id: str = DEFAULT_ASSET_VALIDATOR_ID,
    actor: str = "vera-mcp",
) -> MCPServer:
    """Crée la façade MCP VERA avec exactement sept tools publics et bornés."""
    if not isinstance(actor, str) or not actor or actor != actor.strip() or "/" in actor:
        raise ValueError("Actor MCP invalide.")
    if not isinstance(asset_validator_id, str) or not asset_validator_id or "/" in asset_validator_id:
        raise ValueError("Validator MCP invalide.")
    if runtime_adapter is not None and adapter_registry is not None:
        raise ValueError("Adapter direct et registry MCP sont mutuellement exclusifs.")
    if adapter_registry is not None and manifest is None:
        raise ValueError("Un registry MCP exige un manifeste vérifié.")
    if instructions is not None:
        if manifest is None:
            raise ValueError("Des instructions MCP compilées exigent un manifeste vérifié.")
        if not isinstance(instructions, MCPInstructions):
            raise ValueError("Instructions MCP compilées invalides.")
        expected_instructions = compile_mcp_instructions(store, manifest)
        if instructions != expected_instructions:
            raise ValueError("Instructions MCP périmées, altérées ou liées à un autre manifeste.")
    adapter = runtime_adapter if runtime_adapter is not None else DenyRuntimeAdapter()
    allowed_capability_ids = None if manifest is None else verify_mcp_manifest(store, manifest)
    adapter_bindings = (
        {} if manifest is None else {item.capability_id: item.adapter_id for item in manifest.capabilities}
    )
    registry_adapters = (
        {} if adapter_registry is None else adapter_registry.resolve_manifest(manifest)
    )
    server = MCPServer(
        SERVER_NAME,
        title="VERA Memory Management Unit",
        description="Façade MCP universelle, fermée et policy-gated de VERA-MMU.",
        instructions=SERVER_INSTRUCTIONS if instructions is None else instructions.text,
        version=SERVER_VERSION,
    )

    @server.tool(name="mmu_get_capability_catalog", structured_output=True)
    async def mmu_get_capability_catalog() -> dict[str, object]:
        """Liste les capabilities ALLOW déclarées avec leurs contrats immuables."""
        return _call("get_capability_catalog", lambda: _catalog(store, allowed_capability_ids))

    @server.tool(name="mmu_run_capability", structured_output=True)
    async def mmu_run_capability(capability_id: str, parameters: dict[str, object]) -> dict[str, object]:
        """Exécute une capability déclarée via l’adapter serveur fermé.

        Aucun score, verdict, stdout, exit_code, commande, chemin ou artifact ne peut être fourni.
        """
        def run() -> Mapping[str, object]:
            if not isinstance(capability_id, str) or not capability_id or "/" in capability_id:
                raise StoreError("Capability MCP invalide.")
            if not isinstance(parameters, dict):
                raise StoreError("Paramètres MCP objet requis.")
            if allowed_capability_ids is not None and capability_id not in allowed_capability_ids:
                raise StoreError("Capability absente du manifeste MCP vérifié.")
            selected_adapter = registry_adapters.get(capability_id, adapter)
            if manifest is not None and getattr(selected_adapter, "adapter_id", None) != adapter_bindings[capability_id]:
                raise StoreError("Adapter de runtime incohérent avec le manifeste MCP vérifié.")
            execution_id = _identifier("mcp-execution")
            evidence_id = _identifier("mcp-evidence")
            result = dict(
                selected_adapter.run(
                    store,
                    capability_id,
                    parameters,
                    execution_id=execution_id,
                    evidence_id=evidence_id,
                    actor=actor,
                )
            )
            expected = {"execution_id", "evidence_id", "asset_id", "verdict", "capability_id", "gate_id"}
            if set(result) != expected:
                raise StoreError("Adapter MCP : résultat hors contrat fermé.")
            if result["execution_id"] != execution_id or result["evidence_id"] != evidence_id:
                raise StoreError("Adapter MCP : références d’execution/evidence incohérentes.")
            if result["capability_id"] != capability_id:
                raise StoreError("Adapter MCP : capability incohérente.")
            evidence = EvidenceService(store).get(evidence_id)
            if result["verdict"] != evidence.verdict:
                raise StoreError("Adapter MCP : verdict non persistant ou incohérent.")
            return result

        return _call("run_capability", run)

    @server.tool(name="mmu_get_execution", structured_output=True)
    async def mmu_get_execution(execution_id: str) -> dict[str, object]:
        """Lit exactement une execution persistée ; aucune inférence de succès n’est faite."""
        return _call("get_execution", lambda: _execution(store, execution_id))

    @server.tool(name="mmu_read_artifact", structured_output=True)
    async def mmu_read_artifact(asset_id: str) -> dict[str, object]:
        """Lit un asset Core exact après vérification locale de son hash et de sa taille."""
        def read() -> Mapping[str, object]:
            metadata = AssetService(store).get(asset_id)
            content = AssetService(store).read(asset_id)
            return {
                "asset_id": metadata.id,
                "content_hash": metadata.content_hash,
                "byte_length": metadata.byte_length,
                "media_type": metadata.media_type,
                "content_base64": base64.b64encode(content).decode("ascii"),
            }

        return _call("read_artifact", read)

    @server.tool(name="mmu_validate_evidence", structured_output=True)
    async def mmu_validate_evidence(evidence_id: str) -> dict[str, object]:
        """Lance uniquement le validator d’asset binding configuré côté serveur."""
        def validate() -> Mapping[str, object]:
            validation = ValidatorService(store).validate(
                _identifier("mcp-validation"), asset_validator_id, evidence_id, actor=actor
            )
            return {"validation_id": validation.id, "evidence_id": validation.evidence_id, "verdict": validation.verdict}

        return _call("validate_evidence", validate)

    @server.tool(name="mmu_decide_admission", structured_output=True)
    async def mmu_decide_admission(evidence_id: str, validation_id: str) -> dict[str, object]:
        """Demande seulement la décision ADMITTED : le Core applique sa policy stricte."""
        def decide() -> Mapping[str, object]:
            admission = AdmissionService(store).decide(
                _identifier("mcp-admission"),
                evidence_id,
                "ADMITTED",
                DEFAULT_ADMISSION_REASON,
                validation_id=validation_id,
                actor=actor,
            )
            return {"admission_id": admission.id, "evidence_id": admission.evidence_id, "decision": admission.decision}

        return _call("decide_admission", decide)

    @server.tool(name="mmu_evaluate_gate", structured_output=True)
    async def mmu_evaluate_gate(gate_id: str) -> dict[str, object]:
        """Évalue une gate depuis les admissions persistées, sans promotion implicite."""
        return _call("evaluate_gate", lambda: asdict(GateService(store).evaluate(gate_id)))

    return server


def main(argv: list[str] | None = None) -> None:
    """Point d’entrée stdio générique : lecture/catalogue et refus d’exécution sans adapter configuré."""
    parser = argparse.ArgumentParser(description="Serveur MCP générique VERA-MMU")
    parser.add_argument("--profile", type=Path, required=True, help="Project Profile VERA à ouvrir")
    parser.add_argument("--streamable-http", action="store_true", help="Expose HTTP au lieu de stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    with MemoryStore.open(load_profile(args.profile), args.profile) as store:
        server = create_server(store)
        if args.streamable_http:
            server.run("streamable-http", host=args.host, port=args.port, streamable_http_path="/mcp")
        else:
            server.run("stdio")


if __name__ == "__main__":
    main()

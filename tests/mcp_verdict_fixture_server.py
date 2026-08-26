"""Serveur stdio réservé au contrat M5 de transport MCP.

Le scénario est fixé par argument de démarrage et ne fait pas partie des arguments MCP.
Il ne s’agit pas d’un serveur de production ni d’un adapter universel de Domain Pack.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from pathlib import Path
import shutil
from typing import Any

from vera_mmu.admission_policies import AdmissionPolicyService
from vera_mmu.assets import AssetService
from vera_mmu.domain_packs.aret.closed_oracle_runner import (
    ARET_TOOLKIT_REFERENCE_COMMIT,
    OracleProcessResult,
    declare_aret_oracle_capability,
    run_closed_oracle,
)
from vera_mmu.evidence import EvidenceService
from vera_mmu.executions import ExecutionService
from vera_mmu.gates import GateService
from vera_mmu.identity import load_profile
from vera_mmu.mcp_manifest import compile_mcp_manifest
from vera_mmu.mcp_server import DEFAULT_ASSET_VALIDATOR_ID, MCPRuntimeAdapter, create_server
from vera_mmu.store import MemoryStore, StoreError
from vera_mmu.validators import ValidatorService
from vera_mmu.work_items import WorkItemService


_SCENARIOS: dict[str, tuple[str, OracleProcessResult]] = {
    "pass": ("difftest", OracleProcessResult(0, "differential equivalence: 272/272 functions", "", False)),
    "fail": ("difftest", OracleProcessResult(0, "differential equivalence: 271/272 functions", "", False)),
    "skipped": ("difftest", OracleProcessResult(None, "", "", False)),
    "timeout": ("difftest", OracleProcessResult(None, "", "timeout", True)),
    "unrecognized": ("difftest", OracleProcessResult(0, "unparseable payload", "", False)),
    "unknown": ("winehash", OracleProcessResult(0, "fixture OK " + "a" * 64, "", False)),
    "tampered": ("difftest", OracleProcessResult(0, "differential equivalence: 272/272 functions", "", False)),
}


class VerdictFixtureAdapter(MCPRuntimeAdapter):
    """Adapter de test déclaré au démarrage, sans entrée de résultat sur l’API MCP."""

    adapter_id = "fixture-aret-v1"

    def __init__(self, scenario: str, reference: Path) -> None:
        if scenario not in _SCENARIOS:
            raise ValueError("Scénario MCP de fixture inconnu.")
        self.scenario = scenario
        self.reference = reference

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
        oracle_name, process = _SCENARIOS[self.scenario]
        expected_capability = f"aret-oracle-{oracle_name}"
        if capability_id != expected_capability:
            raise StoreError("Capability absente du scénario MCP déclaré.")
        if dict(parameters) != {}:
            raise StoreError("Le scénario MCP n’accepte aucun paramètre.")
        if self.scenario == "tampered":
            return self._record_tampered_pass(store, capability_id, execution_id, evidence_id, actor)
        outcome = run_closed_oracle(
            store,
            self.reference,
            oracle_name,
            execution_id=execution_id,
            evidence_id=evidence_id,
            actor=actor,
            command_runner=lambda *_: process,
            revision_reader=lambda _: ARET_TOOLKIT_REFERENCE_COMMIT,
            clean_checker=lambda _: True,
            tool_lookup=(lambda name: None if self.scenario == "skipped" and name == "gcc" else "/bin/true"),
        )
        return self._with_gate(store, capability_id, outcome.execution.id, outcome.evidence.id, outcome.asset_id, outcome.verdict, actor)

    @staticmethod
    def _record_tampered_pass(
        store: MemoryStore,
        capability_id: str,
        execution_id: str,
        evidence_id: str,
        actor: str,
    ) -> Mapping[str, object]:
        asset = AssetService(store).record(
            f"{execution_id}-artifact", b"mcp fixture artifact", media_type="application/json", actor=actor
        )
        ExecutionService(store).record_observed_process(
            execution_id,
            capability_id,
            {},
            environment={"adapter": "mcp-verdict-fixture/v1", "scenario": "tampered"},
            exit_code=0,
            artifact_hash=asset.content_hash,
            result={"verdict": "PASS", "asset_id": asset.id},
            actor=actor,
        )
        EvidenceService(store).record(
            evidence_id,
            execution_id,
            "TEST_PROOF",
            "PASS",
            {"asset_id": asset.id, "asset_hash": "0" * 64},
            actor=actor,
        )
        return VerdictFixtureAdapter._with_gate(store, capability_id, execution_id, evidence_id, asset.id, "PASS", actor)

    @staticmethod
    def _with_gate(
        store: MemoryStore,
        capability_id: str,
        execution_id: str,
        evidence_id: str,
        asset_id: str,
        verdict: str,
        actor: str,
    ) -> Mapping[str, object]:
        gate_id = f"gate-{execution_id}"
        WorkItemService(store).create(gate_id, "SUBTASK", "MCP verdict gate", actor=actor)
        GateService(store).declare(gate_id, gate_id, evidence_id, actor=actor)
        return {
            "execution_id": execution_id,
            "evidence_id": evidence_id,
            "asset_id": asset_id,
            "verdict": verdict,
            "capability_id": capability_id,
            "gate_id": gate_id,
        }


def _prepare_reference(root: Path) -> Path:
    binary = root / "target" / "release" / "aret"
    binary.parent.mkdir(parents=True, exist_ok=True)
    binary.write_bytes(b"mcp test-only aret binary")
    for relative_path in ("bench/difftest.sh", "bench/winoracle/wine_hashes.sh"):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    return root


def _initialize_store(store: MemoryStore) -> None:
    declare_aret_oracle_capability(store, "difftest", actor="mcp-fixture")
    declare_aret_oracle_capability(store, "winehash", actor="mcp-fixture")
    ValidatorService(store).register(DEFAULT_ASSET_VALIDATOR_ID, "EVIDENCE_ASSET", actor="mcp-fixture")
    AdmissionPolicyService(store).declare("VALIDATED_PASS_EVIDENCE", actor="mcp-fixture")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fixture MCP VERA verdict transport")
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--scenario", choices=sorted(_SCENARIOS), required=True)
    args = parser.parse_args()
    with MemoryStore.open(load_profile(args.profile), args.profile) as store:
        _initialize_store(store)
        reference = _prepare_reference(args.profile.parent / "aret-reference")
        adapter = VerdictFixtureAdapter(args.scenario, reference)
        manifest = compile_mcp_manifest(
            store,
            adapter_bindings={
                "aret-oracle-difftest": adapter.adapter_id,
                "aret-oracle-winehash": adapter.adapter_id,
            },
        )
        server = create_server(store, adapter, manifest=manifest, actor="mcp-fixture")
        server.run("stdio")


if __name__ == "__main__":
    main()

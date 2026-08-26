"""Adapter MCP de production du Pack ARET.

Le Core ne connaît pas cet adapter. L’hôte de confiance peut l’instancier avec une référence
toolkit attestée puis l’inscrire dans ``RuntimeAdapterRegistry``. Toute exécution reste
déléguée à ``run_closed_oracle`` et à son catalogue/sandbox fermés.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
import shutil
from typing import Any

from ...gates import GateService
from ...store import MemoryStore, StoreError
from ...work_items import WorkItemService
from .closed_oracle_runner import (
    AretClosedOracleError,
    ClosedOracleOutcome,
    OracleProcessResult,
    _repository_is_clean,
    _repository_revision,
    _run_subprocess,
    run_closed_oracle,
)
from .oracle_contract import AretOracleContractError, oracle_spec


class AretClosedOracleMCPAdapter:
    """Expose les neuf oracles fermés du Pack comme un adapter runtime unique."""

    adapter_id = "aret-closed-oracle-v1"

    def __init__(
        self,
        repository: Path,
        *,
        aret_binary: Path | None = None,
        command_runner: Callable[[tuple[str, ...], Path, dict[str, str], int], OracleProcessResult] = _run_subprocess,
        revision_reader: Callable[[Path], str] = _repository_revision,
        clean_checker: Callable[[Path], bool] = _repository_is_clean,
        tool_lookup: Callable[[str], str | None] = shutil.which,
    ) -> None:
        if not isinstance(repository, Path) or not callable(command_runner):
            raise ValueError("Configuration de l’adapter ARET invalide.")
        if aret_binary is not None and not isinstance(aret_binary, Path):
            raise ValueError("Binaire ARET configuré invalide.")
        if not callable(revision_reader) or not callable(clean_checker) or not callable(tool_lookup):
            raise ValueError("Dépendance de runtime ARET invalide.")
        self._repository = repository
        self._aret_binary = aret_binary
        self._command_runner = command_runner
        self._revision_reader = revision_reader
        self._clean_checker = clean_checker
        self._tool_lookup = tool_lookup

    @staticmethod
    def _oracle_for(capability_id: str, parameters: Mapping[str, object]) -> tuple[str, str | None]:
        if not isinstance(capability_id, str) or not isinstance(parameters, Mapping):
            raise StoreError("Entrée adapter ARET invalide.")
        prefix = "aret-oracle-"
        if not capability_id.startswith(prefix):
            raise StoreError("Capability absente du Pack ARET fermé.")
        oracle_name = capability_id[len(prefix) :]
        try:
            spec = oracle_spec(oracle_name)
        except AretOracleContractError as exc:
            raise StoreError("Oracle ARET absent du catalogue fermé.") from exc
        if capability_id != f"{prefix}{spec.name}":
            raise StoreError("Capability ARET non canonique.")
        normalized = dict(parameters)
        allowed = {"fixture"} if spec.accepts_fixture else set()
        if set(normalized) - allowed:
            raise StoreError("Paramètre non déclaré pour l’oracle ARET fermé.")
        fixture = normalized.get("fixture")
        if fixture is not None and not isinstance(fixture, str):
            raise StoreError("Fixture ARET invalide.")
        return spec.name, fixture

    @staticmethod
    def _with_gate(
        store: MemoryStore,
        capability_id: str,
        outcome: ClosedOracleOutcome,
        *,
        actor: str,
    ) -> Mapping[str, object]:
        gate_id = f"gate-{outcome.execution.id}"
        try:
            WorkItemService(store).create(gate_id, "SUBTASK", "ARET MCP oracle gate", actor=actor)
            GateService(store).declare(gate_id, gate_id, outcome.evidence.id, actor=actor)
        except (ValueError, StoreError) as exc:
            raise StoreError("Déclaration de gate ARET MCP impossible.") from exc
        return {
            "execution_id": outcome.execution.id,
            "evidence_id": outcome.evidence.id,
            "asset_id": outcome.asset_id,
            "verdict": outcome.verdict,
            "capability_id": capability_id,
            "gate_id": gate_id,
        }

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
        """Délègue au runner Pack fermé et retourne les seules références acceptées par MCP."""
        oracle_name, fixture = self._oracle_for(capability_id, parameters)
        try:
            outcome = run_closed_oracle(
                store,
                self._repository,
                oracle_name,
                execution_id=execution_id,
                evidence_id=evidence_id,
                actor=actor,
                fixture=fixture,
                aret_binary=self._aret_binary,
                command_runner=self._command_runner,
                revision_reader=self._revision_reader,
                clean_checker=self._clean_checker,
                tool_lookup=self._tool_lookup,
            )
        except AretClosedOracleError as exc:
            raise StoreError("Exécution ARET fermée refusée.") from exc
        return self._with_gate(store, capability_id, outcome, actor=actor)

"""Serveur stdio de fixture M5-K : contexte lifecycle fixé côté hôte de test."""

from __future__ import annotations

import argparse
from pathlib import Path

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.identity import load_profile
from vera_mmu.lifecycle_adapters import LifecycleAdapterRegistry, compile_lifecycle_adapter_plan
from vera_mmu.mcp_manifest import compile_mcp_manifest
from vera_mmu.mcp_server import create_server
from vera_mmu.session_lifecycle import ResumeDossierService, ResumeGuardService, ResumeSectionRequirement
from vera_mmu.store import MemoryStore


class FixtureLifecycleAdapter:
    """Contexte hôte fixé au démarrage ; aucun identifiant ne provient du client MCP."""

    adapter_id = "fixture-lifecycle-v1"
    adapter_version = "1.0.0"
    maximum_guard_mode = "HARD"

    def __init__(self, session_identity: str | None) -> None:
        self._session_identity = session_identity

    def session_identity(self) -> str | None:
        return self._session_identity


def _initialize(store: MemoryStore) -> None:
    CapabilityService(store).create(
        "fixture-check",
        "Fixture check",
        "CHECK",
        "1.0.0",
        parameter_schema={"type": "object", "additionalProperties": False},
        metadata={},
        actor="mcp-lifecycle-fixture",
    )
    CapabilityContractService(store).declare(
        "fixture-check",
        "OBSERVED_PROCESS",
        "DENY_NETWORK",
        30,
        parameter_schema={"type": "object", "additionalProperties": False},
        actor="mcp-lifecycle-fixture",
    )
    CapabilityPolicyService(store).declare("fixture-check", "ALLOW", "fixture", actor="mcp-lifecycle-fixture")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fixture MCP VERA lifecycle")
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--context", choices=("ready", "missing"), required=True)
    args = parser.parse_args()
    with MemoryStore.open(load_profile(args.profile), args.profile) as store:
        _initialize(store)
        manifest = compile_mcp_manifest(store, adapter_bindings={"fixture-check": "fixture-runner-v1"})
        adapter = FixtureLifecycleAdapter("fixture-session" if args.context == "ready" else None)
        plan = compile_lifecycle_adapter_plan(
            store,
            manifest,
            adapter_id=adapter.adapter_id,
            adapter_version=adapter.adapter_version,
            maximum_guard_mode=adapter.maximum_guard_mode,
        )
        dossier = ResumeDossierService(store).compile(
            (
                ResumeSectionRequirement("working-rules", 12, 256),
                ResumeSectionRequirement("current-state", 12, 256),
            ),
            {
                "working-rules": "Mesurer les faits avant toute conclusion.",
                "current-state": "La garde de reprise attend un acquittement.",
            },
        )
        if args.context == "ready":
            ResumeGuardService(store).arm(
                "fixture-session", adapter.adapter_id, "SESSION_OPEN", dossier, mode="HARD"
            )
        server = create_server(
            store,
            manifest=manifest,
            lifecycle_adapter_registry=LifecycleAdapterRegistry((adapter,)),
            lifecycle_adapter_plan=plan,
            actor="mcp-lifecycle-fixture",
        )
        server.run("stdio")


if __name__ == "__main__":
    main()

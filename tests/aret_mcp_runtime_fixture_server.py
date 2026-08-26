"""Hôte stdio réservé aux tests du runtime MCP de production du Pack ARET."""

from __future__ import annotations

import argparse
from pathlib import Path

from vera_mmu.admission_policies import AdmissionPolicyService
from vera_mmu.domain_packs.aret.closed_oracle_runner import (
    ARET_TOOLKIT_REFERENCE_COMMIT,
    OracleProcessResult,
    declare_aret_oracle_capability,
)
from vera_mmu.domain_packs.aret.mcp_runtime import build_aret_mcp_runtime
from vera_mmu.identity import load_profile
from vera_mmu.mcp_server import DEFAULT_ASSET_VALIDATOR_ID
from vera_mmu.store import MemoryStore
from vera_mmu.validators import ValidatorService


def _reference(root: Path) -> Path:
    binary = root / "target" / "release" / "aret"
    binary.parent.mkdir(parents=True, exist_ok=True)
    binary.write_text("aret-mcp-runtime-fixture", encoding="utf-8")
    script = root / "bench" / "difftest.sh"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    return root


def main() -> None:
    parser = argparse.ArgumentParser(description="Fixture MCP runtime ARET")
    parser.add_argument("--profile", type=Path, required=True)
    args = parser.parse_args()
    with MemoryStore.open(load_profile(args.profile), args.profile) as store:
        declare_aret_oracle_capability(store, "difftest", actor="mcp-aret-runtime-fixture")
        ValidatorService(store).register(DEFAULT_ASSET_VALIDATOR_ID, "EVIDENCE_ASSET", actor="mcp-aret-runtime-fixture")
        AdmissionPolicyService(store).declare("VALIDATED_PASS_EVIDENCE", actor="mcp-aret-runtime-fixture")
        runtime = build_aret_mcp_runtime(
            _reference(args.profile.parent / "aret-reference"),
            store,
            command_runner=lambda *_: OracleProcessResult(
                0, "differential equivalence: 2/2 functions", "", False
            ),
            revision_reader=lambda _: ARET_TOOLKIT_REFERENCE_COMMIT,
            clean_checker=lambda _: True,
            tool_lookup=lambda _: "/bin/true",
        )
        runtime.server.run("stdio")


if __name__ == "__main__":
    main()

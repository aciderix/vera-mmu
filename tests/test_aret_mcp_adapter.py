"""M5-D — adapter MCP de production du Pack ARET, jamais du Core."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.domain_packs.aret.closed_oracle_runner import (
    ARET_TOOLKIT_REFERENCE_COMMIT,
    OracleProcessResult,
    declare_aret_oracle_capability,
)
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore, StoreError


PROFILE = """
mmu:
  version: "2.0"
project:
  id: "aret-mcp-adapter"
  name: "ARET MCP Adapter"
  domain: "generic"
workspace:
  root: "."
storage:
  memory_dir: ".vera-mmu"
  sqlite_file: "memory.sqlite"
  artifacts_dir: "artifacts"
identity:
  include_vcs_revision: false
  include_profile_hash: true
"""


class AretMCPAdapterTests(unittest.TestCase):
    def _store(self, directory: Path) -> MemoryStore:
        profile_path = directory / "project.yaml"
        profile_path.write_text(PROFILE, encoding="utf-8")
        return MemoryStore.open(load_profile(profile_path), profile_path)

    @staticmethod
    def _reference(root: Path) -> Path:
        binary = root / "target" / "release" / "aret"
        binary.parent.mkdir(parents=True)
        binary.write_text("aret", encoding="utf-8")
        for script in ("bench/difftest.sh", "bench/winediff.sh", "bench/winoracle/wine_hashes.sh"):
            path = root / script
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        return root

    def test_i007_delegates_only_declared_oracle_to_closed_runner_and_creates_gate(self) -> None:
        from vera_mmu.domain_packs.aret.mcp_adapter import AretClosedOracleMCPAdapter

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                declared = declare_aret_oracle_capability(store, "difftest", actor="test")
                adapter = AretClosedOracleMCPAdapter(
                    self._reference(Path(directory) / "reference"),
                    command_runner=lambda *_: OracleProcessResult(
                        0, "differential equivalence: 2/2 functions", "", False
                    ),
                    revision_reader=lambda _: ARET_TOOLKIT_REFERENCE_COMMIT,
                    clean_checker=lambda _: True,
                    tool_lookup=lambda _: "/bin/true",
                )
                result = adapter.run(
                    store,
                    declared.capability.id,
                    {},
                    execution_id="mcp-production-execution",
                    evidence_id="mcp-production-evidence",
                    actor="test",
                )
                self.assertEqual(adapter.adapter_id, "aret-closed-oracle-v1")
                self.assertEqual(result["capability_id"], declared.capability.id)
                self.assertEqual(result["verdict"], "PASS")
                self.assertEqual(result["execution_id"], "mcp-production-execution")
                self.assertEqual(result["evidence_id"], "mcp-production-evidence")
                self.assertEqual(result["gate_id"], "gate-mcp-production-execution")
                self.assertEqual(
                    store.connection.execute("SELECT COUNT(*) FROM execution").fetchone()[0], 1
                )

    def test_i014_refuses_non_aret_capability_or_unbounded_parameters(self) -> None:
        from vera_mmu.domain_packs.aret.mcp_adapter import AretClosedOracleMCPAdapter

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                declare_aret_oracle_capability(store, "difftest", actor="test")
                adapter = AretClosedOracleMCPAdapter(
                    self._reference(Path(directory) / "reference"),
                    command_runner=lambda *_: OracleProcessResult(0, "differential equivalence: 1/1 functions", "", False),
                    revision_reader=lambda _: ARET_TOOLKIT_REFERENCE_COMMIT,
                    clean_checker=lambda _: True,
                    tool_lookup=lambda _: "/bin/true",
                )
                with self.assertRaises(StoreError):
                    adapter.run(
                        store,
                        "other-capability",
                        {},
                        execution_id="reject-execution-1",
                        evidence_id="reject-evidence-1",
                        actor="test",
                    )
                with self.assertRaises(StoreError):
                    adapter.run(
                        store,
                        "aret-oracle-difftest",
                        {"verdict": "PASS"},
                        execution_id="reject-execution-2",
                        evidence_id="reject-evidence-2",
                        actor="test",
                    )
                self.assertEqual(
                    store.connection.execute("SELECT COUNT(*) FROM execution").fetchone()[0], 0
                )


if __name__ == "__main__":
    unittest.main()

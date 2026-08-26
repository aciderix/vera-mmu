"""M5-D — hôte MCP du Pack ARET, fermé par manifeste et registry."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.domain_packs.aret.closed_oracle_runner import declare_aret_oracle_capability
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore, StoreError


PROFILE = """
mmu:
  version: "2.0"
project:
  id: "aret-mcp-runtime"
  name: "ARET MCP Runtime"
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


class AretMCPRuntimeTests(unittest.TestCase):
    def _store(self, directory: Path) -> MemoryStore:
        profile_path = directory / "project.yaml"
        profile_path.write_text(PROFILE, encoding="utf-8")
        return MemoryStore.open(load_profile(profile_path), profile_path)

    @staticmethod
    def _reference(root: Path) -> Path:
        binary = root / "target" / "release" / "aret"
        binary.parent.mkdir(parents=True)
        binary.write_text("aret", encoding="utf-8")
        path = root / "bench" / "difftest.sh"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        return root

    @staticmethod
    def _other_capability(store: MemoryStore) -> None:
        CapabilityService(store).create(
            "other-capability",
            "Other",
            "CHECK",
            "1.0.0",
            parameter_schema={"type": "object", "additionalProperties": False},
            metadata={},
            actor="test",
        )
        CapabilityContractService(store).declare(
            "other-capability",
            "OBSERVED_PROCESS",
            "DENY_NETWORK",
            30,
            parameter_schema={"type": "object", "additionalProperties": False},
            actor="test",
        )
        CapabilityPolicyService(store).declare("other-capability", "ALLOW", "test", actor="test")

    def test_i007_builds_server_with_only_the_declared_aret_adapter(self) -> None:
        from vera_mmu.domain_packs.aret.mcp_runtime import build_aret_mcp_runtime

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                declare_aret_oracle_capability(store, "difftest", actor="test")
                runtime = build_aret_mcp_runtime(self._reference(Path(directory) / "reference"), store)
                self.assertEqual(runtime.adapter.adapter_id, "aret-closed-oracle-v1")
                self.assertEqual(runtime.registry.adapter_ids, ("aret-closed-oracle-v1",))
                self.assertEqual(
                    tuple(item.capability_id for item in runtime.manifest.capabilities),
                    ("aret-oracle-difftest",),
                )

    def test_i014_refuses_any_allowed_capability_without_a_registered_pack_adapter(self) -> None:
        from vera_mmu.domain_packs.aret.mcp_runtime import build_aret_mcp_runtime

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                declare_aret_oracle_capability(store, "difftest", actor="test")
                self._other_capability(store)
                with self.assertRaises(StoreError):
                    build_aret_mcp_runtime(self._reference(Path(directory) / "reference"), store)


if __name__ == "__main__":
    unittest.main()

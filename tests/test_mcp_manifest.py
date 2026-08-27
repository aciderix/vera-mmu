"""M5-B — I007/I008/I011/I012/I014 : manifeste MCP fermé et déterministe."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore


PROFILE = """
mmu:
  version: "2.0"
project:
  id: "mcp-manifest"
  name: "MCP Manifest"
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


class MCPManifestTests(unittest.TestCase):
    """Un manifest ne dépend que d’entrées déclarées et n’embarque aucune commande."""

    def _store(self, directory: Path) -> MemoryStore:
        profile_path = directory / "project.yaml"
        profile_path.write_text(PROFILE, encoding="utf-8")
        return MemoryStore.open(load_profile(profile_path), profile_path)

    @staticmethod
    def _declare(store: MemoryStore, identifier: str, version: str = "1.0.0") -> None:
        CapabilityService(store).create(
            identifier,
            f"Capability {identifier}",
            "CHECK",
            version,
            parameter_schema={"type": "object", "additionalProperties": False},
            metadata={"fixture": identifier},
            actor="test",
        )
        CapabilityContractService(store).declare(
            identifier,
            "OBSERVED_PROCESS",
            "DENY_NETWORK",
            30,
            parameter_schema={"type": "object", "additionalProperties": False},
            actor="test",
        )
        CapabilityPolicyService(store).declare(identifier, "ALLOW", "test policy", actor="test")

    def test_i012_compilation_is_canonical_and_project_bound(self) -> None:
        from vera_mmu.mcp_manifest import compile_mcp_manifest

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                self._declare(store, "zeta")
                self._declare(store, "alpha")
                bindings = {"zeta": "runner-zeta-v1", "alpha": "runner-alpha-v1"}
                first = compile_mcp_manifest(store, adapter_bindings=bindings)
                second = compile_mcp_manifest(store, adapter_bindings={"alpha": "runner-alpha-v1", "zeta": "runner-zeta-v1"})
                self.assertEqual(first.as_dict(), second.as_dict())
                self.assertEqual(first.mcp_build_hash, second.mcp_build_hash)
                self.assertEqual([item.capability_id for item in first.capabilities], ["alpha", "zeta"])
                self.assertEqual(first.project_identity, store.identity.as_dict())
                self.assertEqual(first.format, "vera-mcp-manifest/v1")
                self.assertEqual(first.tool_names, (
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
                    "mmu_read",
                    "mmu_read_batch",
                ))

    def test_i012_changes_to_declared_capability_change_build_hash(self) -> None:
        from vera_mmu.mcp_manifest import compile_mcp_manifest

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                self._declare(store, "alpha")
                before = compile_mcp_manifest(store, adapter_bindings={"alpha": "runner-alpha-v1"})
                self._declare(store, "beta", "2.0.0")
                after = compile_mcp_manifest(
                    store,
                    adapter_bindings={"alpha": "runner-alpha-v1", "beta": "runner-beta-v2"},
                )
                self.assertNotEqual(before.mcp_build_hash, after.mcp_build_hash)
                self.assertNotEqual(before.as_dict(), after.as_dict())

    def test_i007_i008_reject_incomplete_extra_or_command_like_adapter_bindings(self) -> None:
        from vera_mmu.mcp_manifest import MCPManifestError, compile_mcp_manifest

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                self._declare(store, "alpha")
                self._declare(store, "beta")
                with self.assertRaises(MCPManifestError):
                    compile_mcp_manifest(store, adapter_bindings={"alpha": "runner-alpha-v1"})
                with self.assertRaises(MCPManifestError):
                    compile_mcp_manifest(
                        store,
                        adapter_bindings={
                            "alpha": "runner-alpha-v1",
                            "beta": "runner-beta-v1",
                            "unknown": "runner-unknown-v1",
                        },
                    )
                with self.assertRaises(MCPManifestError):
                    compile_mcp_manifest(
                        store,
                        adapter_bindings={"alpha": "bash -c whoami", "beta": "runner-beta-v1"},
                    )

    def test_i011_i012_verification_refuses_foreign_or_stale_manifest(self) -> None:
        from vera_mmu.mcp_manifest import MCPManifestError, compile_mcp_manifest, verify_mcp_manifest

        with TemporaryDirectory() as first_directory, TemporaryDirectory() as second_directory:
            with self._store(Path(first_directory)) as first, self._store(Path(second_directory)) as second:
                self._declare(first, "alpha")
                manifest = compile_mcp_manifest(first, adapter_bindings={"alpha": "runner-alpha-v1"})
                self.assertEqual(verify_mcp_manifest(first, manifest), frozenset({"alpha"}))
                with self.assertRaises(MCPManifestError):
                    verify_mcp_manifest(second, manifest)
                self._declare(first, "beta")
                with self.assertRaises(MCPManifestError):
                    verify_mcp_manifest(first, manifest)

    def test_i008_manifest_contains_no_client_command_or_result_fields(self) -> None:
        from vera_mmu.mcp_manifest import compile_mcp_manifest

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                self._declare(store, "alpha")
                serialized = compile_mcp_manifest(
                    store, adapter_bindings={"alpha": "runner-alpha-v1"}
                ).canonical_json
                for forbidden in ("command", "stdout", "stderr", "exit_code", "verdict", "artifact"):
                    self.assertNotIn(f'"{forbidden}"', serialized)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.identity import load_profile
from vera_mmu.mcp_manifest import compile_mcp_manifest
from vera_mmu.store import MemoryStore


PROFILE = """
mmu:
  version: "2.0"
project:
  id: "lifecycle-adapter-project"
  name: "Lifecycle Adapter Project"
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


class FixtureLifecycleAdapter:
    adapter_id = "fixture-lifecycle-v1"
    adapter_version = "1.0.0"
    maximum_guard_mode = "SOFT"

    def session_identity(self) -> str | None:
        return "fixture-session"


class OtherVersionLifecycleAdapter(FixtureLifecycleAdapter):
    adapter_version = "2.0.0"


class LifecycleAdapterRegistryTests(unittest.TestCase):
    def _store(self, directory: Path) -> MemoryStore:
        profile_path = directory / "project.yaml"
        profile_path.write_text(PROFILE, encoding="utf-8")
        return MemoryStore.open(load_profile(profile_path), profile_path)

    @staticmethod
    def _declare(store: MemoryStore, identifier: str) -> None:
        CapabilityService(store).create(
            identifier,
            identifier,
            "CHECK",
            "1.0.0",
            parameter_schema={"type": "object", "additionalProperties": False},
            metadata={},
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
        CapabilityPolicyService(store).declare(identifier, "ALLOW", "test", actor="test")

    def _manifest(self, store: MemoryStore):
        return compile_mcp_manifest(store, adapter_bindings={"fixture-capability": "fixture-runner-v1"})

    def test_i011_i012_plan_is_canonical_and_manifest_bound(self) -> None:
        from vera_mmu.lifecycle_adapters import compile_lifecycle_adapter_plan

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                self._declare(store, "fixture-capability")
                manifest = self._manifest(store)
                first = compile_lifecycle_adapter_plan(
                    store,
                    manifest,
                    adapter_id="fixture-lifecycle-v1",
                    adapter_version="1.0.0",
                    maximum_guard_mode="SOFT",
                )
                second = compile_lifecycle_adapter_plan(
                    store,
                    manifest,
                    adapter_id="fixture-lifecycle-v1",
                    adapter_version="1.0.0",
                    maximum_guard_mode="SOFT",
                )
                self.assertEqual(first, second)
                self.assertEqual(first.format, "vera-lifecycle-adapter-plan/v1")
                self.assertEqual(first.project_identity, store.identity.as_dict())
                self.assertEqual(first.mcp_build_hash, manifest.mcp_build_hash)
                self.assertEqual(len(first.lifecycle_plan_hash), 64)
                self.assertNotIn("command", first.canonical_json)
                self.assertNotIn("ARET", first.canonical_json)

    def test_i011_i014_registry_resolves_exact_attested_adapter_only(self) -> None:
        from vera_mmu.lifecycle_adapters import (
            LifecycleAdapterRegistry,
            LifecycleAdapterRegistryError,
            compile_lifecycle_adapter_plan,
        )

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                self._declare(store, "fixture-capability")
                manifest = self._manifest(store)
                plan = compile_lifecycle_adapter_plan(
                    store,
                    manifest,
                    adapter_id="fixture-lifecycle-v1",
                    adapter_version="1.0.0",
                    maximum_guard_mode="SOFT",
                )
                adapter = FixtureLifecycleAdapter()
                self.assertIs(LifecycleAdapterRegistry((adapter,)).resolve_plan(store, manifest, plan), adapter)
                with self.assertRaises(LifecycleAdapterRegistryError):
                    LifecycleAdapterRegistry((OtherVersionLifecycleAdapter(),)).resolve_plan(store, manifest, plan)
                with self.assertRaises(LifecycleAdapterRegistryError):
                    LifecycleAdapterRegistry((adapter, adapter))
                with self.assertRaises(LifecycleAdapterRegistryError):
                    LifecycleAdapterRegistry(())

    def test_i014_facade_refuses_unpaired_lifecycle_registry_or_plan(self) -> None:
        from vera_mmu.lifecycle_adapters import LifecycleAdapterRegistry, compile_lifecycle_adapter_plan
        from vera_mmu.mcp_server import create_server

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                self._declare(store, "fixture-capability")
                manifest = self._manifest(store)
                registry = LifecycleAdapterRegistry((FixtureLifecycleAdapter(),))
                plan = compile_lifecycle_adapter_plan(
                    store,
                    manifest,
                    adapter_id="fixture-lifecycle-v1",
                    adapter_version="1.0.0",
                    maximum_guard_mode="SOFT",
                )
                with self.assertRaises(ValueError):
                    create_server(store, manifest=manifest, lifecycle_adapter_registry=registry)
                with self.assertRaises(ValueError):
                    create_server(store, manifest=manifest, lifecycle_adapter_plan=plan)

    def test_i011_i014_rejects_tampered_stale_and_command_like_plans(self) -> None:
        from vera_mmu.lifecycle_adapters import (
            LifecycleAdapterPlanError,
            LifecycleAdapterRegistry,
            compile_lifecycle_adapter_plan,
        )

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                self._declare(store, "fixture-capability")
                manifest = self._manifest(store)
                plan = compile_lifecycle_adapter_plan(
                    store,
                    manifest,
                    adapter_id="fixture-lifecycle-v1",
                    adapter_version="1.0.0",
                    maximum_guard_mode="SOFT",
                )
                registry = LifecycleAdapterRegistry((FixtureLifecycleAdapter(),))
                with self.assertRaises(LifecycleAdapterPlanError):
                    registry.resolve_plan(store, manifest, replace(plan, lifecycle_plan_hash="0" * 64))
                with self.assertRaises(LifecycleAdapterPlanError):
                    compile_lifecycle_adapter_plan(
                        store,
                        manifest,
                        adapter_id="fixture-lifecycle-v1; rm -rf /",
                        adapter_version="1.0.0",
                        maximum_guard_mode="SOFT",
                    )
                self._declare(store, "new-capability")
                with self.assertRaises(LifecycleAdapterPlanError):
                    registry.resolve_plan(store, manifest, plan)


if __name__ == "__main__":
    unittest.main()

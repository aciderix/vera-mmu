"""M5-C — I007/I008/I012/I014 : registry d’adapters MCP fermé."""

from __future__ import annotations

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
  id: "adapter-registry"
  name: "Adapter Registry"
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


class _Adapter:
    def __init__(self, adapter_id: str) -> None:
        self.adapter_id = adapter_id

    def run(self, *args: object, **kwargs: object) -> dict[str, object]:
        raise AssertionError("Le registry ne doit jamais exécuter un adapter.")


class MCPAdapterRegistryTests(unittest.TestCase):
    """Le registry résout uniquement des objets déclarés par l’hôte serveur."""

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

    def test_i007_resolves_exact_manifest_bindings(self) -> None:
        from vera_mmu.mcp_adapters import RuntimeAdapterRegistry

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                self._declare(store, "alpha")
                self._declare(store, "beta")
                alpha = _Adapter("adapter-alpha-v1")
                beta = _Adapter("adapter-beta-v1")
                manifest = compile_mcp_manifest(
                    store,
                    adapter_bindings={"alpha": alpha.adapter_id, "beta": beta.adapter_id},
                )
                resolved = RuntimeAdapterRegistry((beta, alpha)).resolve_manifest(manifest)
                self.assertEqual(tuple(resolved), ("alpha", "beta"))
                self.assertIs(resolved["alpha"], alpha)
                self.assertIs(resolved["beta"], beta)

    def test_i007_i014_refuses_missing_duplicate_or_unknown_adapter(self) -> None:
        from vera_mmu.mcp_adapters import AdapterRegistryError, RuntimeAdapterRegistry

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                self._declare(store, "alpha")
                manifest = compile_mcp_manifest(store, adapter_bindings={"alpha": "adapter-alpha-v1"})
                with self.assertRaises(AdapterRegistryError):
                    RuntimeAdapterRegistry(()).resolve_manifest(manifest)
                with self.assertRaises(AdapterRegistryError):
                    RuntimeAdapterRegistry((_Adapter("adapter-alpha-v1"), _Adapter("adapter-alpha-v1")))
                with self.assertRaises(AdapterRegistryError):
                    RuntimeAdapterRegistry((_Adapter("adapter-other-v1"),)).resolve_manifest(manifest)

    def test_i014_facade_rejects_registry_without_manifest_or_ambiguous_runtime(self) -> None:
        from vera_mmu.mcp_adapters import RuntimeAdapterRegistry
        from vera_mmu.mcp_server import create_server

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                self._declare(store, "alpha")
                adapter = _Adapter("adapter-alpha-v1")
                registry = RuntimeAdapterRegistry((adapter,))
                manifest = compile_mcp_manifest(store, adapter_bindings={"alpha": adapter.adapter_id})
                with self.assertRaises(ValueError):
                    create_server(store, adapter_registry=registry)
                with self.assertRaises(ValueError):
                    create_server(
                        store,
                        runtime_adapter=adapter,
                        adapter_registry=registry,
                        manifest=manifest,
                    )

    def test_i008_rejects_adapter_ids_that_look_like_paths_or_commands(self) -> None:
        from vera_mmu.mcp_adapters import AdapterRegistryError, RuntimeAdapterRegistry

        for adapter_id in ("bash -c id", "../adapter", "/bin/sh", "adapter/v1", "adapter v1"):
            with self.subTest(adapter_id=adapter_id):
                with self.assertRaises(AdapterRegistryError):
                    RuntimeAdapterRegistry((_Adapter(adapter_id),))


if __name__ == "__main__":
    unittest.main()

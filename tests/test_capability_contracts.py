from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractError, CapabilityContractService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore

PROFILE = '''
mmu:
  version: "2.0"
project:
  id: "contract-project"
  name: "Contract Project"
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
'''


class CapabilityContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        runtime = Path(self._directory.name) / ".vera-mmu"
        runtime.mkdir()
        self.profile_path = runtime / "project.yaml"
        self.profile_path.write_text(PROFILE, encoding="utf-8")

    def _open(self) -> MemoryStore:
        return MemoryStore.open(load_profile(self.profile_path), self.profile_path)

    def test_contract_migration_and_exact_declaration(self) -> None:
        with self._open() as store:
            self.assertEqual(store.metadata()["store_format"], {"schema_version": 19})
            capabilities = CapabilityService(store)
            capabilities.create("unit-tests", "Unit tests", "CHECK", "1.0.0")
            contract = CapabilityContractService(store).declare(
                "unit-tests", "NOOP", "DENY_NETWORK", 30,
                parameter_schema={"type": "object"}, yields_proof=False, actor="test-suite"
            )
            self.assertEqual(contract.capability_id, "unit-tests")
            self.assertEqual(contract.runner_profile, "NOOP")
            self.assertEqual(contract.network_policy, "DENY_NETWORK")
            self.assertEqual(contract.timeout_seconds, 30)
            self.assertFalse(contract.yields_proof)
            self.assertEqual(CapabilityContractService(store).get("unit-tests"), contract)

    def test_rejects_unknown_capability_invalid_contract_and_duplicates(self) -> None:
        with self._open() as store:
            service = CapabilityContractService(store)
            with self.assertRaises(CapabilityContractError):
                service.declare("unknown", "NOOP", "DENY_NETWORK", 30)
            CapabilityService(store).create("unit-tests", "Unit tests", "CHECK", "1.0.0")
            invalid = (
                lambda: service.declare("unit-tests", "SHELL", "DENY_NETWORK", 30),
                lambda: service.declare("unit-tests", "NOOP", "NETWORK", 30),
                lambda: service.declare("unit-tests", "NOOP", "DENY_NETWORK", 0),
                lambda: service.declare("unit-tests", "NOOP", "DENY_NETWORK", 30, parameter_schema=[]),
            )
            for call in invalid:
                with self.assertRaises(CapabilityContractError):
                    call()
            service.declare("unit-tests", "NOOP", "DENY_NETWORK", 30)
            with self.assertRaises(CapabilityContractError):
                service.declare("unit-tests", "NOOP", "DENY_NETWORK", 30)

    def test_contract_is_immutable_and_audited_atomically(self) -> None:
        with self._open() as store:
            CapabilityService(store).create("unit-tests", "Unit tests", "CHECK", "1.0.0")
            service = CapabilityContractService(store)
            store.connection.execute("CREATE TRIGGER reject_contract_audit BEFORE INSERT ON store_audit WHEN NEW.action = 'CAPABILITY_CONTRACT_DECLARED' BEGIN SELECT RAISE(ABORT, 'reject'); END")
            with self.assertRaises(CapabilityContractError):
                service.declare("unit-tests", "NOOP", "DENY_NETWORK", 30)
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM capability_contract").fetchone()[0], 0)
            store.connection.execute("DROP TRIGGER reject_contract_audit")
            service.declare("unit-tests", "NOOP", "DENY_NETWORK", 30)
            with self.assertRaises(sqlite3.IntegrityError):
                store.connection.execute("UPDATE capability_contract SET timeout_seconds = 1")
            with self.assertRaises(sqlite3.IntegrityError):
                store.connection.execute("DELETE FROM capability_contract")


if __name__ == "__main__":
    unittest.main()

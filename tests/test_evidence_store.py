from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.evidence import EvidenceError, EvidenceService
from vera_mmu.executions import ExecutionService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore

PROFILE = '''
mmu:
  version: "2.0"
project:
  id: "evidence-project"
  name: "Evidence Project"
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

class EvidenceStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory(); self.addCleanup(self._directory.cleanup)
        runtime=Path(self._directory.name)/'.vera-mmu'; runtime.mkdir()
        self.profile_path=runtime/'project.yaml'; self.profile_path.write_text(PROFILE)
    def _open(self) -> MemoryStore: return MemoryStore.open(load_profile(self.profile_path), self.profile_path)
    def _execution(self, store: MemoryStore) -> str:
        CapabilityService(store).create('check','Check','CHECK','1.0.0')
        CapabilityContractService(store).declare('check','NOOP','DENY_NETWORK',30)
        CapabilityPolicyService(store).declare('check','ALLOW','test policy',actor='test')
        return ExecutionService(store).run_noop('execution-001','check',{},actor='test').id
    def test_record_hashes_exact_content_and_stays_pending(self) -> None:
        with self._open() as store:
            execution=self._execution(store)
            evidence=EvidenceService(store).record('evidence-001',execution,'TEST_PROOF','PASS',{'assertion':'noop completed'},actor='test')
            self.assertEqual(evidence.execution_id,execution); self.assertEqual(evidence.verdict,'PASS')
            self.assertEqual(evidence.admission_status,'PENDING'); self.assertEqual(len(evidence.content_hash),64)
            self.assertEqual(EvidenceService(store).get('evidence-001'),evidence)
            self.assertNotIn('PROVEN',[row[0] for row in store.connection.execute("SELECT status FROM knowledge")])
    def test_refuses_unknown_execution_invalid_type_or_verdict(self) -> None:
        with self._open() as store:
            service=EvidenceService(store)
            with self.assertRaises(EvidenceError): service.record('e-1','unknown','TEST_PROOF','PASS',{})
            execution=self._execution(store)
            with self.assertRaises(EvidenceError): service.record('e-1',execution,'SHELL_PROOF','PASS',{})
            with self.assertRaises(EvidenceError): service.record('e-1',execution,'TEST_PROOF','PROMOTED',{})
    def test_immutable_and_atomic_audit(self) -> None:
        with self._open() as store:
            execution=self._execution(store); service=EvidenceService(store)
            store.connection.execute("CREATE TRIGGER reject_evidence_audit BEFORE INSERT ON store_audit WHEN NEW.action='EVIDENCE_RECORDED' BEGIN SELECT RAISE(ABORT,'reject'); END")
            with self.assertRaises(EvidenceError): service.record('e-1',execution,'TEST_PROOF','PASS',{})
            self.assertEqual(store.connection.execute('SELECT COUNT(*) FROM evidence').fetchone()[0],0)
            store.connection.execute('DROP TRIGGER reject_evidence_audit'); service.record('e-1',execution,'TEST_PROOF','PASS',{})
            with self.assertRaises(sqlite3.IntegrityError): store.connection.execute("UPDATE evidence SET admission_status='ADMITTED'")
            with self.assertRaises(sqlite3.IntegrityError): store.connection.execute('DELETE FROM evidence')

if __name__=='__main__': unittest.main()

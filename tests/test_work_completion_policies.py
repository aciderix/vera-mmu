from __future__ import annotations
from pathlib import Path
import shutil,sqlite3,tempfile,unittest
from vera_mmu.admission import AdmissionService
from vera_mmu.admission_policies import AdmissionPolicyService
from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.evidence import EvidenceService
from vera_mmu.executions import ExecutionService
from vera_mmu.gates import GateService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore
from vera_mmu.work_completion_policies import WorkCompletionPolicyError,WorkCompletionPolicyService
from vera_mmu.work_items import WorkItemService
from vera_mmu.work_lifecycle import WorkLifecycleError,WorkLifecycleService
from vera_mmu.work_readiness import WorkReadinessService
P='''mmu:\n  version: "2.0"\nproject:\n  id: "completion-policy"\n  name: "Completion Policy"\n  domain: "generic"\nworkspace:\n  root: "."\nstorage:\n  memory_dir: ".vera-mmu"\n  sqlite_file: "memory.sqlite"\n  artifacts_dir: "artifacts"\nidentity:\n  include_vcs_revision: false\n  include_profile_hash: true\n'''
class WorkCompletionPolicyTests(unittest.TestCase):
 def setUp(self):
  self.d=tempfile.TemporaryDirectory();self.addCleanup(self.d.cleanup);r=Path(self.d.name)/'.vera-mmu';r.mkdir();self.p=r/'p.yaml';self.p.write_text(P)
 def _open(self,schema_dir:Path|None=None):return MemoryStore.open(load_profile(self.p),self.p,schema_dir=schema_dir)
 def _evidence(self,s):
  CapabilityService(s).create('source','Source','CHECK','1.0.0');CapabilityContractService(s).declare('source','NOOP','DENY_NETWORK',30);CapabilityPolicyService(s).declare('source','ALLOW','test');ExecutionService(s).run_noop('run','source',{});EvidenceService(s).record('e1','run','TEST_PROOF','PASS',{'evidence':'e1'});EvidenceService(s).record('e2','run','TEST_PROOF','PASS',{'evidence':'e2'});AdmissionPolicyService(s).declare('PASS_EVIDENCE')
 def _blocked_target(self,s):
  w=WorkItemService(s);w.create('up','SUBTASK','up');w.create('target','SUBTASK','target');g=GateService(s);g.add_dependency('target','up');g.declare('gate','target','e1');g.add_requirement('gate','e2');g.declare_policy('gate','ALL')
 def test_no_policy_preserves_historical_completion_when_readiness_is_blocked(self):
  with self._open() as s:
   self.assertEqual(s.metadata()['store_format'],{'schema_version':33});self._evidence(s);self._blocked_target(s);life=WorkLifecycleService(s);self.assertEqual(WorkReadinessService(s).evaluate('target').status,'BLOCKED');life.transition('start-target','target','START','x');self.assertEqual(life.transition('complete-target','target','COMPLETE','x').event,'COMPLETE')
 def test_open_policy_preserves_historical_completion_when_readiness_is_blocked(self):
  with self._open() as s:
   self._evidence(s);self._blocked_target(s);life=WorkLifecycleService(s);life.transition('start-target','target','START','x');WorkCompletionPolicyService(s).declare('OPEN');self.assertEqual(life.transition('complete-target','target','COMPLETE','x').event,'COMPLETE')
 def test_strict_complete_refuses_then_succeeds_only_after_prerequisite_and_gate_are_ready(self):
  with self._open() as s:
   self._evidence(s);self._blocked_target(s);life=WorkLifecycleService(s);life.transition('start-target','target','START','x');p=WorkCompletionPolicyService(s).declare('REQUIRE_READY_FOR_COMPLETE',actor='test');self.assertEqual(WorkCompletionPolicyService(s).get(),p);events=len(life.history('target'));audits=len(s.audit_events())
   with self.assertRaises(WorkLifecycleError):life.transition('complete-blocked','target','COMPLETE','x')
   self.assertEqual(len(life.history('target')),events);self.assertEqual(len(s.audit_events()),audits);life.transition('start-up','up','START','x');life.transition('complete-up','up','COMPLETE','x');self.assertEqual(WorkReadinessService(s).evaluate('target').status,'BLOCKED');AdmissionService(s).decide('admit-e1','e1','ADMITTED','test');self.assertEqual(WorkReadinessService(s).evaluate('target').status,'BLOCKED');AdmissionService(s).decide('admit-e2','e2','ADMITTED','test');self.assertEqual(WorkReadinessService(s).evaluate('target').status,'READY');self.assertEqual(life.transition('complete-ready','target','COMPLETE','x').event,'COMPLETE')
 def test_policy_is_closed_immutable_and_invalid_declarations_are_atomic(self):
  with self._open() as s:
   service=WorkCompletionPolicyService(s);audits=len(s.audit_events())
   for mode in ('UNKNOWN','',None):
    with self.assertRaises(WorkCompletionPolicyError):service.declare(mode) # type:ignore[arg-type]
   self.assertEqual(s.connection.execute('SELECT COUNT(*) FROM work_completion_policy').fetchone()[0],0);self.assertEqual(len(s.audit_events()),audits);service.declare('OPEN')
   with self.assertRaises(WorkCompletionPolicyError):service.declare('REQUIRE_READY_FOR_COMPLETE')
   with self.assertRaises(sqlite3.IntegrityError):s.connection.execute("UPDATE work_completion_policy SET mode='REQUIRE_READY_FOR_COMPLETE' WHERE id=1")
   with self.assertRaises(sqlite3.IntegrityError):s.connection.execute('DELETE FROM work_completion_policy WHERE id=1')
 def test_existing_m3_22_store_upgrades_from_030_to_optional_completion_policy(self):
  schema=Path(self.d.name)/'schema';schema.mkdir();source=Path(__file__).parents[1]/'src'/'vera_mmu'/'schema'
  for version in range(1,31):
   migration=next(source.glob(f'{version:03d}_*.sql'));shutil.copyfile(migration,schema/migration.name)
  with self._open(schema) as legacy:self.assertEqual(legacy.metadata()['store_format'],{'schema_version':30});WorkItemService(legacy).create('legacy','SUBTASK','Legacy')
  migration=next(source.glob('031_*.sql'));shutil.copyfile(migration,schema/migration.name)
  with self._open(schema) as upgraded:
   self.assertEqual(upgraded.metadata()['store_format'],{'schema_version':31});self.assertEqual(WorkCompletionPolicyService(upgraded).declare('REQUIRE_READY_FOR_COMPLETE').mode,'REQUIRE_READY_FOR_COMPLETE')
if __name__=='__main__':unittest.main()

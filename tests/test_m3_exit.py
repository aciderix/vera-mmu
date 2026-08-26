from __future__ import annotations
from pathlib import Path
import shutil,tempfile,unittest
from vera_mmu.admission import AdmissionService
from vera_mmu.admission_policies import AdmissionPolicyService
from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.evidence import EvidenceService
from vera_mmu.executions import ExecutionService
from vera_mmu.gates import GateService
from vera_mmu.identity import load_profile
from vera_mmu.knowledge import KnowledgeService
from vera_mmu.proof_policies import ProofPolicyService
from vera_mmu.proofs import ProofService
from vera_mmu.store import MemoryStore
from vera_mmu.validators import ValidatorService
from vera_mmu.work_completion_policies import WorkCompletionPolicyService
from vera_mmu.work_items import WorkItemService
from vera_mmu.work_lifecycle import WorkLifecycleError,WorkLifecycleService
from vera_mmu.work_readiness import WorkReadinessService
from vera_mmu.work_start_policies import WorkStartPolicyService
P='''mmu:\n  version: "2.0"\nproject:\n  id: "m3-exit"\n  name: "M3 Exit"\n  domain: "generic"\nworkspace:\n  root: "."\nstorage:\n  memory_dir: ".vera-mmu"\n  sqlite_file: "memory.sqlite"\n  artifacts_dir: "artifacts"\nidentity:\n  include_vcs_revision: false\n  include_profile_hash: true\n'''
S={'type':'object','properties':{'validator_id':{'type':'string'},'evidence_id':{'type':'string'}},'required':['validator_id','evidence_id'],'additionalProperties':False}
class M3ExitTests(unittest.TestCase):
 def setUp(self):
  self.d=tempfile.TemporaryDirectory();self.addCleanup(self.d.cleanup);r=Path(self.d.name)/'.vera-mmu';r.mkdir();self.p=r/'p.yaml';self.p.write_text(P)
 def _open(self,schema_dir:Path|None=None):return MemoryStore.open(load_profile(self.p),self.p,schema_dir=schema_dir)
 def test_fresh_store_runs_the_entire_closed_m3_chain(self):
  with self._open() as s:
   self.assertEqual(s.metadata()['store_format'],{'schema_version':35});self.assertEqual(set(s.migration_checksums),set(range(1,36)))
   k=KnowledgeService(s);k.register_type('fact','Fact');k.append('knowledge','fact','OBSERVED','Terminal chain','content')
   CapabilityService(s).create('source','Source','CHECK','1.0.0');CapabilityContractService(s).declare('source','NOOP','DENY_NETWORK',30);CapabilityPolicyService(s).declare('source','ALLOW','exit');ExecutionService(s).run_noop('source-run','source',{});EvidenceService(s).record('evidence','source-run','TEST_PROOF','PASS',{'claim':'terminal'})
   v=ValidatorService(s);v.register('hash','EVIDENCE_HASH');CapabilityService(s).create('hash-cap','Hash','CHECK','1.0.0');CapabilityContractService(s).declare('hash-cap','EVIDENCE_HASH','DENY_NETWORK',30,parameter_schema=S);CapabilityPolicyService(s).declare('hash-cap','ALLOW','exit');self.assertEqual(ExecutionService(s).run_evidence_hash('hash-run','hash-cap',{'validator_id':'hash','evidence_id':'evidence'},validation_id='validation').status,'COMPLETED');self.assertEqual(v.get_result('validation').verdict,'PASS')
   AdmissionPolicyService(s).declare('VALIDATED_PASS_EVIDENCE');admission=AdmissionService(s).decide('admission','evidence','ADMITTED','validated',validation_id='validation');ProofPolicyService(s).declare('HMAC_SHA256',hmac_required=False);self.assertEqual(ProofService(s).promote('proof','knowledge','evidence','admission').status,'PROVEN');self.assertEqual(k.get('knowledge').status,'OBSERVED')
   w=WorkItemService(s);w.create('upstream','SUBTASK','Upstream');w.create('target','SUBTASK','Target');g=GateService(s);g.add_dependency('target','upstream');g.declare('gate','target','evidence');WorkStartPolicyService(s).declare('REQUIRE_READY');WorkCompletionPolicyService(s).declare('REQUIRE_READY_FOR_COMPLETE');l=WorkLifecycleService(s)
   with self.assertRaises(WorkLifecycleError):l.transition('target-blocked','target','START','blocked')
   l.transition('upstream-start','upstream','START','ready');l.transition('upstream-complete','upstream','COMPLETE','ready');self.assertEqual(WorkReadinessService(s).evaluate('target').status,'READY');l.transition('target-start','target','START','ready');self.assertEqual(l.transition('target-complete','target','COMPLETE','ready').event,'COMPLETE');self.assertEqual(l.get_state('target').status,'COMPLETED');self.assertEqual(s.connection.execute('SELECT COUNT(*) FROM admission_validation_binding').fetchone()[0],1);self.assertEqual(s.connection.execute('SELECT COUNT(*) FROM knowledge_proof').fetchone()[0],1)
 def test_historical_store_upgrades_from_001_to_032(self):
  schema=Path(self.d.name)/'schema';schema.mkdir();source=Path(__file__).parents[1]/'src'/'vera_mmu'/'schema';first=next(source.glob('001_*.sql'));shutil.copyfile(first,schema/first.name)
  with self._open(schema) as legacy:self.assertEqual(legacy.metadata()['store_format'],{'schema_version':1})
  for version in range(2,34):
   migration=next(source.glob(f'{version:03d}_*.sql'));shutil.copyfile(migration,schema/migration.name)
  with self._open(schema) as upgraded:self.assertEqual(upgraded.metadata()['store_format'],{'schema_version':33});self.assertEqual(set(upgraded.migration_checksums),set(range(1,34)))
if __name__=='__main__':unittest.main()

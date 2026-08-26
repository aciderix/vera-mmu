from __future__ import annotations
from pathlib import Path
import tempfile,unittest
from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.evidence import EvidenceService
from vera_mmu.executions import ExecutionError,ExecutionService
from vera_mmu.identity import load_profile
from vera_mmu.runner_validator_compatibility import RunnerValidatorCompatibilityError,ensure_runner_validator_compatibility
from vera_mmu.store import MemoryStore
from vera_mmu.validators import ValidatorService
P='''mmu:\n  version: "2.0"\nproject:\n  id: "runner-validator-catalog"\n  name: "Runner Validator Catalog"\n  domain: "generic"\nworkspace:\n  root: "."\nstorage:\n  memory_dir: ".vera-mmu"\n  sqlite_file: "memory.sqlite"\n  artifacts_dir: "artifacts"\nidentity:\n  include_vcs_revision: false\n  include_profile_hash: true\n'''
S={'type':'object','properties':{'validator_id':{'type':'string'},'evidence_id':{'type':'string'}},'required':['validator_id','evidence_id'],'additionalProperties':False}
BAD={'type':'object','properties':{'validator_id':{'type':'string'}},'required':['validator_id'],'additionalProperties':False}
class RunnerValidatorCompatibilityTests(unittest.TestCase):
 def setUp(self):
  self.d=tempfile.TemporaryDirectory();self.addCleanup(self.d.cleanup);r=Path(self.d.name)/'.vera-mmu';r.mkdir();self.p=r/'p.yaml';self.p.write_text(P)
 def _open(self):return MemoryStore.open(load_profile(self.p),self.p)
 def _setup(self,s):
  CapabilityService(s).create('source','Source','CHECK','1.0.0');CapabilityContractService(s).declare('source','NOOP','DENY_NETWORK',30);CapabilityPolicyService(s).declare('source','ALLOW','test');ExecutionService(s).run_noop('seed','source',{});EvidenceService(s).record('good','seed','TEST_PROOF','PASS',{'claim':'x'});EvidenceService(s).record('bad','seed','TEST_PROOF','PASS',{});v=ValidatorService(s);v.register('hash','EVIDENCE_HASH');v.register('fields','EVIDENCE_FIELDS',required_keys=('claim',))
  for capability,runner,schema in (('hash-cap','EVIDENCE_HASH',S),('fields-cap','EVIDENCE_FIELDS',S),('wrong-cap','EVIDENCE_HASH',BAD)):
   CapabilityService(s).create(capability,capability,'CHECK','1.0.0');CapabilityContractService(s).declare(capability,runner,'DENY_NETWORK',30,parameter_schema=schema,yields_proof=False);CapabilityPolicyService(s).declare(capability,'ALLOW','test')
 def test_catalog_accepts_only_exact_runner_validator_schema_pairs(self):
  for runner,kind in (('EVIDENCE_HASH','EVIDENCE_HASH'),('EVIDENCE_FIELDS','EVIDENCE_FIELDS')):self.assertIsNone(ensure_runner_validator_compatibility(runner,kind,S))
  for runner,kind,schema in (('EVIDENCE_HASH','EVIDENCE_FIELDS',S),('EVIDENCE_FIELDS','EVIDENCE_HASH',S),('NOOP','EVIDENCE_HASH',S),('EVIDENCE_HASH','EVIDENCE_HASH',BAD)):
   with self.assertRaises(RunnerValidatorCompatibilityError):ensure_runner_validator_compatibility(runner,kind,schema)
 def test_closed_runners_enforce_catalog_before_writes_and_preserve_pass_fail(self):
  with self._open() as s:
   self.assertEqual(s.metadata()['store_format'],{'schema_version':36});self._setup(s);e=ExecutionService(s);self.assertEqual(e.run_evidence_hash('hash-pass','hash-cap',{'validator_id':'hash','evidence_id':'good'},validation_id='hash-v').status,'COMPLETED');self.assertEqual(e.run_evidence_fields('fields-pass','fields-cap',{'validator_id':'fields','evidence_id':'good'},validation_id='fields-v').status,'COMPLETED');self.assertEqual(e.run_evidence_fields('fields-fail','fields-cap',{'validator_id':'fields','evidence_id':'bad'},validation_id='fields-f').status,'COMPLETED');self.assertEqual(ValidatorService(s).get_result('fields-f').verdict,'FAIL');executions=s.connection.execute('SELECT COUNT(*) FROM execution').fetchone()[0];validations=s.connection.execute('SELECT COUNT(*) FROM validation_result').fetchone()[0];audits=len(s.audit_events())
   for identifier,method,capability,validator in (('cross-hash',e.run_evidence_hash,'hash-cap','fields'),('cross-fields',e.run_evidence_fields,'fields-cap','hash'),('wrong-schema',e.run_evidence_hash,'wrong-cap','hash')):
    with self.assertRaises(ExecutionError):method(identifier,capability,{'validator_id':validator,'evidence_id':'bad'},validation_id=identifier+'-v')
    self.assertEqual(s.connection.execute('SELECT COUNT(*) FROM execution').fetchone()[0],executions);self.assertEqual(s.connection.execute('SELECT COUNT(*) FROM validation_result').fetchone()[0],validations);self.assertEqual(len(s.audit_events()),audits)
   self.assertEqual(s.connection.execute('SELECT COUNT(*) FROM evidence_admission').fetchone()[0],0);self.assertEqual(s.connection.execute('SELECT COUNT(*) FROM knowledge_proof').fetchone()[0],0)
if __name__=='__main__':unittest.main()

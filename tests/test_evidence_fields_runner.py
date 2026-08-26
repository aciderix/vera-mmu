from __future__ import annotations
from pathlib import Path
import tempfile,unittest
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore
from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.evidence import EvidenceService
from vera_mmu.executions import ExecutionService,ExecutionError
from vera_mmu.validators import ValidatorService
P='''mmu:\n  version: "2.0"\nproject:\n  id: "fields-runner"\n  name: "Fields Runner"\n  domain: "generic"\nworkspace:\n  root: "."\nstorage:\n  memory_dir: ".vera-mmu"\n  sqlite_file: "memory.sqlite"\n  artifacts_dir: "artifacts"\nidentity:\n  include_vcs_revision: false\n  include_profile_hash: true\n'''
S={'type':'object','properties':{'validator_id':{'type':'string'},'evidence_id':{'type':'string'}},'required':['validator_id','evidence_id'],'additionalProperties':False}
class FieldsRunner(unittest.TestCase):
 def setUp(self):
  self.d=tempfile.TemporaryDirectory();self.addCleanup(self.d.cleanup);r=Path(self.d.name)/'.vera-mmu';r.mkdir();self.p=r/'p.yaml';self.p.write_text(P)
 def test_runner_persists_fields_verdict_without_admission_or_proof(self):
  with MemoryStore.open(load_profile(self.p),self.p) as s:
   self.assertEqual(s.metadata()['store_format'],{'schema_version':31});CapabilityService(s).create('source','S','CHECK','1.0.0');CapabilityContractService(s).declare('source','NOOP','DENY_NETWORK',30);CapabilityPolicyService(s).declare('source','ALLOW','x');ExecutionService(s).run_noop('seed','source',{});EvidenceService(s).record('ok','seed','TEST_PROOF','PASS',{'claim':'x','scope':'u'});EvidenceService(s).record('bad','seed','TEST_PROOF','PASS',{'claim':'x'});ValidatorService(s).register('fields','EVIDENCE_FIELDS',required_keys=('claim','scope'));CapabilityService(s).create('check','C','CHECK','1.0.0');CapabilityContractService(s).declare('check','EVIDENCE_FIELDS','DENY_NETWORK',30,parameter_schema=S,yields_proof=False);CapabilityPolicyService(s).declare('check','ALLOW','x');e=ExecutionService(s);self.assertEqual(e.run_evidence_fields('x1','check',{'validator_id':'fields','evidence_id':'ok'},validation_id='v1').status,'COMPLETED');self.assertEqual(ValidatorService(s).get_result('v1').verdict,'PASS');e.run_evidence_fields('x2','check',{'validator_id':'fields','evidence_id':'bad'},validation_id='v2');self.assertEqual(ValidatorService(s).get_result('v2').verdict,'FAIL');self.assertEqual(s.connection.execute('SELECT COUNT(*) FROM evidence_admission').fetchone()[0],0);self.assertEqual(s.connection.execute('SELECT COUNT(*) FROM knowledge_proof').fetchone()[0],0)
if __name__=='__main__':unittest.main()

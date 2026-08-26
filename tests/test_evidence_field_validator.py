from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.evidence import EvidenceService
from vera_mmu.executions import ExecutionService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore
from vera_mmu.validators import ValidatorError, ValidatorService

PROFILE='''
mmu:
  version: "2.0"
project:
  id: "field-validator-project"
  name: "Field Validator"
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

class EvidenceFieldValidatorTests(unittest.TestCase):
 def setUp(self):
  self.d=tempfile.TemporaryDirectory();self.addCleanup(self.d.cleanup);r=Path(self.d.name)/'.vera-mmu';r.mkdir();self.p=r/'p.yaml';self.p.write_text(PROFILE)
 def _open(self):return MemoryStore.open(load_profile(self.p),self.p)
 def _evidence(self,s):
  CapabilityService(s).create('c','C','CHECK','1.0.0');CapabilityContractService(s).declare('c','NOOP','DENY_NETWORK',30);CapabilityPolicyService(s).declare('c','ALLOW','test');ExecutionService(s).run_noop('x','c',{});EvidenceService(s).record('pass','x','TEST_PROOF','PASS',{'claim':'ok','scope':'unit'});EvidenceService(s).record('fail','x','TEST_PROOF','PASS',{'claim':'missing'})
 def test_declared_required_keys_produce_local_pass_fail_without_admission(self):
  with self._open() as s:
   self.assertEqual(s.metadata()['store_format'],{'schema_version':35});self._evidence(s);v=ValidatorService(s);v.register('fields','EVIDENCE_FIELDS',required_keys=('claim','scope'))
   self.assertEqual(v.validate('vp','fields','pass').verdict,'PASS');self.assertEqual(v.validate('vf','fields','fail').verdict,'FAIL');self.assertEqual(s.connection.execute('SELECT COUNT(*) FROM evidence_admission').fetchone()[0],0)
 def test_closed_rules_refuse_before_validator_or_result_write(self):
  with self._open() as s:
   self._evidence(s);v=ValidatorService(s);audits=len(s.audit_events())
   for rule in ((),('claim','claim'),('bad/key',)):
    with self.assertRaises(ValidatorError):v.register('fields-'+str(len(rule)),'EVIDENCE_FIELDS',required_keys=rule)
   self.assertEqual(s.connection.execute('SELECT COUNT(*) FROM validator').fetchone()[0],0);self.assertEqual(len(s.audit_events()),audits)
if __name__=='__main__':unittest.main()

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from vera_mmu.admission import AdmissionError, AdmissionService
from vera_mmu.admission_policies import AdmissionPolicyService
from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.evidence import EvidenceService
from vera_mmu.executions import ExecutionService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore

PROFILE='''
mmu:
  version: "2.0"
project:
  id: "admission-project"
  name: "Admission Project"
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
class AdmissionTests(unittest.TestCase):
 def setUp(self):
  self.d=tempfile.TemporaryDirectory();self.addCleanup(self.d.cleanup);r=Path(self.d.name)/'.vera-mmu';r.mkdir();self.p=r/'p.yaml';self.p.write_text(PROFILE)
 def store(self): return MemoryStore.open(load_profile(self.p),self.p)
 def evidence(self,s,verdict='PASS'):
  CapabilityService(s).create('c','C','CHECK','1.0.0');CapabilityContractService(s).declare('c','NOOP','DENY_NETWORK',30);CapabilityPolicyService(s).declare('c','ALLOW','test policy');ExecutionService(s).run_noop('x','c',{});return EvidenceService(s).record('e','x','TEST_PROOF',verdict,{})
 def test_admits_pass_without_mutating_evidence_or_knowledge(self):
  with self.store() as s:
   self.evidence(s);AdmissionPolicyService(s).declare('PASS_EVIDENCE');d=AdmissionService(s).decide('d','e','ADMITTED','verified',actor='t')
   self.assertEqual(d.decision,'ADMITTED');self.assertEqual(EvidenceService(s).get('e').admission_status,'PENDING');self.assertEqual(s.connection.execute('SELECT COUNT(*) FROM knowledge').fetchone()[0],0)
 def test_refuses_admit_nonpass_and_duplicate(self):
  with self.store() as s:
   self.evidence(s,'FAIL');a=AdmissionService(s)
   with self.assertRaises(AdmissionError):a.decide('d','e','ADMITTED','bad')
   self.assertEqual(a.decide('d','e','REJECTED','diagnostic').decision,'REJECTED')
   with self.assertRaises(AdmissionError):a.decide('d2','e','REJECTED','again')
if __name__=='__main__':unittest.main()

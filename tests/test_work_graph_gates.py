from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from vera_mmu.admission import AdmissionService
from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.evidence import EvidenceService
from vera_mmu.executions import ExecutionService
from vera_mmu.gates import GateError, GateService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore
from vera_mmu.work_items import WorkItemService

PROFILE='''
mmu:
  version: "2.0"
project:
  id: "gate-project"
  name: "Gate"
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
class GateTests(unittest.TestCase):
 def setUp(self):
  self.d=tempfile.TemporaryDirectory();self.addCleanup(self.d.cleanup);r=Path(self.d.name)/'.vera-mmu';r.mkdir();self.p=r/'p.yaml';self.p.write_text(PROFILE)
 def _store(self):return MemoryStore.open(load_profile(self.p),self.p)
 def _evidence(self,s):
  CapabilityService(s).create('c','C','CHECK','1.0.0');CapabilityContractService(s).declare('c','NOOP','DENY_NETWORK',30);CapabilityPolicyService(s).declare('c','ALLOW','test policy');ExecutionService(s).run_noop('x','c',{});EvidenceService(s).record('e','x','TEST_PROOF','PASS',{})
 def test_dependency_cycle_and_admission_gate(self):
  with self._store() as s:
   w=WorkItemService(s);w.create('a','GOAL','A');w.create('b','SUBTASK','B')
   g=GateService(s);g.add_dependency('b','a')
   with self.assertRaises(GateError):g.add_dependency('a','b')
   self._evidence(s)
   g.declare('gate-1','b','e')
   self.assertEqual(g.evaluate('gate-1').status,'FAIL')
   AdmissionService(s).decide('a','e','ADMITTED','ok')
   self.assertEqual(g.evaluate('gate-1').status,'PASS')
if __name__=='__main__':unittest.main()

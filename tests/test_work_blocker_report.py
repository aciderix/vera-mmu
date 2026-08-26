from __future__ import annotations
from pathlib import Path
import tempfile,unittest
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore
from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.executions import ExecutionService
from vera_mmu.evidence import EvidenceService
from vera_mmu.admission_policies import AdmissionPolicyService
from vera_mmu.work_items import WorkItemService
from vera_mmu.gates import GateService
from vera_mmu.work_blocker_reports import WorkBlockerReportService
P='''mmu:\n  version: "2.0"\nproject:\n  id: "blocker-report"\n  name: "Blocker Report"\n  domain: "generic"\nworkspace:\n  root: "."\nstorage:\n  memory_dir: ".vera-mmu"\n  sqlite_file: "memory.sqlite"\n  artifacts_dir: "artifacts"\nidentity:\n  include_vcs_revision: false\n  include_profile_hash: true\n'''
class WorkBlockerReportTests(unittest.TestCase):
 def setUp(self):
  self.d=tempfile.TemporaryDirectory();self.addCleanup(self.d.cleanup);r=Path(self.d.name)/'.vera-mmu';r.mkdir();self.p=r/'p.yaml';self.p.write_text(P)
 def test_composes_transitive_dependencies_and_direct_failing_gates_without_mutation(self):
  with MemoryStore.open(load_profile(self.p),self.p) as s:
   w=WorkItemService(s)
   for i in ('a','b','c'):w.create(i,'SUBTASK',i)
   g=GateService(s);g.add_dependency('a','b');g.add_dependency('b','c')
   CapabilityService(s).create('source','S','CHECK','1.0.0');CapabilityContractService(s).declare('source','NOOP','DENY_NETWORK',30);CapabilityPolicyService(s).declare('source','ALLOW','x');ExecutionService(s).run_noop('run','source',{});EvidenceService(s).record('e','run','TEST_PROOF','PASS',{'x':'y'});AdmissionPolicyService(s).declare('PASS_EVIDENCE');g.declare('gate-a','a','e');audits=len(s.audit_events())
   r=WorkBlockerReportService(s).diagnose('a')
   self.assertEqual([(x.kind,x.identifier,x.status) for x in r.dependencies],[('PREREQUISITE','b','PLANNED'),('PREREQUISITE','c','PLANNED')])
   self.assertEqual([(x.gate_id,x.status,x.admitted_count,x.required_count) for x in r.gates],[('gate-a','FAIL',0,1)])
   self.assertEqual(r.status,'BLOCKED');self.assertEqual(len(s.audit_events()),audits)
if __name__=='__main__':unittest.main()

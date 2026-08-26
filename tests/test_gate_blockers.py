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
from vera_mmu.admission import AdmissionService
from vera_mmu.work_items import WorkItemService
from vera_mmu.gates import GateService
from vera_mmu.gate_blockers import GateBlockerService
P='''mmu:\n  version: "2.0"\nproject:\n  id: "gate-blockers"\n  name: "Gate Blockers"\n  domain: "generic"\nworkspace:\n  root: "."\nstorage:\n  memory_dir: ".vera-mmu"\n  sqlite_file: "memory.sqlite"\n  artifacts_dir: "artifacts"\nidentity:\n  include_vcs_revision: false\n  include_profile_hash: true\n'''
class GateBlockers(unittest.TestCase):
 def setUp(self):
  self.d=tempfile.TemporaryDirectory();self.addCleanup(self.d.cleanup);r=Path(self.d.name)/'.vera-mmu';r.mkdir();self.p=r/'p.yaml';self.p.write_text(P)
 def test_reports_failing_direct_gate_without_mutation_then_clears_on_admission(self):
  with MemoryStore.open(load_profile(self.p),self.p) as s:
   CapabilityService(s).create('source','S','CHECK','1.0.0');CapabilityContractService(s).declare('source','NOOP','DENY_NETWORK',30);CapabilityPolicyService(s).declare('source','ALLOW','x');ExecutionService(s).run_noop('run','source',{});EvidenceService(s).record('e','run','TEST_PROOF','PASS',{'x':'y'});AdmissionPolicyService(s).declare('PASS_EVIDENCE');WorkItemService(s).create('target','SUBTASK','target');GateService(s).declare('target','target','e');a=len(s.audit_events());b=GateBlockerService(s).diagnose('target');self.assertEqual([(x.gate_id,x.status,x.admitted_count,x.required_count) for x in b],[('target','FAIL',0,1)]);self.assertEqual(len(s.audit_events()),a);AdmissionService(s).decide('admit','e','ADMITTED','x');self.assertEqual(GateBlockerService(s).diagnose('target'),())
if __name__=='__main__':unittest.main()

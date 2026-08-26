from __future__ import annotations
from pathlib import Path
import tempfile,unittest
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore
from vera_mmu.work_items import WorkItemService
from vera_mmu.gates import GateService
from vera_mmu.work_lifecycle import WorkLifecycleService
from vera_mmu.work_blockers import WorkBlockerService
P='''mmu:\n  version: "2.0"\nproject:\n  id: "work-blockers"\n  name: "Work Blockers"\n  domain: "generic"\nworkspace:\n  root: "."\nstorage:\n  memory_dir: ".vera-mmu"\n  sqlite_file: "memory.sqlite"\n  artifacts_dir: "artifacts"\nidentity:\n  include_vcs_revision: false\n  include_profile_hash: true\n'''
class WorkBlockers(unittest.TestCase):
 def setUp(self):
  self.d=tempfile.TemporaryDirectory();self.addCleanup(self.d.cleanup);r=Path(self.d.name)/'.vera-mmu';r.mkdir();self.p=r/'p.yaml';self.p.write_text(P)
 def test_reports_direct_uncompleted_prerequisite_without_writes(self):
  with MemoryStore.open(load_profile(self.p),self.p) as s:
   w=WorkItemService(s);w.create('up','SUBTASK','up');w.create('target','SUBTASK','target');GateService(s).add_dependency('target','up');audits=len(s.audit_events());b=WorkBlockerService(s).diagnose('target');self.assertEqual([(x.kind,x.identifier,x.status) for x in b],[('PREREQUISITE','up','PLANNED')]);self.assertEqual(len(s.audit_events()),audits);WorkLifecycleService(s).transition('start','up','START','x');WorkLifecycleService(s).transition('done','up','COMPLETE','x');self.assertEqual(WorkBlockerService(s).diagnose('target'),())
if __name__=='__main__':unittest.main()

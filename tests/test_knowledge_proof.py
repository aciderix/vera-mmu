from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from vera_mmu.admission import AdmissionService
from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.evidence import EvidenceService
from vera_mmu.executions import ExecutionService
from vera_mmu.identity import load_profile
from vera_mmu.knowledge import KnowledgeService
from vera_mmu.proofs import ProofError, ProofService
from vera_mmu.store import MemoryStore

PROFILE='''
mmu:
  version: "2.0"
project:
  id: "proof-project"
  name: "Proof Project"
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
class ProofTests(unittest.TestCase):
 def setUp(self):
  self.d=tempfile.TemporaryDirectory();self.addCleanup(self.d.cleanup);r=Path(self.d.name)/'.vera-mmu';r.mkdir();self.p=r/'p.yaml';self.p.write_text(PROFILE)
 def _store(self):return MemoryStore.open(load_profile(self.p),self.p)
 def _ready(self,s):
  k=KnowledgeService(s);k.register_type('fact','Fact');k.append('k','fact','OBSERVED','T','content')
  CapabilityService(s).create('c','C','CHECK','1.0.0');CapabilityContractService(s).declare('c','NOOP','DENY_NETWORK',30);ExecutionService(s).run_noop('x','c',{})
  EvidenceService(s).record('e','x','TEST_PROOF','PASS',{});AdmissionService(s).decide('a','e','ADMITTED','ok')
 def test_derived_proven_record_preserves_knowledge(self):
  with self._store() as s:
   self._ready(s);proof=ProofService(s).promote('p','k','e','a',actor='t')
   self.assertEqual(proof.knowledge_id,'k');self.assertEqual(proof.status,'PROVEN');self.assertEqual(KnowledgeService(s).get('k').status,'OBSERVED')
 def test_hmac_required_refuses_missing_or_invalid_secret(self):
  with self._store() as s:
   self._ready(s);service=ProofService(s,hmac_required=True)
   with self.assertRaises(ProofError):service.promote('p','k','e','a')
if __name__=='__main__':unittest.main()

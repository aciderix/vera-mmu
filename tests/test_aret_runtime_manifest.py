from __future__ import annotations
from pathlib import Path
import unittest
from vera_mmu.domain_packs.aret.runtime import AretLegacyRuntimeLayout,legacy_runtime_layout
class AretRuntimeManifestTests(unittest.TestCase):
 def test_declares_exact_legacy_runtime_layout_without_resolving_it(self):
  layout=legacy_runtime_layout();self.assertEqual(layout,AretLegacyRuntimeLayout(environment_override='ARET_MEMORY_DIR',default_runtime_dir='.aret-memory',sqlite_filename='aret_memory.sqlite',artifacts_dirname='artifacts',exports_dirname='exports'));self.assertEqual(layout.relative_members,('.aret-memory/aret_memory.sqlite','.aret-memory/artifacts','.aret-memory/exports'))
 def test_manifest_is_pack_local_and_has_no_core_storage_dependency(self):
  core=Path(__file__).parents[1]/'src'/'vera_mmu'
  for path in (core/'store.py',core/'workspace.py',core/'identity.py'):
   self.assertNotIn('domain_packs.aret',path.read_text(encoding='utf-8'))
  self.assertEqual(AretLegacyRuntimeLayout.__module__,'vera_mmu.domain_packs.aret.runtime')
if __name__=='__main__':unittest.main()

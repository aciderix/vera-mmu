from __future__ import annotations
from pathlib import Path
import unittest
from vera_mmu.domain_packs.aret.profile import AretCompatibilityProfile,aret_v1_compatibility_profile
class AretCompatibilityProfileTests(unittest.TestCase):
 def test_composes_closed_v1_contracts_and_declares_limits(self):
  profile=aret_v1_compatibility_profile();self.assertIsInstance(profile,AretCompatibilityProfile);self.assertEqual(profile.profile_id,'aret-v1-compatibility');self.assertEqual(profile.version,'1');self.assertEqual(profile.address_scheme,'ARET://');self.assertEqual(profile.supported_operations,('parse_address','describe_runtime','describe_schema'));self.assertEqual(profile.forbidden_operations,('resolve_runtime','read_sqlite','import_data','write_vera'));self.assertEqual(profile.runtime.default_runtime_dir,'.aret-memory');self.assertEqual(profile.schema.migration_versions,(1,2,3,4,5,6))
 def test_profile_is_pack_local_and_core_independent(self):
  self.assertEqual(AretCompatibilityProfile.__module__,'vera_mmu.domain_packs.aret.profile')
  core=Path(__file__).parents[1]/'src'/'vera_mmu'
  for path in (core/'store.py',core/'workspace.py',core/'identity.py'):
   self.assertNotIn('domain_packs.aret',path.read_text(encoding='utf-8'))
if __name__=='__main__':unittest.main()

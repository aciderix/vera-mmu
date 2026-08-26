from __future__ import annotations
from pathlib import Path
import unittest
from vera_mmu.domain_packs.aret.schema import AretLegacySchemaManifest,aret_v1_schema_manifest
class AretSchemaManifestTests(unittest.TestCase):
 def test_declares_observed_v1_migrations_and_application_tables(self):
  manifest=aret_v1_schema_manifest();self.assertIsInstance(manifest,AretLegacySchemaManifest);self.assertEqual(manifest.migration_versions,(1,2,3,4,5,6));self.assertEqual(manifest.application_tables,('asset','audit_event','brick','bundle_import','component','front_state','function_symbol','id_sequence','knowledge','knowledge_source','knowledge_tag','migration_batch','pipeline_run','proof','proof_link','relation','schema_migrations','store_metadata'))
 def test_manifest_excludes_fts_internals_and_is_pack_local(self):
  manifest=aret_v1_schema_manifest();self.assertTrue(all(not table.startswith('knowledge_fts') for table in manifest.application_tables));self.assertEqual(AretLegacySchemaManifest.__module__,'vera_mmu.domain_packs.aret.schema')
  core=Path(__file__).parents[1]/'src'/'vera_mmu'
  for path in (core/'store.py',core/'workspace.py',core/'identity.py'):
   self.assertNotIn('domain_packs.aret',path.read_text(encoding='utf-8'))
if __name__=='__main__':unittest.main()

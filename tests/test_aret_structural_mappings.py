from __future__ import annotations
from pathlib import Path
import unittest
from vera_mmu.domain_packs.aret.mapping import AretStructuralMapping,aret_v1_structural_mappings
class AretStructuralMappingTests(unittest.TestCase):
 def test_closed_explicitly_reviewed_structural_mappings(self):
  mappings=aret_v1_structural_mappings();self.assertEqual(mappings,(AretStructuralMapping('component','entity','COMPONENT'),AretStructuralMapping('function_symbol','symbol',None),AretStructuralMapping('brick','work_item',None)))
  self.assertTrue(all(mapping.requires_explicit_import for mapping in mappings))
 def test_registry_does_not_map_data_or_operational_tables(self):
  sources={mapping.legacy_table for mapping in aret_v1_structural_mappings()};self.assertFalse(sources & {'knowledge','proof','proof_link','relation','asset','audit_event','front_state','pipeline_run','bundle_import'})
  self.assertEqual(AretStructuralMapping.__module__,'vera_mmu.domain_packs.aret.mapping')
  core=Path(__file__).parents[1]/'src'/'vera_mmu'
  for path in (core/'store.py',core/'workspace.py',core/'identity.py'):
   self.assertNotIn('domain_packs.aret',path.read_text(encoding='utf-8'))
if __name__=='__main__':unittest.main()

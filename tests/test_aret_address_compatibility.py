from __future__ import annotations
from pathlib import Path
import unittest
from vera_mmu.domain_packs.aret.addressing import AretAddressCompatibilityError,AretAddress,make_aret_address,parse_aret_address
class AretAddressCompatibilityTests(unittest.TestCase):
 def test_round_trip_closed_legacy_resources(self):
  for resource,identifier in (('knowledge','KN-001'),('component','comp.name'),('function','sym!_-.42'),('brick','B-42'),('proof','P-1'),('relation','R-1'),('asset','AST-1'),('pipeline','pipe-1')):
   address=make_aret_address(resource,identifier);self.assertEqual(parse_aret_address(address),AretAddress(resource,identifier));self.assertEqual(parse_aret_address(address).canonical,address)
  self.assertEqual(parse_aret_address('ARET://front/current'),AretAddress('front','current'))
 def test_percent_encoded_identifier_requires_exact_canonical_form(self):
  address='ARET://knowledge/alpha%20beta';self.assertEqual(parse_aret_address(address).identifier,'alpha beta');self.assertEqual(make_aret_address('knowledge','alpha beta'),address)
  for value in ('ARET://knowledge/alpha beta','ARET://knowledge/alpha%2fbeta','ARET://knowledge/alpha%2Fbeta','ARET://knowledge/%41','ARET://knowledge/%ZZ'):
   with self.assertRaises(AretAddressCompatibilityError):parse_aret_address(value)
 def test_rejects_unknown_noncanonical_or_write_like_inputs(self):
  for value in ('vera://p/knowledge/x','aret://knowledge/x','ARET://','ARET://knowledge','ARET://unknown/x','ARET://knowledge/x/y','ARET://front/x','ARET://front/current/extra','ARET://knowledge/../x'):
   with self.assertRaises(AretAddressCompatibilityError):parse_aret_address(value)
  for resource,identifier in (('unknown','x'),('knowledge',''),('knowledge','x/y'),('front','other')):
   with self.assertRaises(AretAddressCompatibilityError):make_aret_address(resource,identifier)
 def test_pack_does_not_create_a_core_dependency_or_storage_effect(self):
  core=Path(__file__).parents[1]/'src'/'vera_mmu'
  for path in (core/'addressing.py',core/'store.py',core/'identity.py'):
   self.assertNotIn('domain_packs.aret',path.read_text(encoding='utf-8'))
  self.assertEqual(AretAddress.__module__,'vera_mmu.domain_packs.aret.addressing')
if __name__=='__main__':unittest.main()

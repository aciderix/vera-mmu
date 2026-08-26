from __future__ import annotations
from pathlib import Path
import shutil,sqlite3,tempfile,unittest
from vera_mmu.admission import AdmissionError,AdmissionService
from vera_mmu.admission_policies import AdmissionPolicyService
from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.evidence import EvidenceService
from vera_mmu.executions import ExecutionService
from vera_mmu.identity import load_profile
from vera_mmu.store import MemoryStore
from vera_mmu.validators import ValidatorService
P='''mmu:\n  version: "2.0"\nproject:\n  id: "admission-binding"\n  name: "Admission Binding"\n  domain: "generic"\nworkspace:\n  root: "."\nstorage:\n  memory_dir: ".vera-mmu"\n  sqlite_file: "memory.sqlite"\n  artifacts_dir: "artifacts"\nidentity:\n  include_vcs_revision: false\n  include_profile_hash: true\n'''
class AdmissionValidationBindingTests(unittest.TestCase):
 def setUp(self):
  self.d=tempfile.TemporaryDirectory();self.addCleanup(self.d.cleanup);r=Path(self.d.name)/'.vera-mmu';r.mkdir();self.p=r/'p.yaml';self.p.write_text(P)
 def _open(self,schema_dir:Path|None=None):return MemoryStore.open(load_profile(self.p),self.p,schema_dir=schema_dir)
 def _evidence_and_validations(self,s):
  CapabilityService(s).create('source','Source','CHECK','1.0.0');CapabilityContractService(s).declare('source','NOOP','DENY_NETWORK',30);CapabilityPolicyService(s).declare('source','ALLOW','test');ExecutionService(s).run_noop('run','source',{});EvidenceService(s).record('e1','run','TEST_PROOF','PASS',{});EvidenceService(s).record('e2','run','TEST_PROOF','PASS',{});v=ValidatorService(s);v.register('hash','EVIDENCE_HASH');v.register('fields','EVIDENCE_FIELDS',required_keys=('required',));self.assertEqual(v.validate('pass-e1','hash','e1').verdict,'PASS');self.assertEqual(v.validate('pass-e2','hash','e2').verdict,'PASS');self.assertEqual(v.validate('fail-e1','fields','e1').verdict,'FAIL')
 def test_strict_policy_requires_explicit_same_evidence_pass_binding_atomically(self):
  with self._open() as s:
   self.assertEqual(s.metadata()['store_format'],{'schema_version':36});self._evidence_and_validations(s);AdmissionPolicyService(s).declare('VALIDATED_PASS_EVIDENCE');service=AdmissionService(s);audits=len(s.audit_events())
   for identifier,validation in (('missing',None),('cross','pass-e2'),('failed','fail-e1')):
    with self.assertRaises(AdmissionError):service.decide(identifier,'e1','ADMITTED','strict',validation_id=validation)
    self.assertEqual(s.connection.execute('SELECT COUNT(*) FROM evidence_admission').fetchone()[0],0);self.assertEqual(s.connection.execute('SELECT COUNT(*) FROM admission_validation_binding').fetchone()[0],0);self.assertEqual(len(s.audit_events()),audits)
   admission=service.decide('admit','e1','ADMITTED','strict',validation_id='pass-e1');self.assertEqual((admission.decision,admission.validation_id),('ADMITTED','pass-e1'));row=s.connection.execute('SELECT admission_id,validation_id,evidence_id FROM admission_validation_binding').fetchone();self.assertEqual(tuple(row),('admit','pass-e1','e1'))
 def test_permissive_policy_remains_compatible_and_does_not_create_binding(self):
  with self._open() as s:
   self._evidence_and_validations(s);AdmissionPolicyService(s).declare('PASS_EVIDENCE');admission=AdmissionService(s).decide('admit','e1','ADMITTED','manual');self.assertEqual((admission.decision,admission.validation_id),('ADMITTED',None));self.assertEqual(s.connection.execute('SELECT COUNT(*) FROM admission_validation_binding').fetchone()[0],0)
 def test_binding_table_rejects_cross_evidence_fail_and_duplicates(self):
  with self._open() as s:
   self._evidence_and_validations(s);AdmissionPolicyService(s).declare('VALIDATED_PASS_EVIDENCE');service=AdmissionService(s);service.decide('admit','e1','ADMITTED','strict',validation_id='pass-e1')
   with self.assertRaises(sqlite3.IntegrityError):s.connection.execute("INSERT INTO admission_validation_binding(admission_id,validation_id,evidence_id,created_at,created_by) VALUES('admit','pass-e2','e1','now','test')")
   with self.assertRaises(sqlite3.IntegrityError):s.connection.execute("INSERT INTO admission_validation_binding(admission_id,validation_id,evidence_id,created_at,created_by) VALUES('other','fail-e1','e1','now','test')")
   with self.assertRaises(sqlite3.IntegrityError):s.connection.execute("UPDATE admission_validation_binding SET validation_id='pass-e2' WHERE admission_id='admit'")
   with self.assertRaises(sqlite3.IntegrityError):s.connection.execute("DELETE FROM admission_validation_binding WHERE admission_id='admit'")
 def test_existing_m3_23_store_upgrades_from_031_to_optional_binding_schema(self):
  schema=Path(self.d.name)/'schema';schema.mkdir();source=Path(__file__).parents[1]/'src'/'vera_mmu'/'schema'
  for version in range(1,32):
   migration=next(source.glob(f'{version:03d}_*.sql'));shutil.copyfile(migration,schema/migration.name)
  with self._open(schema) as legacy:self.assertEqual(legacy.metadata()['store_format'],{'schema_version':31})
  migration=next(source.glob('032_*.sql'));shutil.copyfile(migration,schema/migration.name)
  migration=next(source.glob('033_*.sql'));shutil.copyfile(migration,schema/migration.name)
  with self._open(schema) as upgraded:self.assertEqual(upgraded.metadata()['store_format'],{'schema_version':33});self.assertEqual(upgraded.connection.execute('SELECT COUNT(*) FROM admission_validation_binding').fetchone()[0],0)
if __name__=='__main__':unittest.main()

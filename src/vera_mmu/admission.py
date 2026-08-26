from __future__ import annotations
from dataclasses import dataclass
import sqlite3
from .store import MemoryStore,StoreError
class AdmissionError(StoreError): pass
@dataclass(frozen=True)
class Admission: id:str; evidence_id:str; decision:str; reason:str; created_at:str; created_by:str
class AdmissionService:
 def __init__(self,store:MemoryStore): self.store=store
 def decide(self,identifier:str,evidence_id:str,decision:str,reason:str,*,actor:str='system')->Admission:
  if not isinstance(identifier,str) or not identifier or '/' in identifier or decision not in {'ADMITTED','REJECTED'} or not isinstance(reason,str) or not reason.strip() or not isinstance(actor,str) or not actor: raise AdmissionError('Décision d’admission invalide.')
  try:
   with self.store.transaction() as c:
    row=c.execute('SELECT verdict FROM evidence WHERE id=?',(evidence_id,)).fetchone()
    if row is None: raise AdmissionError('Evidence inconnue.')
    if decision=='ADMITTED':
     if row['verdict']!='PASS': raise AdmissionError('Seule une evidence PASS est admissible.')
     policy=c.execute('SELECT mode FROM admission_policy WHERE id=1').fetchone()
     if policy is None: raise AdmissionError('Policy d’admission absente.')
     if policy['mode']=='VALIDATED_PASS_EVIDENCE' and c.execute("SELECT 1 FROM validation_result WHERE evidence_id=? AND verdict='PASS'",(evidence_id,)).fetchone() is None: raise AdmissionError('Validation PASS requise par la policy d’admission.')
    c.execute("INSERT INTO evidence_admission(id,evidence_id,decision,reason,created_at,created_by) VALUES(?,?,?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'),?)",(identifier,evidence_id,decision,reason.strip(),actor))
    result=c.execute('SELECT id,evidence_id,decision,reason,created_at,created_by FROM evidence_admission WHERE id=?',(identifier,)).fetchone()
    self.store.append_audit(c,'EVIDENCE_ADMISSION_DECIDED',{'admission_id':identifier,'evidence_id':evidence_id,'decision':decision,'actor':actor})
  except sqlite3.IntegrityError as exc: raise AdmissionError('Décision déjà présente ou invalide.') from exc
  if result is None: raise AdmissionError('Décision non lisible.')
  return Admission(*(str(result[k]) for k in ('id','evidence_id','decision','reason','created_at','created_by')))

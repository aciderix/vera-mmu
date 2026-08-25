from __future__ import annotations
from dataclasses import dataclass
import sqlite3
from .store import MemoryStore,StoreError
class GateError(StoreError): pass
@dataclass(frozen=True)
class GateEvaluation: gate_id:str; status:str
class GateService:
 def __init__(self,store:MemoryStore):self.store=store
 def add_dependency(self,dependent_id:str,prerequisite_id:str,*,actor:str='system')->None:
  if dependent_id==prerequisite_id:raise GateError('Auto-dépendance interdite.')
  try:
   with self.store.transaction() as c:
    if c.execute('SELECT 1 FROM work_item WHERE id=?',(dependent_id,)).fetchone() is None or c.execute('SELECT 1 FROM work_item WHERE id=?',(prerequisite_id,)).fetchone() is None:raise GateError('Work item inconnu.')
    rows=c.execute("WITH RECURSIVE r(id) AS (SELECT prerequisite_id FROM work_dependency WHERE dependent_id=? UNION SELECT d.prerequisite_id FROM work_dependency d JOIN r ON d.dependent_id=r.id) SELECT id FROM r",(prerequisite_id,)).fetchall()
    if dependent_id in {str(r['id']) for r in rows}:raise GateError('Cycle de dépendance interdit.')
    c.execute("INSERT INTO work_dependency(dependent_id,prerequisite_id,created_at,created_by) VALUES(?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'),?)",(dependent_id,prerequisite_id,actor));self.store.append_audit(c,'WORK_DEPENDENCY_ADDED',{'dependent_id':dependent_id,'prerequisite_id':prerequisite_id,'actor':actor})
  except sqlite3.IntegrityError as e:raise GateError('Dépendance invalide ou dupliquée.') from e
 def declare(self,identifier:str,work_item_id:str,evidence_id:str,*,actor:str='system')->None:
  try:
   with self.store.transaction() as c:
    if c.execute('SELECT 1 FROM work_item WHERE id=?',(work_item_id,)).fetchone() is None or c.execute('SELECT 1 FROM evidence WHERE id=?',(evidence_id,)).fetchone() is None:raise GateError('Endpoint de gate inconnu.')
    c.execute("INSERT INTO admission_gate(id,work_item_id,evidence_id,created_at,created_by) VALUES(?,?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'),?)",(identifier,work_item_id,evidence_id,actor));self.store.append_audit(c,'ADMISSION_GATE_DECLARED',{'gate_id':identifier,'actor':actor})
  except sqlite3.IntegrityError as e:raise GateError('Gate invalide ou dupliquée.') from e
 def evaluate(self,identifier:str)->GateEvaluation:
  row=self.store.connection.execute("SELECT g.id,a.decision FROM admission_gate g LEFT JOIN evidence_admission a ON a.evidence_id=g.evidence_id WHERE g.id=?",(identifier,)).fetchone()
  if row is None:raise GateError('Gate introuvable.')
  return GateEvaluation(str(row['id']),'PASS' if row['decision']=='ADMITTED' else 'FAIL')

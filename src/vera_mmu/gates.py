from __future__ import annotations
from dataclasses import dataclass
import sqlite3
from .store import MemoryStore, StoreError

GATE_POLICY_MODES = frozenset({"ALL", "ANY", "AT_LEAST"})


class GateError(StoreError): pass


@dataclass(frozen=True)
class GateEvaluation:
 gate_id: str; status: str; mode: str; admitted_count: int; required_count: int; minimum_admissions: int


@dataclass(frozen=True)
class GatePolicy:
 gate_id: str; mode: str; minimum_admissions: int | None; created_at: str; created_by: str


class GateService:
 def __init__(self,store: MemoryStore): self.store=store
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
 def add_requirement(self,gate_id:str,evidence_id:str,*,actor:str='system')->None:
  try:
   with self.store.transaction() as c:
    gate=c.execute('SELECT evidence_id FROM admission_gate WHERE id=?',(gate_id,)).fetchone()
    if gate is None or c.execute('SELECT 1 FROM evidence WHERE id=?',(evidence_id,)).fetchone() is None:raise GateError('Exigence de gate inconnue.')
    if c.execute('SELECT 1 FROM admission_gate_policy WHERE gate_id=?',(gate_id,)).fetchone() is not None:raise GateError('Exigences gelées après déclaration de policy.')
    if str(gate['evidence_id'])==evidence_id:raise GateError('Evidence principale déjà exigée.')
    c.execute("INSERT INTO admission_gate_requirement(gate_id,evidence_id,created_at,created_by) VALUES(?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'),?)",(gate_id,evidence_id,actor));self.store.append_audit(c,'ADMISSION_GATE_REQUIREMENT_ADDED',{'gate_id':gate_id,'evidence_id':evidence_id,'actor':actor})
  except sqlite3.IntegrityError as e:raise GateError('Exigence de gate invalide ou dupliquée.') from e
 def declare_policy(self,gate_id:str,mode:str,*,minimum_admissions:int|None=None,actor:str='system')->GatePolicy:
  if not isinstance(gate_id,str) or not gate_id or '/' in gate_id:raise GateError('Identifiant de gate invalide.')
  if mode not in GATE_POLICY_MODES:raise GateError('Mode de policy hors catalogue fermé.')
  if not isinstance(actor,str) or not actor or actor!=actor.strip() or len(actor)>256:raise GateError('Actor invalide.')
  try:
   with self.store.transaction() as c:
    requirements=self._requirements(c,gate_id)
    if not requirements:raise GateError('Gate introuvable.')
    if mode in {'ALL','ANY'} and minimum_admissions is not None:raise GateError('Seuil interdit pour ce mode.')
    if mode=='AT_LEAST' and (not isinstance(minimum_admissions,int) or isinstance(minimum_admissions,bool) or not 1<=minimum_admissions<=len(requirements)):raise GateError('Seuil AT_LEAST hors borne.')
    c.execute("INSERT INTO admission_gate_policy(gate_id,mode,minimum_admissions,created_at,created_by) VALUES(?,?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'),?)",(gate_id,mode,minimum_admissions,actor))
    row=c.execute('SELECT gate_id,mode,minimum_admissions,created_at,created_by FROM admission_gate_policy WHERE gate_id=?',(gate_id,)).fetchone()
    self.store.append_audit(c,'ADMISSION_GATE_POLICY_DECLARED',{'gate_id':gate_id,'mode':mode,'minimum_admissions':minimum_admissions,'actor':actor})
  except sqlite3.IntegrityError as e:raise GateError('Policy de gate invalide ou déjà déclarée.') from e
  if row is None:raise GateError('Policy de gate non lisible.')
  return _policy(row)
 def get_policy(self,gate_id:str)->GatePolicy:
  if not isinstance(gate_id,str) or not gate_id or '/' in gate_id:raise GateError('Identifiant de gate invalide.')
  row=self.store.connection.execute('SELECT gate_id,mode,minimum_admissions,created_at,created_by FROM admission_gate_policy WHERE gate_id=?',(gate_id,)).fetchone()
  if row is None:raise GateError('Policy de gate introuvable.')
  return _policy(row)
 def evaluate(self,identifier:str)->GateEvaluation:
  requirements=self._requirements(self.store.connection,identifier)
  if not requirements:raise GateError('Gate introuvable.')
  policy=self.store.connection.execute('SELECT mode,minimum_admissions FROM admission_gate_policy WHERE gate_id=?',(identifier,)).fetchone()
  mode='ALL' if policy is None else str(policy['mode'])
  minimum=len(requirements) if mode=='ALL' else 1 if mode=='ANY' else int(policy['minimum_admissions'])
  admitted=sum(1 for evidence_id in requirements if (row:=self.store.connection.execute("SELECT decision FROM evidence_admission WHERE evidence_id=?",(evidence_id,)).fetchone()) is not None and row['decision']=='ADMITTED')
  return GateEvaluation(identifier,'PASS' if admitted>=minimum else 'FAIL',mode,admitted,len(requirements),minimum)
 @staticmethod
 def _requirements(connection:sqlite3.Connection,gate_id:str)->list[str]:
  return [str(row['evidence_id']) for row in connection.execute("SELECT evidence_id FROM admission_gate WHERE id=? UNION ALL SELECT evidence_id FROM admission_gate_requirement WHERE gate_id=?",(gate_id,gate_id)).fetchall()]


def _policy(row:sqlite3.Row)->GatePolicy:
 return GatePolicy(str(row['gate_id']),str(row['mode']),None if row['minimum_admissions'] is None else int(row['minimum_admissions']),str(row['created_at']),str(row['created_by']))

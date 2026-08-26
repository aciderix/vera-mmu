from __future__ import annotations
from dataclasses import dataclass
from .gates import GateService
from .store import MemoryStore,StoreError
class GateBlockerError(StoreError):pass
@dataclass(frozen=True)
class GateBlocker:gate_id:str;status:str;admitted_count:int;required_count:int
class GateBlockerService:
 def __init__(self,store:MemoryStore):self.store=store
 def diagnose(self,work_item_id:str)->tuple[GateBlocker,...]:
  if not isinstance(work_item_id,str) or not work_item_id or '/' in work_item_id:raise GateBlockerError('Identifiant de work item invalide.')
  c=self.store.connection
  if c.execute('SELECT 1 FROM work_item WHERE id=?',(work_item_id,)).fetchone() is None:raise GateBlockerError('Work item inconnu.')
  gates=GateService(self.store);result=[]
  for row in c.execute('SELECT id FROM admission_gate WHERE work_item_id=? ORDER BY id',(work_item_id,)).fetchall():
   evaluation=gates.evaluate(str(row['id']))
   if evaluation.status!='PASS':result.append(GateBlocker(evaluation.gate_id,evaluation.status,evaluation.admitted_count,evaluation.required_count))
  return tuple(result)

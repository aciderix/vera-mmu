from __future__ import annotations
from dataclasses import dataclass
from .store import MemoryStore,StoreError
from .work_readiness import _work_status
class WorkBlockerError(StoreError):pass
@dataclass(frozen=True)
class WorkBlocker:kind:str;identifier:str;status:str
class WorkBlockerService:
 def __init__(self,store:MemoryStore):self.store=store
 def diagnose(self,work_item_id:str)->tuple[WorkBlocker,...]:
  if not isinstance(work_item_id,str) or not work_item_id or '/' in work_item_id:raise WorkBlockerError('Identifiant de work item invalide.')
  c=self.store.connection
  if c.execute('SELECT 1 FROM work_item WHERE id=?',(work_item_id,)).fetchone() is None:raise WorkBlockerError('Work item inconnu.')
  return tuple(WorkBlocker('PREREQUISITE',str(r['prerequisite_id']),status) for r in c.execute('SELECT prerequisite_id FROM work_dependency WHERE dependent_id=? ORDER BY prerequisite_id',(work_item_id,)).fetchall() if (status:=_work_status(c,str(r['prerequisite_id'])))!='COMPLETED')

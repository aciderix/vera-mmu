from __future__ import annotations
from dataclasses import dataclass
from .gate_blockers import GateBlocker,GateBlockerService
from .store import MemoryStore
from .work_blockers import WorkBlocker,WorkBlockerService
@dataclass(frozen=True)
class WorkBlockerReport:
 work_item_id:str;status:str;dependencies:tuple[WorkBlocker,...];gates:tuple[GateBlocker,...]
class WorkBlockerReportService:
 def __init__(self,store:MemoryStore):self.store=store
 def diagnose(self,work_item_id:str)->WorkBlockerReport:
  dependencies=WorkBlockerService(self.store).diagnose_transitive(work_item_id)
  gates=GateBlockerService(self.store).diagnose(work_item_id)
  return WorkBlockerReport(work_item_id,'BLOCKED' if dependencies or gates else 'READY',dependencies,gates)

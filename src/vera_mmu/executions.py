from __future__ import annotations
from dataclasses import dataclass
import json
from typing import Any, Mapping
from .store import MemoryStore, StoreError

class ExecutionError(StoreError): pass
@dataclass(frozen=True)
class Execution:
 id: str; capability_id: str; status: str; exit_code: int; parameters: dict[str, Any]; artifact_hash: None
class ExecutionService:
 def __init__(self, store: MemoryStore): self.store=store
 def run_noop(self, identifier: str, capability_id: str, parameters: Mapping[str, Any], *, actor: str='system')->Execution:
  if not isinstance(identifier,str) or not identifier or '/' in identifier: raise ExecutionError('Identifiant execution invalide.')
  if not isinstance(parameters,Mapping): raise ExecutionError('Paramètres objet requis.')
  if not isinstance(actor,str) or not actor: raise ExecutionError('Actor requis.')
  payload=json.dumps(dict(parameters),sort_keys=True,separators=(',',':'))
  with self.store.transaction() as c:
   row=c.execute("SELECT runner_profile,network_policy,yields_proof FROM capability_contract WHERE capability_id=?",(capability_id,)).fetchone()
   if row is None or row['runner_profile']!='NOOP' or row['network_policy']!='DENY_NETWORK' or bool(row['yields_proof']): raise ExecutionError('Contrat NOOP non admissible.')
   c.execute("INSERT INTO execution(id,capability_id,status,exit_code,parameters_json,environment_json,started_at,finished_at,result_json,created_by) VALUES(?,?, 'COMPLETED',0,?, '{}',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'),'{}',?)",(identifier,capability_id,payload,actor))
   self.store.append_audit(c,'EXECUTION_RECORDED',{'execution_id':identifier,'capability_id':capability_id,'runner_profile':'NOOP','actor':actor})
  return Execution(identifier,capability_id,'COMPLETED',0,dict(parameters),None)

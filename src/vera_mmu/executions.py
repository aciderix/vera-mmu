from __future__ import annotations
from dataclasses import dataclass
import json
import sqlite3
from typing import Any, Mapping
from .parameter_validation import ParameterValidationError, validate_parameters
from .store import MemoryStore, StoreError
from .validators import ValidatorError, record_evidence_hash_validation

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
  with self.store.transaction() as c:
   row=c.execute("SELECT contract.runner_profile,contract.network_policy,contract.yields_proof,contract.parameter_schema_json,policy.decision AS policy_decision FROM capability_contract AS contract LEFT JOIN capability_policy AS policy ON policy.capability_id=contract.capability_id WHERE contract.capability_id=?",(capability_id,)).fetchone()
   if row is None or row['runner_profile']!='NOOP' or row['network_policy']!='DENY_NETWORK' or bool(row['yields_proof']): raise ExecutionError('Contrat NOOP non admissible.')
   if row['policy_decision']!='ALLOW': raise ExecutionError('Policy ALLOW explicite requise.')
   try: validated_parameters=validate_parameters(json.loads(str(row['parameter_schema_json'])),parameters)
   except (ParameterValidationError, TypeError, ValueError) as exc: raise ExecutionError('Paramètres hors contrat fermé.') from exc
   payload=json.dumps(validated_parameters,sort_keys=True,separators=(',',':'),allow_nan=False)
   c.execute("INSERT INTO execution(id,capability_id,status,exit_code,parameters_json,environment_json,started_at,finished_at,result_json,created_by) VALUES(?,?, 'COMPLETED',0,?, '{}',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'),'{}',?)",(identifier,capability_id,payload,actor))
   self.store.append_audit(c,'EXECUTION_RECORDED',{'execution_id':identifier,'capability_id':capability_id,'runner_profile':'NOOP','actor':actor})
  return Execution(identifier,capability_id,'COMPLETED',0,validated_parameters,None)
 def run_evidence_hash(self, identifier: str, capability_id: str, parameters: Mapping[str, Any], *, validation_id: str, actor: str='system')->Execution:
  if not all(isinstance(value,str) and value and '/' not in value for value in (identifier,capability_id,validation_id,actor)): raise ExecutionError('Identifiant execution invalide.')
  if not isinstance(parameters,Mapping): raise ExecutionError('Paramètres objet requis.')
  expected_schema={'type':'object','properties':{'validator_id':{'type':'string'},'evidence_id':{'type':'string'}},'required':['validator_id','evidence_id'],'additionalProperties':False}
  try:
   with self.store.transaction() as c:
    row=c.execute("SELECT contract.runner_profile,contract.network_policy,contract.yields_proof,contract.parameter_schema_json,policy.decision AS policy_decision FROM capability_contract AS contract LEFT JOIN capability_policy AS policy ON policy.capability_id=contract.capability_id WHERE contract.capability_id=?",(capability_id,)).fetchone()
    if row is None or row['runner_profile']!='EVIDENCE_HASH' or row['network_policy']!='DENY_NETWORK' or bool(row['yields_proof']): raise ExecutionError('Contrat EVIDENCE_HASH non admissible.')
    if row['policy_decision']!='ALLOW': raise ExecutionError('Policy ALLOW explicite requise.')
    schema=json.loads(str(row['parameter_schema_json']))
    if schema!=expected_schema: raise ExecutionError('Schéma EVIDENCE_HASH hors contrat fermé.')
    try: validated_parameters=validate_parameters(schema,parameters)
    except (ParameterValidationError, TypeError, ValueError) as exc: raise ExecutionError('Paramètres hors contrat fermé.') from exc
    validator_id=validated_parameters['validator_id'];evidence_id=validated_parameters['evidence_id']
    validation=record_evidence_hash_validation(c,validation_id,validator_id,evidence_id,actor=actor)
    payload=json.dumps(validated_parameters,sort_keys=True,separators=(',',':'),allow_nan=False);result=json.dumps({'validation_id':validation_id,'verdict':validation.verdict},sort_keys=True,separators=(',',':'))
    c.execute("INSERT INTO execution(id,capability_id,status,exit_code,parameters_json,environment_json,started_at,finished_at,result_json,created_by) VALUES(?,?, 'COMPLETED',0,?, '{}',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'),?,?)",(identifier,capability_id,payload,result,actor))
    self.store.append_audit(c,'VALIDATION_RECORDED',{'validation_id':validation_id,'validator_id':validator_id,'evidence_id':evidence_id,'verdict':validation.verdict,'actor':actor,'runner_profile':'EVIDENCE_HASH'})
    self.store.append_audit(c,'EXECUTION_RECORDED',{'execution_id':identifier,'capability_id':capability_id,'runner_profile':'EVIDENCE_HASH','actor':actor})
  except ValidatorError as exc: raise ExecutionError('Validation EVIDENCE_HASH impossible.') from exc
  except sqlite3.IntegrityError as exc: raise ExecutionError('Execution ou validation invalide ou déjà présente.') from exc
  return Execution(identifier,capability_id,'COMPLETED',0,validated_parameters,None)

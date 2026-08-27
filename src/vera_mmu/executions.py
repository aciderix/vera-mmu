from __future__ import annotations
from dataclasses import dataclass
import json
import re
import sqlite3
from typing import Any, Mapping
from .addressing import AddressError, make_address
from .identity import canonical_json
from .parameter_validation import ParameterValidationError, validate_parameters
from .runner_validator_compatibility import RunnerValidatorCompatibilityError, ensure_runner_validator_compatibility
from .store import MemoryStore, StoreError
from .validators import ValidatorError, record_evidence_hash_validation, record_validation

class ExecutionError(StoreError): pass
@dataclass(frozen=True)
class Execution:
 id: str; capability_id: str; status: str; exit_code: int | None; parameters: dict[str, Any]; artifact_hash: str | None
@dataclass(frozen=True)
class ExecutionRecord:
 id: str; capability_id: str; status: str; exit_code: int | None; parameters: dict[str, Any]; environment: dict[str, Any]; started_at: str | None; finished_at: str | None; artifact_hash: str | None; result: dict[str, Any]; created_by: str; address: str

class ExecutionService:
 def __init__(self, store: MemoryStore): self.store=store
 def get(self, identifier: str) -> ExecutionRecord:
  try: make_address(self.store.identity.project_id,'execution',identifier)
  except AddressError as exc: raise ExecutionError('Identifiant execution VERA invalide.') from exc
  row=self.store.connection.execute("SELECT id,capability_id,status,exit_code,parameters_json,environment_json,started_at,finished_at,artifact_hash,result_json,created_by FROM execution WHERE id=?",(identifier,)).fetchone()
  if row is None: raise ExecutionError('Execution introuvable.')
  try:
   parameters=json.loads(str(row['parameters_json']));environment=json.loads(str(row['environment_json']));result=json.loads(str(row['result_json']))
   if not all(isinstance(value,dict) for value in (parameters,environment,result)): raise ValueError
  except (TypeError,ValueError,json.JSONDecodeError) as exc: raise ExecutionError('Execution persistée illisible ou altérée.') from exc
  return ExecutionRecord(str(row['id']),str(row['capability_id']),str(row['status']),None if row['exit_code'] is None else int(row['exit_code']),parameters,environment,None if row['started_at'] is None else str(row['started_at']),None if row['finished_at'] is None else str(row['finished_at']),None if row['artifact_hash'] is None else str(row['artifact_hash']),result,str(row['created_by']),make_address(self.store.identity.project_id,'execution',identifier))
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
 def record_observed_process(self, identifier: str, capability_id: str, parameters: Mapping[str, Any], *, environment: Mapping[str, Any], exit_code: int | None, artifact_hash: str, result: Mapping[str, Any], actor: str='system')->Execution:
  if not all(isinstance(value,str) and value and '/' not in value for value in (identifier,capability_id,actor)): raise ExecutionError('Identifiant execution invalide.')
  if not isinstance(parameters,Mapping) or not isinstance(environment,Mapping) or not isinstance(result,Mapping): raise ExecutionError('Paramètres, environnement et résultat objet requis.')
  if exit_code is not None and (isinstance(exit_code,bool) or not isinstance(exit_code,int)): raise ExecutionError('Code de sortie invalide.')
  if not isinstance(artifact_hash,str) or re.fullmatch(r'[0-9a-f]{64}',artifact_hash) is None: raise ExecutionError('Hash d’artefact SHA-256 invalide.')
  try:
   with self.store.transaction() as c:
    row=c.execute("SELECT contract.runner_profile,contract.network_policy,contract.yields_proof,contract.parameter_schema_json,policy.decision AS policy_decision FROM capability_contract AS contract LEFT JOIN capability_policy AS policy ON policy.capability_id=contract.capability_id WHERE contract.capability_id=?",(capability_id,)).fetchone()
    if row is None or row['runner_profile']!='OBSERVED_PROCESS' or row['network_policy']!='DENY_NETWORK' or bool(row['yields_proof']): raise ExecutionError('Contrat OBSERVED_PROCESS non admissible.')
    if row['policy_decision']!='ALLOW': raise ExecutionError('Policy ALLOW explicite requise.')
    schema=json.loads(str(row['parameter_schema_json']))
    try: validated_parameters=validate_parameters(schema,parameters)
    except (ParameterValidationError, TypeError, ValueError) as exc: raise ExecutionError('Paramètres hors contrat fermé.') from exc
    try:
     payload=canonical_json(validated_parameters);environment_payload=canonical_json(dict(environment));result_payload=canonical_json(dict(result))
    except (TypeError, ValueError) as exc: raise ExecutionError('Environnement ou résultat non canonique.') from exc
    c.execute("INSERT INTO execution(id,capability_id,status,exit_code,parameters_json,environment_json,started_at,finished_at,artifact_hash,result_json,created_by) VALUES(?,?, 'COMPLETED', ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'),?,?,?)",(identifier,capability_id,exit_code,payload,environment_payload,artifact_hash,result_payload,actor))
    self.store.append_audit(c,'OBSERVED_PROCESS_RECORDED',{'execution_id':identifier,'capability_id':capability_id,'artifact_hash':artifact_hash,'actor':actor})
  except sqlite3.IntegrityError as exc: raise ExecutionError('Execution observée invalide ou déjà présente.') from exc
  return Execution(identifier,capability_id,'COMPLETED',exit_code,validated_parameters,artifact_hash)
 def run_evidence_hash(self, identifier: str, capability_id: str, parameters: Mapping[str, Any], *, validation_id: str, actor: str='system')->Execution:
  if not all(isinstance(value,str) and value and '/' not in value for value in (identifier,capability_id,validation_id,actor)): raise ExecutionError('Identifiant execution invalide.')
  if not isinstance(parameters,Mapping): raise ExecutionError('Paramètres objet requis.')
  try:
   with self.store.transaction() as c:
    row=c.execute("SELECT contract.runner_profile,contract.network_policy,contract.yields_proof,contract.parameter_schema_json,policy.decision AS policy_decision FROM capability_contract AS contract LEFT JOIN capability_policy AS policy ON policy.capability_id=contract.capability_id WHERE contract.capability_id=?",(capability_id,)).fetchone()
    if row is None or row['runner_profile']!='EVIDENCE_HASH' or row['network_policy']!='DENY_NETWORK' or bool(row['yields_proof']): raise ExecutionError('Contrat EVIDENCE_HASH non admissible.')
    if row['policy_decision']!='ALLOW': raise ExecutionError('Policy ALLOW explicite requise.')
    schema=json.loads(str(row['parameter_schema_json']))
    try: validated_parameters=validate_parameters(schema,parameters)
    except (ParameterValidationError, TypeError, ValueError) as exc: raise ExecutionError('Paramètres hors contrat fermé.') from exc
    validator_id=validated_parameters['validator_id'];evidence_id=validated_parameters['evidence_id'];validator=c.execute('SELECT kind FROM validator WHERE id=?',(validator_id,)).fetchone()
    try: ensure_runner_validator_compatibility('EVIDENCE_HASH','' if validator is None else str(validator['kind']),schema)
    except RunnerValidatorCompatibilityError as exc: raise ExecutionError('Compatibilité EVIDENCE_HASH hors catalogue fermé.') from exc
    validation=record_evidence_hash_validation(c,validation_id,validator_id,evidence_id,actor=actor)
    payload=json.dumps(validated_parameters,sort_keys=True,separators=(',',':'),allow_nan=False);result=json.dumps({'validation_id':validation_id,'verdict':validation.verdict},sort_keys=True,separators=(',',':'))
    c.execute("INSERT INTO execution(id,capability_id,status,exit_code,parameters_json,environment_json,started_at,finished_at,result_json,created_by) VALUES(?,?, 'COMPLETED',0,?, '{}',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'),?,?)",(identifier,capability_id,payload,result,actor))
    self.store.append_audit(c,'VALIDATION_RECORDED',{'validation_id':validation_id,'validator_id':validator_id,'evidence_id':evidence_id,'verdict':validation.verdict,'actor':actor,'runner_profile':'EVIDENCE_HASH'})
    self.store.append_audit(c,'EXECUTION_RECORDED',{'execution_id':identifier,'capability_id':capability_id,'runner_profile':'EVIDENCE_HASH','actor':actor})
  except ValidatorError as exc: raise ExecutionError('Validation EVIDENCE_HASH impossible.') from exc
  except sqlite3.IntegrityError as exc: raise ExecutionError('Execution ou validation invalide ou déjà présente.') from exc
  return Execution(identifier,capability_id,'COMPLETED',0,validated_parameters,None)
 def run_evidence_fields(self, identifier: str, capability_id: str, parameters: Mapping[str, Any], *, validation_id: str, actor: str='system')->Execution:
  if not all(isinstance(value,str) and value and '/' not in value for value in (identifier,capability_id,validation_id,actor)): raise ExecutionError('Identifiant execution invalide.')
  if not isinstance(parameters,Mapping): raise ExecutionError('Paramètres objet requis.')
  try:
   with self.store.transaction() as c:
    row=c.execute("SELECT contract.runner_profile,contract.network_policy,contract.yields_proof,contract.parameter_schema_json,policy.decision AS policy_decision FROM capability_contract AS contract LEFT JOIN capability_policy AS policy ON policy.capability_id=contract.capability_id WHERE contract.capability_id=?",(capability_id,)).fetchone()
    if row is None or row['runner_profile']!='EVIDENCE_FIELDS' or row['network_policy']!='DENY_NETWORK' or bool(row['yields_proof']): raise ExecutionError('Contrat EVIDENCE_FIELDS non admissible.')
    if row['policy_decision']!='ALLOW': raise ExecutionError('Policy ALLOW explicite requise.')
    schema=json.loads(str(row['parameter_schema_json']))
    try: validated_parameters=validate_parameters(schema,parameters)
    except (ParameterValidationError, TypeError, ValueError) as exc: raise ExecutionError('Paramètres hors contrat fermé.') from exc
    validator_id=validated_parameters['validator_id'];evidence_id=validated_parameters['evidence_id'];validator=c.execute('SELECT kind FROM validator WHERE id=?',(validator_id,)).fetchone()
    try: ensure_runner_validator_compatibility('EVIDENCE_FIELDS','' if validator is None else str(validator['kind']),schema)
    except RunnerValidatorCompatibilityError as exc: raise ExecutionError('Compatibilité EVIDENCE_FIELDS hors catalogue fermé.') from exc
    validation=record_validation(c,validation_id,validator_id,evidence_id,actor=actor,required_kind='EVIDENCE_FIELDS')
    payload=json.dumps(validated_parameters,sort_keys=True,separators=(',',':'),allow_nan=False);result=json.dumps({'validation_id':validation_id,'verdict':validation.verdict},sort_keys=True,separators=(',',':'))
    c.execute("INSERT INTO execution(id,capability_id,status,exit_code,parameters_json,environment_json,started_at,finished_at,result_json,created_by) VALUES(?,?, 'COMPLETED',0,?, '{}',strftime('%Y-%m-%dT%H:%M:%fZ','now'),strftime('%Y-%m-%dT%H:%M:%fZ','now'),?,?)",(identifier,capability_id,payload,result,actor))
    self.store.append_audit(c,'VALIDATION_RECORDED',{'validation_id':validation_id,'validator_id':validator_id,'evidence_id':evidence_id,'verdict':validation.verdict,'actor':actor,'runner_profile':'EVIDENCE_FIELDS'});self.store.append_audit(c,'EXECUTION_RECORDED',{'execution_id':identifier,'capability_id':capability_id,'runner_profile':'EVIDENCE_FIELDS','actor':actor})
  except ValidatorError as exc: raise ExecutionError('Validation EVIDENCE_FIELDS impossible.') from exc
  except sqlite3.IntegrityError as exc: raise ExecutionError('Execution ou validation invalide ou déjà présente.') from exc
  return Execution(identifier,capability_id,'COMPLETED',0,validated_parameters,None)

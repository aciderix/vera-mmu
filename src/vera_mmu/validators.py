from __future__ import annotations
from dataclasses import dataclass
import hashlib,json,re,sqlite3
from .identity import canonical_json
from .store import MemoryStore,StoreError
VALIDATOR_KINDS=frozenset({'EVIDENCE_HASH','EVIDENCE_FIELDS','EVIDENCE_ASSET'})
class ValidatorError(StoreError):pass
@dataclass(frozen=True)
class Validator:id:str;kind:str;required_keys:tuple[str,...];created_at:str;created_by:str
@dataclass(frozen=True)
class ValidationResult:id:str;validator_id:str;evidence_id:str;verdict:str;expected_hash:str;observed_hash:str|None;created_at:str;created_by:str
class ValidatorService:
 def __init__(self,store:MemoryStore):self.store=store
 def register(self,identifier:str,kind:str,*,required_keys:tuple[str,...]|None=None,actor:str='system')->Validator:
  if not isinstance(identifier,str) or not identifier or '/' in identifier or kind not in VALIDATOR_KINDS:raise ValidatorError('Validator invalide ou hors catalogue fermé.')
  if not isinstance(actor,str) or not actor or actor!=actor.strip() or len(actor)>256:raise ValidatorError('Actor invalide.')
  rule=_rule(kind,required_keys)
  try:
   with self.store.transaction() as c:
    c.execute("INSERT INTO validator(id,kind,rule_json,created_at,created_by) VALUES(?,?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'),?)",(identifier,kind,canonical_json(rule),actor));row=c.execute('SELECT id,kind,rule_json,created_at,created_by FROM validator WHERE id=?',(identifier,)).fetchone();self.store.append_audit(c,'VALIDATOR_REGISTERED',{'validator_id':identifier,'kind':kind,'actor':actor})
  except sqlite3.IntegrityError as e:raise ValidatorError('Validator invalide ou déjà enregistré.') from e
  if row is None:raise ValidatorError('Validator non lisible.')
  return _validator(row)
 def get(self,identifier:str)->Validator:
  if not isinstance(identifier,str) or not identifier or '/' in identifier:raise ValidatorError('Identifiant de validator invalide.')
  row=self.store.connection.execute('SELECT id,kind,rule_json,created_at,created_by FROM validator WHERE id=?',(identifier,)).fetchone()
  if row is None:raise ValidatorError('Validator introuvable.')
  return _validator(row)
 def get_result(self,identifier:str)->ValidationResult:
  row=self.store.connection.execute('SELECT id,validator_id,evidence_id,verdict,expected_hash,observed_hash,created_at,created_by FROM validation_result WHERE id=?',(identifier,)).fetchone()
  if row is None:raise ValidatorError('Résultat de validation introuvable.')
  return _result(row)
 def validate(self,identifier:str,validator_id:str,evidence_id:str,*,actor:str='system')->ValidationResult:
  if not all(isinstance(v,str) and v and '/' not in v for v in(identifier,validator_id,evidence_id,actor)):raise ValidatorError('Identifiant de validation invalide.')
  try:
   with self.store.transaction() as c:
    result=record_validation(c,identifier,validator_id,evidence_id,actor=actor);self.store.append_audit(c,'VALIDATION_RECORDED',{'validation_id':identifier,'validator_id':validator_id,'evidence_id':evidence_id,'verdict':result.verdict,'actor':actor})
  except sqlite3.IntegrityError as e:raise ValidatorError('Résultat de validation invalide ou déjà présent.') from e
  return result
def record_evidence_hash_validation(c:sqlite3.Connection,identifier:str,validator_id:str,evidence_id:str,*,actor:str)->ValidationResult:
 return record_validation(c,identifier,validator_id,evidence_id,actor=actor,required_kind='EVIDENCE_HASH')
def record_validation(c:sqlite3.Connection,identifier:str,validator_id:str,evidence_id:str,*,actor:str,required_kind:str|None=None)->ValidationResult:
 v=c.execute('SELECT kind,rule_json FROM validator WHERE id=?',(validator_id,)).fetchone();e=c.execute('SELECT execution_id,content_json,content_hash FROM evidence WHERE id=?',(evidence_id,)).fetchone()
 if v is None or e is None or(required_kind is not None and v['kind']!=required_kind):raise ValidatorError('Validator ou evidence introuvable.')
 content=_content(str(e['content_json']));kind=str(v['kind'])
 if kind=='EVIDENCE_HASH':expected=str(e['content_hash']);observed=_hash(content);verdict='PASS' if observed==expected else 'FAIL'
 elif kind=='EVIDENCE_FIELDS':
  rule=_decode_rule(str(v['rule_json']));expected=_hash(rule);observed=_hash(content);verdict='PASS' if all(k in content for k in rule['required_keys']) else 'FAIL'
 elif kind=='EVIDENCE_ASSET':
  asset_id=content.get('asset_id');declared_hash=content.get('asset_hash');expected=declared_hash if isinstance(declared_hash,str) and re.fullmatch(r'[0-9a-f]{64}',declared_hash) else str(e['content_hash']);asset=c.execute('SELECT content_hash FROM asset WHERE id=?',(asset_id,)).fetchone() if isinstance(asset_id,str) and asset_id else None;execution=c.execute('SELECT artifact_hash FROM execution WHERE id=?',(e['execution_id'],)).fetchone();observed=None if asset is None else str(asset['content_hash']);verdict='PASS' if asset is not None and execution is not None and observed==expected and execution['artifact_hash']==expected else 'FAIL'
 else:raise ValidatorError('Type de validator hors catalogue fermé.')
 c.execute("INSERT INTO validation_result(id,validator_id,evidence_id,verdict,expected_hash,observed_hash,created_at,created_by) VALUES(?,?,?,?,?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'),?)",(identifier,validator_id,evidence_id,verdict,expected,observed,actor));row=c.execute('SELECT id,validator_id,evidence_id,verdict,expected_hash,observed_hash,created_at,created_by FROM validation_result WHERE id=?',(identifier,)).fetchone()
 if row is None:raise ValidatorError('Résultat de validation non lisible.')
 return _result(row)
def _rule(kind:str,keys:tuple[str,...]|None)->dict[str,object]:
 if kind in {'EVIDENCE_HASH','EVIDENCE_ASSET'}:
  if keys is not None:raise ValidatorError('Règle interdite pour ce validator.')
  return {}
 if not isinstance(keys,tuple) or not keys or len(keys)>32 or len(set(keys))!=len(keys) or any(not isinstance(k,str) or not k or '/' in k or len(k)>128 for k in keys):raise ValidatorError('Clés requises invalides.')
 return {'required_keys':list(keys)}
def _decode_rule(text:str)->dict[str,object]:
 try:
  value=json.loads(text);keys=value['required_keys']
  if not isinstance(keys,list) or not keys or any(not isinstance(k,str) for k in keys):raise ValueError
  return {'required_keys':keys}
 except (TypeError,ValueError,KeyError,json.JSONDecodeError) as e:raise ValidatorError('Règle de validator invalide.') from e
def _content(text:str)->dict[str,object]:
 try:
  value=json.loads(text)
  if not isinstance(value,dict):raise ValueError
  return value
 except (TypeError,ValueError,json.JSONDecodeError) as e:raise ValidatorError('Contenu d’evidence non canonique.') from e
def _hash(value:object)->str:return hashlib.sha256(canonical_json(value).encode()).hexdigest()
def _validator(r:sqlite3.Row)->Validator:
 rule={} if str(r['kind']) in {'EVIDENCE_HASH','EVIDENCE_ASSET'} else _decode_rule(str(r['rule_json']));return Validator(str(r['id']),str(r['kind']),tuple(rule.get('required_keys',[])),str(r['created_at']),str(r['created_by']))
def _result(r:sqlite3.Row)->ValidationResult:return ValidationResult(str(r['id']),str(r['validator_id']),str(r['evidence_id']),str(r['verdict']),str(r['expected_hash']),None if r['observed_hash'] is None else str(r['observed_hash']),str(r['created_at']),str(r['created_by']))

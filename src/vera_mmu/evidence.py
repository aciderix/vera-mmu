from __future__ import annotations
from dataclasses import dataclass
import hashlib,json,sqlite3
from typing import Any,Mapping
from .identity import canonical_json
from .store import MemoryStore,StoreError
TYPES=frozenset({'COMMAND_PROOF','TEST_PROOF','CI_PROOF','API_PROOF','HASH_PROOF','METRIC_PROOF','FILE_PROOF','EXTERNAL_ATTESTATION','HUMAN_ASSERTION','MODEL_EVALUATION'})
VERDICTS=frozenset({'PASS','FAIL','ERROR','SKIPPED','UNKNOWN'})
class EvidenceError(StoreError): pass
@dataclass(frozen=True)
class Evidence:
 id:str; execution_id:str; evidence_type:str; verdict:str; content:dict[str,Any]; content_hash:str; admission_status:str; created_at:str; created_by:str
class EvidenceService:
 def __init__(self,store:MemoryStore): self.store=store
 def record(self,identifier:str,execution_id:str,evidence_type:str,verdict:str,content:Mapping[str,Any],*,actor:str='system')->Evidence:
  if not isinstance(identifier,str) or not identifier or '/' in identifier: raise EvidenceError('Identifiant evidence invalide.')
  if evidence_type not in TYPES or verdict not in VERDICTS: raise EvidenceError('Type ou verdict evidence invalide.')
  if not isinstance(content,Mapping) or not isinstance(actor,str) or not actor: raise EvidenceError('Contenu ou actor invalide.')
  payload=canonical_json(dict(content)); digest=hashlib.sha256(payload.encode()).hexdigest()
  try:
   with self.store.transaction() as c:
    if c.execute('SELECT 1 FROM execution WHERE id=?',(execution_id,)).fetchone() is None: raise EvidenceError('Execution inconnue.')
    c.execute("INSERT INTO evidence(id,execution_id,evidence_type,verdict,content_json,content_hash,created_at,created_by) VALUES(?,?,?,?,?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'),?)",(identifier,execution_id,evidence_type,verdict,payload,digest,actor))
    row=c.execute('SELECT id,execution_id,evidence_type,verdict,content_json,content_hash,admission_status,created_at,created_by FROM evidence WHERE id=?',(identifier,)).fetchone()
    self.store.append_audit(c,'EVIDENCE_RECORDED',{'evidence_id':identifier,'execution_id':execution_id,'verdict':verdict,'actor':actor})
  except sqlite3.IntegrityError as exc: raise EvidenceError('Evidence invalide ou dupliquée.') from exc
  if row is None: raise EvidenceError('Evidence non lisible.')
  return _row(row)
 def get(self,identifier:str)->Evidence:
  row=self.store.connection.execute('SELECT id,execution_id,evidence_type,verdict,content_json,content_hash,admission_status,created_at,created_by FROM evidence WHERE id=?',(identifier,)).fetchone()
  if row is None: raise EvidenceError('Evidence introuvable.')
  return _row(row)
def _row(row:sqlite3.Row)->Evidence:
 content=json.loads(str(row['content_json']))
 if not isinstance(content,dict): raise EvidenceError('Evidence illisible.')
 return Evidence(str(row['id']),str(row['execution_id']),str(row['evidence_type']),str(row['verdict']),content,str(row['content_hash']),str(row['admission_status']),str(row['created_at']),str(row['created_by']))

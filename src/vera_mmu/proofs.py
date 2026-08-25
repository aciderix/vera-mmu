from __future__ import annotations
from dataclasses import dataclass
import hashlib,hmac,sqlite3
from .store import MemoryStore,StoreError
class ProofError(StoreError): pass
@dataclass(frozen=True)
class KnowledgeProof:
 id:str; knowledge_id:str; evidence_id:str; admission_id:str; status:str; hmac_required:bool; hmac_digest:str|None; created_at:str; created_by:str
class ProofService:
 def __init__(self,store:MemoryStore,*,hmac_secret:bytes|None=None): self.store=store;self.hmac_secret=hmac_secret
 def promote(self,identifier:str,knowledge_id:str,evidence_id:str,admission_id:str,*,actor:str='system')->KnowledgeProof:
  if not all(isinstance(v,str) and v and '/' not in v for v in (identifier,knowledge_id,evidence_id,admission_id,actor)): raise ProofError('Identifiant de preuve invalide.')
  try:
   with self.store.transaction() as c:
    policy=c.execute('SELECT algorithm,hmac_required FROM proof_policy WHERE singleton=1').fetchone()
    if policy is None or policy['algorithm']!='HMAC_SHA256': raise ProofError('Policy de preuve explicite requise.')
    hmac_required=bool(policy['hmac_required'])
    if hmac_required and (not isinstance(self.hmac_secret,bytes) or not self.hmac_secret): raise ProofError('Secret HMAC requis pour cette policy.')
    if not hmac_required and self.hmac_secret is not None: raise ProofError('Secret HMAC interdit lorsque la policy ne le requiert pas.')
    digest=None if not hmac_required else hmac.new(self.hmac_secret,f'{knowledge_id}:{evidence_id}:{admission_id}'.encode(),hashlib.sha256).hexdigest()
    if c.execute('SELECT 1 FROM knowledge WHERE id=?',(knowledge_id,)).fetchone() is None: raise ProofError('Knowledge inconnue.')
    evidence=c.execute('SELECT verdict FROM evidence WHERE id=?',(evidence_id,)).fetchone()
    admission=c.execute('SELECT evidence_id,decision FROM evidence_admission WHERE id=?',(admission_id,)).fetchone()
    if evidence is None or evidence['verdict']!='PASS' or admission is None or admission['evidence_id']!=evidence_id or admission['decision']!='ADMITTED': raise ProofError('Evidence non admissible pour promotion.')
    c.execute("INSERT INTO knowledge_proof(id,knowledge_id,evidence_id,admission_id,status,hmac_required,hmac_digest,created_at,created_by) VALUES(?,?,?,?, 'PROVEN',?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'),?)",(identifier,knowledge_id,evidence_id,admission_id,int(hmac_required),digest,actor))
    row=c.execute('SELECT id,knowledge_id,evidence_id,admission_id,status,hmac_required,hmac_digest,created_at,created_by FROM knowledge_proof WHERE id=?',(identifier,)).fetchone()
    self.store.append_audit(c,'KNOWLEDGE_PROOF_PROMOTED',{'proof_id':identifier,'knowledge_id':knowledge_id,'evidence_id':evidence_id,'actor':actor})
  except sqlite3.IntegrityError as exc: raise ProofError('Preuve dérivée invalide ou dupliquée.') from exc
  if row is None: raise ProofError('Preuve non lisible.')
  return KnowledgeProof(str(row['id']),str(row['knowledge_id']),str(row['evidence_id']),str(row['admission_id']),str(row['status']),bool(row['hmac_required']),None if row['hmac_digest'] is None else str(row['hmac_digest']),str(row['created_at']),str(row['created_by']))

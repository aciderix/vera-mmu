CREATE TABLE IF NOT EXISTS knowledge_proof (
 id TEXT PRIMARY KEY CHECK(length(id) BETWEEN 1 AND 256),
 knowledge_id TEXT NOT NULL REFERENCES knowledge(id) ON DELETE RESTRICT,
 evidence_id TEXT NOT NULL REFERENCES evidence(id) ON DELETE RESTRICT,
 admission_id TEXT NOT NULL REFERENCES evidence_admission(id) ON DELETE RESTRICT,
 status TEXT NOT NULL CHECK(status='PROVEN'),
 hmac_required INTEGER NOT NULL DEFAULT 0 CHECK(hmac_required IN (0,1)),
 hmac_digest TEXT CHECK(hmac_digest IS NULL OR length(hmac_digest)=64),
 created_at TEXT NOT NULL,
 created_by TEXT NOT NULL CHECK(length(created_by) BETWEEN 1 AND 256),
 UNIQUE(knowledge_id,evidence_id)
) STRICT;
CREATE TRIGGER IF NOT EXISTS knowledge_proof_no_update BEFORE UPDATE ON knowledge_proof BEGIN SELECT RAISE(ABORT,'knowledge proofs are append-only'); END;
CREATE TRIGGER IF NOT EXISTS knowledge_proof_no_delete BEFORE DELETE ON knowledge_proof BEGIN SELECT RAISE(ABORT,'knowledge proofs are append-only'); END;

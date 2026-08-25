CREATE TABLE IF NOT EXISTS evidence (
 id TEXT PRIMARY KEY CHECK(length(id) BETWEEN 1 AND 256),
 execution_id TEXT NOT NULL REFERENCES execution(id) ON DELETE RESTRICT,
 evidence_type TEXT NOT NULL CHECK(evidence_type IN ('COMMAND_PROOF','TEST_PROOF','CI_PROOF','API_PROOF','HASH_PROOF','METRIC_PROOF','FILE_PROOF','EXTERNAL_ATTESTATION','HUMAN_ASSERTION','MODEL_EVALUATION')),
 verdict TEXT NOT NULL CHECK(verdict IN ('PASS','FAIL','ERROR','SKIPPED','UNKNOWN')),
 content_json TEXT NOT NULL CHECK(json_valid(content_json)),
 content_hash TEXT NOT NULL CHECK(length(content_hash)=64),
 admission_status TEXT NOT NULL DEFAULT 'PENDING' CHECK(admission_status='PENDING'),
 created_at TEXT NOT NULL,
 created_by TEXT NOT NULL CHECK(length(created_by) BETWEEN 1 AND 256)
) STRICT;
CREATE TRIGGER IF NOT EXISTS evidence_no_update BEFORE UPDATE ON evidence BEGIN SELECT RAISE(ABORT,'evidence records are append-only'); END;
CREATE TRIGGER IF NOT EXISTS evidence_no_delete BEFORE DELETE ON evidence BEGIN SELECT RAISE(ABORT,'evidence records are append-only'); END;

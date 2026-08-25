CREATE TABLE IF NOT EXISTS evidence_admission (
 id TEXT PRIMARY KEY CHECK(length(id) BETWEEN 1 AND 256),
 evidence_id TEXT NOT NULL UNIQUE REFERENCES evidence(id) ON DELETE RESTRICT,
 decision TEXT NOT NULL CHECK(decision IN ('ADMITTED','REJECTED')),
 reason TEXT NOT NULL CHECK(length(reason) BETWEEN 1 AND 1024),
 created_at TEXT NOT NULL,
 created_by TEXT NOT NULL CHECK(length(created_by) BETWEEN 1 AND 256)
) STRICT;
CREATE TRIGGER IF NOT EXISTS evidence_admission_no_update BEFORE UPDATE ON evidence_admission BEGIN SELECT RAISE(ABORT,'admission records are append-only'); END;
CREATE TRIGGER IF NOT EXISTS evidence_admission_no_delete BEFORE DELETE ON evidence_admission BEGIN SELECT RAISE(ABORT,'admission records are append-only'); END;

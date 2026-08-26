CREATE TABLE IF NOT EXISTS admission_policy (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    mode TEXT NOT NULL CHECK (mode IN ('PASS_EVIDENCE', 'VALIDATED_PASS_EVIDENCE')),
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256)
) STRICT;
CREATE TRIGGER IF NOT EXISTS admission_policy_no_update BEFORE UPDATE ON admission_policy BEGIN SELECT RAISE(ABORT, 'admission policy is append-only'); END;
CREATE TRIGGER IF NOT EXISTS admission_policy_no_delete BEFORE DELETE ON admission_policy BEGIN SELECT RAISE(ABORT, 'admission policy is append-only'); END;

CREATE TABLE IF NOT EXISTS capability_policy (
    capability_id TEXT PRIMARY KEY REFERENCES capability(id) ON DELETE RESTRICT,
    decision TEXT NOT NULL CHECK (decision IN ('ALLOW', 'DENY', 'CONFIRM')),
    reason TEXT NOT NULL CHECK (length(reason) BETWEEN 1 AND 4096),
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256)
) STRICT;
CREATE TRIGGER IF NOT EXISTS capability_policy_no_update BEFORE UPDATE ON capability_policy BEGIN SELECT RAISE(ABORT, 'capability policies are append-only'); END;
CREATE TRIGGER IF NOT EXISTS capability_policy_no_delete BEFORE DELETE ON capability_policy BEGIN SELECT RAISE(ABORT, 'capability policies are append-only'); END;

CREATE TABLE IF NOT EXISTS work_start_policy (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    mode TEXT NOT NULL CHECK (mode IN ('OPEN', 'REQUIRE_READY')),
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256)
) STRICT;
CREATE TRIGGER IF NOT EXISTS work_start_policy_no_update BEFORE UPDATE ON work_start_policy BEGIN SELECT RAISE(ABORT, 'work start policy is append-only'); END;
CREATE TRIGGER IF NOT EXISTS work_start_policy_no_delete BEFORE DELETE ON work_start_policy BEGIN SELECT RAISE(ABORT, 'work start policy is append-only'); END;

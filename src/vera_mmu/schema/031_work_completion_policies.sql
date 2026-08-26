CREATE TABLE work_completion_policy (
 id INTEGER PRIMARY KEY CHECK(id=1),
 mode TEXT NOT NULL CHECK(mode IN ('OPEN','REQUIRE_READY_FOR_COMPLETE')),
 created_at TEXT NOT NULL,
 created_by TEXT NOT NULL CHECK(length(created_by) BETWEEN 1 AND 256)
) STRICT;
CREATE TRIGGER work_completion_policy_no_update BEFORE UPDATE ON work_completion_policy BEGIN SELECT RAISE(ABORT,'work completion policy is append-only'); END;
CREATE TRIGGER work_completion_policy_no_delete BEFORE DELETE ON work_completion_policy BEGIN SELECT RAISE(ABORT,'work completion policy is append-only'); END;

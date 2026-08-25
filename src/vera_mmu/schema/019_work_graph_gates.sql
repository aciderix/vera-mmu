CREATE TABLE IF NOT EXISTS work_dependency (
 dependent_id TEXT NOT NULL REFERENCES work_item(id) ON DELETE RESTRICT,
 prerequisite_id TEXT NOT NULL REFERENCES work_item(id) ON DELETE RESTRICT,
 created_at TEXT NOT NULL,
 created_by TEXT NOT NULL CHECK(length(created_by) BETWEEN 1 AND 256),
 PRIMARY KEY(dependent_id,prerequisite_id),
 CHECK(dependent_id != prerequisite_id)
) STRICT;
CREATE TRIGGER IF NOT EXISTS work_dependency_no_update BEFORE UPDATE ON work_dependency BEGIN SELECT RAISE(ABORT,'work dependencies are append-only'); END;
CREATE TRIGGER IF NOT EXISTS work_dependency_no_delete BEFORE DELETE ON work_dependency BEGIN SELECT RAISE(ABORT,'work dependencies are append-only'); END;
CREATE TABLE IF NOT EXISTS admission_gate (
 id TEXT PRIMARY KEY CHECK(length(id) BETWEEN 1 AND 256),
 work_item_id TEXT NOT NULL REFERENCES work_item(id) ON DELETE RESTRICT,
 evidence_id TEXT NOT NULL REFERENCES evidence(id) ON DELETE RESTRICT,
 created_at TEXT NOT NULL,
 created_by TEXT NOT NULL CHECK(length(created_by) BETWEEN 1 AND 256),
 UNIQUE(work_item_id,evidence_id)
) STRICT;
CREATE TRIGGER IF NOT EXISTS admission_gate_no_update BEFORE UPDATE ON admission_gate BEGIN SELECT RAISE(ABORT,'gates are append-only'); END;
CREATE TRIGGER IF NOT EXISTS admission_gate_no_delete BEFORE DELETE ON admission_gate BEGIN SELECT RAISE(ABORT,'gates are append-only'); END;

CREATE TABLE IF NOT EXISTS capability (
    id TEXT PRIMARY KEY CHECK (length(id) BETWEEN 1 AND 256),
    name TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 256),
    description TEXT NOT NULL DEFAULT '' CHECK (length(description) <= 4096),
    kind TEXT NOT NULL CHECK (kind IN ('ACTION', 'CHECK', 'ORACLE', 'COLLECTOR', 'GENERATOR', 'QUERY')),
    version TEXT NOT NULL CHECK (length(version) BETWEEN 1 AND 64),
    input_schema_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(input_schema_json)),
    parameter_schema_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(parameter_schema_json)),
    output_schema_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(output_schema_json)),
    metadata_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(metadata_json)),
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256),
    UNIQUE(name, version)
) STRICT;

CREATE TRIGGER IF NOT EXISTS capability_no_update
BEFORE UPDATE ON capability
BEGIN
    SELECT RAISE(ABORT, 'capability records are append-only');
END;

CREATE TRIGGER IF NOT EXISTS capability_no_delete
BEFORE DELETE ON capability
BEGIN
    SELECT RAISE(ABORT, 'capability records are append-only');
END;

CREATE TABLE IF NOT EXISTS execution (
    id TEXT PRIMARY KEY CHECK (length(id) BETWEEN 1 AND 256),
    capability_id TEXT NOT NULL REFERENCES capability(id) ON DELETE RESTRICT,
    status TEXT NOT NULL CHECK (length(status) BETWEEN 1 AND 64),
    exit_code INTEGER,
    parameters_json TEXT NOT NULL CHECK (json_valid(parameters_json)),
    environment_json TEXT NOT NULL CHECK (json_valid(environment_json)),
    started_at TEXT,
    finished_at TEXT,
    artifact_hash TEXT CHECK (artifact_hash IS NULL OR length(artifact_hash) = 64),
    result_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(result_json)),
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256)
) STRICT;

CREATE TRIGGER IF NOT EXISTS execution_no_update
BEFORE UPDATE ON execution
BEGIN
    SELECT RAISE(ABORT, 'execution records are append-only');
END;

CREATE TRIGGER IF NOT EXISTS execution_no_delete
BEFORE DELETE ON execution
BEGIN
    SELECT RAISE(ABORT, 'execution records are append-only');
END;

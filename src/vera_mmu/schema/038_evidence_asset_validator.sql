PRAGMA foreign_keys=OFF;
DROP TRIGGER IF EXISTS admission_validation_binding_admission_integrity;
DROP TRIGGER IF EXISTS admission_validation_binding_validation_integrity;
DROP TRIGGER IF EXISTS admission_validation_binding_no_update;
DROP TRIGGER IF EXISTS admission_validation_binding_no_delete;
ALTER TABLE admission_validation_binding RENAME TO admission_validation_binding_legacy;
DROP TRIGGER IF EXISTS validator_no_update;
DROP TRIGGER IF EXISTS validator_no_delete;
DROP TRIGGER IF EXISTS validation_result_no_update;
DROP TRIGGER IF EXISTS validation_result_no_delete;
ALTER TABLE validation_result RENAME TO validation_result_legacy;
ALTER TABLE validator RENAME TO validator_legacy;
CREATE TABLE validator (
    id TEXT PRIMARY KEY CHECK (length(id) BETWEEN 1 AND 256),
    kind TEXT NOT NULL UNIQUE CHECK (kind IN ('EVIDENCE_HASH', 'EVIDENCE_FIELDS', 'EVIDENCE_ASSET')),
    rule_json TEXT NOT NULL CHECK (json_valid(rule_json)),
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256)
) STRICT;
CREATE TABLE validation_result (
    id TEXT PRIMARY KEY CHECK (length(id) BETWEEN 1 AND 256),
    validator_id TEXT NOT NULL REFERENCES validator(id) ON DELETE RESTRICT,
    evidence_id TEXT NOT NULL REFERENCES evidence(id) ON DELETE RESTRICT,
    verdict TEXT NOT NULL CHECK (verdict IN ('PASS', 'FAIL')),
    expected_hash TEXT NOT NULL CHECK (length(expected_hash) = 64),
    observed_hash TEXT CHECK (observed_hash IS NULL OR length(observed_hash) = 64),
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK (length(created_by) BETWEEN 1 AND 256),
    UNIQUE (validator_id, evidence_id)
) STRICT;
INSERT INTO validator(id, kind, rule_json, created_at, created_by)
SELECT id, kind, rule_json, created_at, created_by FROM validator_legacy;
INSERT INTO validation_result(id, validator_id, evidence_id, verdict, expected_hash, observed_hash, created_at, created_by)
SELECT id, validator_id, evidence_id, verdict, expected_hash, observed_hash, created_at, created_by FROM validation_result_legacy;
CREATE TABLE admission_validation_binding (
    admission_id TEXT PRIMARY KEY REFERENCES evidence_admission(id) ON DELETE RESTRICT,
    validation_id TEXT NOT NULL UNIQUE REFERENCES validation_result(id) ON DELETE RESTRICT,
    evidence_id TEXT NOT NULL REFERENCES evidence(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK(length(created_by) BETWEEN 1 AND 256)
) STRICT;
INSERT INTO admission_validation_binding(admission_id, validation_id, evidence_id, created_at, created_by)
SELECT admission_id, validation_id, evidence_id, created_at, created_by FROM admission_validation_binding_legacy;
DROP TABLE admission_validation_binding_legacy;
DROP TABLE validation_result_legacy;
DROP TABLE validator_legacy;
CREATE TRIGGER validator_no_update BEFORE UPDATE ON validator BEGIN SELECT RAISE(ABORT, 'validators are append-only'); END;
CREATE TRIGGER validator_no_delete BEFORE DELETE ON validator BEGIN SELECT RAISE(ABORT, 'validators are append-only'); END;
CREATE TRIGGER validation_result_no_update BEFORE UPDATE ON validation_result BEGIN SELECT RAISE(ABORT, 'validation results are append-only'); END;
CREATE TRIGGER validation_result_no_delete BEFORE DELETE ON validation_result BEGIN SELECT RAISE(ABORT, 'validation results are append-only'); END;
CREATE TRIGGER admission_validation_binding_admission_integrity BEFORE INSERT ON admission_validation_binding BEGIN
    SELECT CASE WHEN (SELECT decision FROM evidence_admission WHERE id = NEW.admission_id) != 'ADMITTED'
        OR (SELECT evidence_id FROM evidence_admission WHERE id = NEW.admission_id) != NEW.evidence_id
        THEN RAISE(ABORT, 'admission validation binding requires admitted same evidence') END;
END;
CREATE TRIGGER admission_validation_binding_validation_integrity BEFORE INSERT ON admission_validation_binding BEGIN
    SELECT CASE WHEN (SELECT verdict FROM validation_result WHERE id = NEW.validation_id) != 'PASS'
        OR (SELECT evidence_id FROM validation_result WHERE id = NEW.validation_id) != NEW.evidence_id
        THEN RAISE(ABORT, 'admission validation binding requires pass same evidence') END;
END;
CREATE TRIGGER admission_validation_binding_no_update BEFORE UPDATE ON admission_validation_binding BEGIN SELECT RAISE(ABORT,'admission validation bindings are append-only'); END;
CREATE TRIGGER admission_validation_binding_no_delete BEFORE DELETE ON admission_validation_binding BEGIN SELECT RAISE(ABORT,'admission validation bindings are append-only'); END;
PRAGMA foreign_keys=ON;

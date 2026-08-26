CREATE TABLE admission_validation_binding (
    admission_id TEXT PRIMARY KEY REFERENCES evidence_admission(id) ON DELETE RESTRICT,
    validation_id TEXT NOT NULL UNIQUE REFERENCES validation_result(id) ON DELETE RESTRICT,
    evidence_id TEXT NOT NULL REFERENCES evidence(id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL CHECK(length(created_by) BETWEEN 1 AND 256)
) STRICT;
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

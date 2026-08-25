CREATE INDEX IF NOT EXISTS idx_knowledge_source_hash_knowledge
ON knowledge_source(source_hash, knowledge_id, id);

CREATE INDEX IF NOT EXISTS idx_knowledge_asset_link_asset_knowledge
ON knowledge_asset_link(asset_id, knowledge_id);

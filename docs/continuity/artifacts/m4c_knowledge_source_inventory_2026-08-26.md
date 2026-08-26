# Inventaire source ARET V1 — cadrage M4-C knowledge

> **Nature :** observation SQLite strictement en lecture seule depuis `/home/ubuntu/ARET-MMU/aret-memory/.aret-memory/aret_memory.sqlite`, snapshot attesté `85bdf19a5683591a8e3d42571bd4f28285a72f1a96627f392aa0dd0bfdb01cf5`, commit ARET `7f7b4df6d4f3bb493dfa26868fcec5f5b95a7ac4`.
>
> **Limite :** cet inventaire ne constitue pas une migration, une preuve admissible ni un verdict de compatibilité.

| Table candidate | Cardinalité observée | Colonnes pertinentes |
|---|---:|---|
| `knowledge` | 532 | `id`, `type`, `status`, `title`, `content`, `component_id`, `function_id`, `brick_id`, `supersedes_id`, `version`, `content_hash`, `created_at`, `updated_at`, `created_by`, `effective_at` |
| `knowledge_source` | 517 | `id`, `knowledge_id`, `source_repository`, `source_revision`, `source_path`, `source_start_line`, `source_end_line`, `source_section`, `source_hash`, `imported_at`, `imported_by`, `migration_batch_id` |
| `knowledge_tag` | 2 545 | `knowledge_id`, `tag` |
| `relation` | 47 | `id`, `from_id`, `relation_type`, `to_id`, `created_at`, `created_by`, `status`, `superseded_by` |
| `proof` | 4 | `id`, `kind`, `command`, `result`, `exit_code`, `stdout_ref`, `stderr_ref`, `artifact_path`, `artifact_hash`, `artifact_size`, `environment_json`, `started_at`, `finished_at`, `payload_hash`, `receipt_hmac`, `admissible`, `created_at`, `created_by` |
| `proof_link` | 3 | `knowledge_id`, `proof_id`, `linked_at`, `linked_by` |
| `front_state` | 24 | `key`, `value`, `updated_at`, `updated_by` |
| `audit_event` | 1 193 | `id`, `timestamp`, `actor`, `operation`, `entity_type`, `entity_id`, `payload_before`, `payload_after` |
| `asset` | 0 | `id`, `kind`, `source_kind`, `relative_path`, `sha256`, `size_bytes`, `provenance_json`, `created_at`, `created_by` |

## Valeurs knowledge

| Dimension | Valeurs observées |
|---|---|
| Types | `ARCHITECTURE` (10), `DECISION` (4), `DISCOVERY` (8), `FORENSIC` (310), `MEASUREMENT` (103), `OBSERVATION` (66), `RULE` (11), `STATE` (20) |
| Statuts | `ACTIVE` (50), `OBSERVED` (481), `SUPERSEDED` (1) |
| Liens legacy | 520 enregistrements portent `component_id`, 0 portent `function_id`, 3 portent `brick_id`; 1 enregistrement porte `supersedes_id`. |

> **Implication de cadrage :** le premier sous-contrat M4-C doit normaliser explicitement les types et les statuts, préserver la provenance complète et refuser par défaut la migration directe de `SUPERSEDED`, des relations, preuves, Front et tags tant que leurs contracts propres n’existent pas.

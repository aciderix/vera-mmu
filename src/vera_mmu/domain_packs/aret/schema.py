"""Declarative inventory of the observed ARET V1 application schema."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AretLegacySchemaManifest:
    """Observed schema names only; this object does not inspect, open or import a database."""

    migration_versions: tuple[int, ...]
    application_tables: tuple[str, ...]


def aret_v1_schema_manifest() -> AretLegacySchemaManifest:
    """Return the immutable, observed ARET V1 application-schema inventory."""
    return AretLegacySchemaManifest(
        migration_versions=(1, 2, 3, 4, 5, 6),
        application_tables=(
            "asset",
            "audit_event",
            "brick",
            "bundle_import",
            "component",
            "front_state",
            "function_symbol",
            "id_sequence",
            "knowledge",
            "knowledge_source",
            "knowledge_tag",
            "migration_batch",
            "pipeline_run",
            "proof",
            "proof_link",
            "relation",
            "schema_migrations",
            "store_metadata",
        ),
    )

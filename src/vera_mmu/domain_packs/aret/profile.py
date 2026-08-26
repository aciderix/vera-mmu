"""Closed, declarative compatibility profile for observed ARET V1 conventions."""

from __future__ import annotations

from dataclasses import dataclass

from .runtime import AretLegacyRuntimeLayout, legacy_runtime_layout
from .schema import AretLegacySchemaManifest, aret_v1_schema_manifest


@dataclass(frozen=True)
class AretCompatibilityProfile:
    """Compatibility declarations only; this profile never resolves, imports or mutates."""

    profile_id: str
    version: str
    address_scheme: str
    runtime: AretLegacyRuntimeLayout
    schema: AretLegacySchemaManifest
    supported_operations: tuple[str, ...]
    forbidden_operations: tuple[str, ...]


def aret_v1_compatibility_profile() -> AretCompatibilityProfile:
    """Return the immutable, strictly bounded ARET V1 compatibility profile."""
    return AretCompatibilityProfile(
        profile_id="aret-v1-compatibility",
        version="1",
        address_scheme="ARET://",
        runtime=legacy_runtime_layout(),
        schema=aret_v1_schema_manifest(),
        supported_operations=("parse_address", "describe_runtime", "describe_schema"),
        forbidden_operations=("resolve_runtime", "read_sqlite", "import_data", "write_vera"),
    )

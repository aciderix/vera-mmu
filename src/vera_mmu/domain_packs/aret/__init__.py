"""Isolated ARET domain-pack compatibility surfaces."""

from .addressing import (
    ARET_RESOURCE_TYPES,
    AretAddress,
    AretAddressCompatibilityError,
    make_aret_address,
    parse_aret_address,
)
from .runtime import AretLegacyRuntimeLayout, legacy_runtime_layout
from .schema import AretLegacySchemaManifest, aret_v1_schema_manifest
from .profile import AretCompatibilityProfile, aret_v1_compatibility_profile

__all__ = [
    "ARET_RESOURCE_TYPES",
    "AretAddress",
    "AretAddressCompatibilityError",
    "make_aret_address",
    "parse_aret_address",
    "AretLegacyRuntimeLayout",
    "legacy_runtime_layout",
    "AretLegacySchemaManifest",
    "aret_v1_schema_manifest",
    "AretCompatibilityProfile",
    "aret_v1_compatibility_profile",
]

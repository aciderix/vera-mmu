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
from .mapping import AretStructuralMapping, aret_v1_structural_mappings
from .import_preparation import (
    AretComponentImportPreparation,
    AretComponentImportPreparationError,
    component_import_preparation,
)
from .source_attestation import (
    ARET_V1_BASELINE_REVISION,
    AretSourceAttestationError,
    AretV1ComponentSourceAttestation,
    attest_aret_v1_component_source,
)
from .git_identity import (
    AretGitSourceIdentityError,
    AretV1GitSourceIdentity,
    verify_aret_v1_git_source_identity,
)

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
    "AretStructuralMapping",
    "aret_v1_structural_mappings",
    "AretComponentImportPreparation",
    "AretComponentImportPreparationError",
    "component_import_preparation",
    "ARET_V1_BASELINE_REVISION",
    "AretSourceAttestationError",
    "AretV1ComponentSourceAttestation",
    "attest_aret_v1_component_source",
    "AretGitSourceIdentityError",
    "AretV1GitSourceIdentity",
    "verify_aret_v1_git_source_identity",
]

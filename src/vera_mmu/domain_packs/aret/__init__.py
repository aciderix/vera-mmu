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
from .sqlite_schema import (
    AretSqliteSchemaInspectionError,
    AretV1SchemaSnapshotInspection,
    inspect_aret_v1_schema_snapshot,
)
from .component_reader import (
    AretComponentSourceReadError,
    AretV1ComponentSourcePage,
    AretV1ComponentSourceRecord,
    read_aret_v1_component_page,
)
from .component_import_preflight import (
    AretComponentImportPreflightError,
    AretV1ComponentImportPreflight,
    component_import_preflight,
)
from .component_entity_projection import (
    AretComponentEntityProjectionError,
    AretV1ComponentEntityProjection,
    AretV1EntityDraft,
    project_aret_v1_component_entities,
)
from .component_target_collision import (
    AretComponentTargetCollisionError,
    AretV1ComponentTargetClearCheck,
    check_aret_v1_component_target_clear,
)
from .component_schema_conformance import (
    AretComponentSchemaConformanceError,
    AretV1ComponentSchemaConformance,
    inspect_aret_v1_component_schema,
)
from .component_page_import import (
    AretComponentPageImportError,
    AretV1AuthorizedComponentPageImportResult,
    AretV1ComponentPageImportAuthorization,
    authorize_aret_v1_component_page_import,
    import_authorized_aret_v1_component_page,
)
from .component_authorized_import import (
    AretComponentAuthorizedImportError,
    AretV1AuthorizedComponentImportResult,
    AretV1ComponentImportAuthorization,
    authorize_aret_v1_component_import,
    import_authorized_aret_v1_component_entities,
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
    "AretSqliteSchemaInspectionError",
    "AretV1SchemaSnapshotInspection",
    "inspect_aret_v1_schema_snapshot",
    "AretComponentSourceReadError",
    "AretV1ComponentSourcePage",
    "AretV1ComponentSourceRecord",
    "read_aret_v1_component_page",
    "AretComponentImportPreflightError",
    "AretV1ComponentImportPreflight",
    "component_import_preflight",
    "AretComponentEntityProjectionError",
    "AretV1ComponentEntityProjection",
    "AretV1EntityDraft",
    "project_aret_v1_component_entities",
    "AretComponentTargetCollisionError",
    "AretV1ComponentTargetClearCheck",
    "check_aret_v1_component_target_clear",
    "AretComponentSchemaConformanceError",
    "AretV1ComponentSchemaConformance",
    "inspect_aret_v1_component_schema",
    "AretComponentPageImportError",
    "AretV1AuthorizedComponentPageImportResult",
    "AretV1ComponentPageImportAuthorization",
    "authorize_aret_v1_component_page_import",
    "import_authorized_aret_v1_component_page",
    "AretComponentAuthorizedImportError",
    "AretV1AuthorizedComponentImportResult",
    "AretV1ComponentImportAuthorization",
    "authorize_aret_v1_component_import",
    "import_authorized_aret_v1_component_entities",
]

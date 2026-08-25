"""VERA-MMU: a transport-neutral Core for verifiable project memory."""

from .addressing import Address, AddressError, CORE_RESOURCE_TYPES, make_address, parse_address
from .assets import Asset, AssetError, AssetNotFoundError, AssetService, MAX_ASSET_BYTES
from .entities import Entity, EntityError, EntityNotFoundError, EntityService, EntityType
from .knowledge import (
    Knowledge,
    KnowledgeAdmissionError,
    KnowledgeError,
    KnowledgeNotFoundError,
    KnowledgeService,
    KnowledgeType,
)
from .identity import (
    ProfileError,
    ProfileIdentity,
    ProjectIdentity,
    canonical_json,
    load_profile,
    profile_identity,
    project_identity,
    validate_profile,
)
from .migrations import Migration, MigrationError, MigrationRunner, migration_checksums
from .provenance import KnowledgeSource, KnowledgeSourceError, KnowledgeSourceNotFoundError, KnowledgeSourceService
from .relations import Relation, RelationError, RelationNotFoundError, RelationService, RelationType
from .runtime import RuntimeLocator, RuntimeLocatorError
from .store import MemoryStore, StoreError, StoreIdentityError
from .supersession import (
    KnowledgeSupersession,
    KnowledgeSupersessionError,
    KnowledgeSupersessionNotFoundError,
    KnowledgeSupersessionService,
)
from .workspace import Workspace, WorkspaceError, WorkspaceResolver, resolve_workspace

__all__ = [
    "Address",
    "AddressError",
    "Asset",
    "AssetError",
    "AssetNotFoundError",
    "AssetService",
    "CORE_RESOURCE_TYPES",
    "Entity",
    "EntityError",
    "EntityNotFoundError",
    "EntityService",
    "EntityType",
    "MAX_ASSET_BYTES",
    "MemoryStore",
    "Knowledge",
    "KnowledgeAdmissionError",
    "KnowledgeError",
    "KnowledgeNotFoundError",
    "KnowledgeService",
    "KnowledgeType",
    "KnowledgeSupersession",
    "KnowledgeSupersessionError",
    "KnowledgeSupersessionNotFoundError",
    "KnowledgeSupersessionService",
    "KnowledgeSource",
    "KnowledgeSourceError",
    "KnowledgeSourceNotFoundError",
    "KnowledgeSourceService",
    "Migration",
    "MigrationError",
    "MigrationRunner",
    "ProfileError",
    "ProfileIdentity",
    "ProjectIdentity",
    "Relation",
    "RelationError",
    "RelationNotFoundError",
    "RelationService",
    "RelationType",
    "RuntimeLocator",
    "StoreError",
    "StoreIdentityError",
    "RuntimeLocatorError",
    "Workspace",
    "WorkspaceError",
    "WorkspaceResolver",
    "canonical_json",
    "load_profile",
    "make_address",
    "migration_checksums",
    "parse_address",
    "profile_identity",
    "project_identity",
    "resolve_workspace",
    "validate_profile",
]

__version__ = "0.1.0"

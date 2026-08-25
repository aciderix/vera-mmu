"""VERA-MMU: a transport-neutral Core for verifiable project memory."""

from .addressing import Address, AddressError, CORE_RESOURCE_TYPES, make_address, parse_address
from .assets import Asset, AssetError, AssetNotFoundError, AssetService, MAX_ASSET_BYTES
from .capabilities import Capability, CapabilityError, CapabilityNotFoundError, CapabilityService
from .asset_provenance import AssetSource, AssetSourceError, AssetSourceNotFoundError, AssetSourceService, MAX_ASSET_SOURCE_LIST_LIMIT
from .entities import Entity, EntityError, EntityNotFoundError, EntityService, EntityType
from .knowledge_assets import (
    KnowledgeAssetLink,
    KnowledgeAssetLinkError,
    KnowledgeAssetLinkNotFoundError,
    KnowledgeAssetLinkService,
)
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
from .symbols import Symbol, SymbolError, SymbolNotFoundError, SymbolService
from .supersession import (
    KnowledgeSupersession,
    KnowledgeSupersessionError,
    KnowledgeSupersessionNotFoundError,
    KnowledgeSupersessionService,
)
from .work_items import WorkItem, WorkItemError, WorkItemNotFoundError, WorkItemService
from .workspace import Workspace, WorkspaceError, WorkspaceResolver, resolve_workspace

__all__ = [
    "Address",
    "AddressError",
    "Asset",
    "AssetError",
    "AssetNotFoundError",
    "AssetService",
    "AssetSource",
    "AssetSourceError",
    "AssetSourceNotFoundError",
    "AssetSourceService",
    "Capability",
    "CapabilityError",
    "CapabilityNotFoundError",
    "CapabilityService",
    "CORE_RESOURCE_TYPES",
    "Entity",
    "EntityError",
    "EntityNotFoundError",
    "EntityService",
    "EntityType",
    "MAX_ASSET_BYTES",
    "MAX_ASSET_SOURCE_LIST_LIMIT",
    "MemoryStore",
    "Knowledge",
    "KnowledgeAssetLink",
    "KnowledgeAssetLinkError",
    "KnowledgeAssetLinkNotFoundError",
    "KnowledgeAssetLinkService",
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
    "Symbol",
    "SymbolError",
    "SymbolNotFoundError",
    "SymbolService",
    "RuntimeLocatorError",
    "WorkItem",
    "WorkItemError",
    "WorkItemNotFoundError",
    "WorkItemService",
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

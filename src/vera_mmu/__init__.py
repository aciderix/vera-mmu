"""VERA-MMU: a transport-neutral Core for verifiable project memory."""

from .addressing import Address, AddressError, CORE_RESOURCE_TYPES, make_address, parse_address
from .entities import Entity, EntityError, EntityNotFoundError, EntityService, EntityType
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
from .runtime import RuntimeLocator, RuntimeLocatorError
from .store import MemoryStore, StoreError, StoreIdentityError
from .workspace import Workspace, WorkspaceError, WorkspaceResolver, resolve_workspace

__all__ = [
    "Address",
    "AddressError",
    "CORE_RESOURCE_TYPES",
    "Entity",
    "EntityError",
    "EntityNotFoundError",
    "EntityService",
    "EntityType",
    "MemoryStore",
    "Migration",
    "MigrationError",
    "MigrationRunner",
    "ProfileError",
    "ProfileIdentity",
    "ProjectIdentity",
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

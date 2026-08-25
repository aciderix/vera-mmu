"""VERA-MMU: a transport-neutral Core for verifiable project memory."""

from .addressing import Address, AddressError, CORE_RESOURCE_TYPES, make_address, parse_address
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
from .runtime import RuntimeLocator, RuntimeLocatorError
from .workspace import Workspace, WorkspaceError, WorkspaceResolver, resolve_workspace

__all__ = [
    "Address",
    "AddressError",
    "CORE_RESOURCE_TYPES",
    "ProfileError",
    "ProfileIdentity",
    "ProjectIdentity",
    "RuntimeLocator",
    "RuntimeLocatorError",
    "Workspace",
    "WorkspaceError",
    "WorkspaceResolver",
    "canonical_json",
    "load_profile",
    "make_address",
    "parse_address",
    "profile_identity",
    "project_identity",
    "resolve_workspace",
    "validate_profile",
]

__version__ = "0.1.0"

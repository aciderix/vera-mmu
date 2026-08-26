"""Isolated ARET domain-pack compatibility surfaces."""

from .addressing import (
    ARET_RESOURCE_TYPES,
    AretAddress,
    AretAddressCompatibilityError,
    make_aret_address,
    parse_aret_address,
)
from .runtime import AretLegacyRuntimeLayout, legacy_runtime_layout

__all__ = [
    "ARET_RESOURCE_TYPES",
    "AretAddress",
    "AretAddressCompatibilityError",
    "make_aret_address",
    "parse_aret_address",
    "AretLegacyRuntimeLayout",
    "legacy_runtime_layout",
]

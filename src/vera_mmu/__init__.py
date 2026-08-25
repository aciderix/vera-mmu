"""VERA-MMU: verifiable continuity primitives for AI-assisted projects."""

from .identity import ProfileIdentity, canonical_json, load_profile, profile_identity

__all__ = [
    "ProfileIdentity",
    "canonical_json",
    "load_profile",
    "profile_identity",
]

__version__ = "0.1.0"

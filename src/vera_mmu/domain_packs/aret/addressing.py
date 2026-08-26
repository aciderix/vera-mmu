"""Read-only compatibility parser for canonical ARET V1 addresses."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote, unquote


ARET_RESOURCE_TYPES = frozenset(
    {
        "knowledge",
        "component",
        "function",
        "brick",
        "proof",
        "relation",
        "asset",
        "pipeline",
    }
)


class AretAddressCompatibilityError(ValueError):
    """Raised when an ARET V1 address is not canonical and read-compatible."""


@dataclass(frozen=True)
class AretAddress:
    """One canonical legacy address; this value has no store resolution behavior."""

    resource_type: str
    identifier: str

    @property
    def canonical(self) -> str:
        return make_aret_address(self.resource_type, self.identifier)


def make_aret_address(resource_type: str, identifier: str) -> str:
    """Construct one canonical, closed ARET V1 address for compatibility reads only."""
    if resource_type == "front" and identifier == "current":
        return "ARET://front/current"
    if resource_type not in ARET_RESOURCE_TYPES:
        raise AretAddressCompatibilityError("Type de ressource ARET hors compatibilité fermée.")
    if not isinstance(identifier, str) or not identifier or "/" in identifier:
        raise AretAddressCompatibilityError("Identifiant ARET invalide.")
    return f"ARET://{resource_type}/{quote(identifier, safe='!._-')}"


def parse_aret_address(address: str) -> AretAddress:
    """Parse one exact canonical ARET V1 address without lookup, mutation or migration."""
    if not isinstance(address, str) or not address.startswith("ARET://"):
        raise AretAddressCompatibilityError("Préfixe ARET:// strictement requis.")
    rest = address[len("ARET://") :]
    parts = rest.split("/", 1)
    if len(parts) != 2:
        raise AretAddressCompatibilityError("Ressource et identifiant ARET requis.")
    resource_type, encoded_identifier = parts
    try:
        identifier = unquote(encoded_identifier, errors="strict")
    except UnicodeDecodeError as exc:
        raise AretAddressCompatibilityError("Encodage ARET invalide.") from exc
    canonical = make_aret_address(resource_type, identifier)
    if address != canonical:
        raise AretAddressCompatibilityError("Adresse ARET non canonique.")
    return AretAddress(resource_type, identifier)

"""Registry fermé des adapters de runtime MCP déclarés par l’hôte serveur.

Les adapters sont des objets Python déjà instanciés par l’hôte de confiance. Ce module ne
charge pas de module par nom, ne lit pas de chemin et ne lance aucune commande : il vérifie
uniquement que les bindings attestés du manifeste se résolvent exactement.
"""

from __future__ import annotations

from types import MappingProxyType
import re
from typing import Iterable, Mapping, Protocol

from .mcp_manifest import MCPManifest
from .store import StoreError


_ADAPTER_ID_RE = re.compile(r"[a-z][a-z0-9-]{0,127}")


class AdapterRegistryError(StoreError):
    """Le registry runtime est incomplet, ambigu ou incompatible avec le manifeste."""


class RegisteredRuntimeAdapter(Protocol):
    """Surface minimale d’un adapter déjà instancié par l’hôte serveur."""

    adapter_id: str

    def run(self, *args: object, **kwargs: object) -> Mapping[str, object]:
        """Exécute seulement via la façade, jamais pendant la résolution."""


class RuntimeAdapterRegistry:
    """Index immutable d’adapters déclarés et non chargés dynamiquement."""

    def __init__(self, adapters: Iterable[RegisteredRuntimeAdapter]) -> None:
        try:
            candidates = tuple(adapters)
        except TypeError as exc:
            raise AdapterRegistryError("Les adapters doivent former un itérable déclaré.") from exc
        indexed: dict[str, RegisteredRuntimeAdapter] = {}
        for adapter in candidates:
            adapter_id = getattr(adapter, "adapter_id", None)
            if not isinstance(adapter_id, str) or _ADAPTER_ID_RE.fullmatch(adapter_id) is None:
                raise AdapterRegistryError("Identifiant d’adapter invalide : chemin ou commande interdits.")
            if not callable(getattr(adapter, "run", None)):
                raise AdapterRegistryError("Adapter sans méthode run déclarée.")
            if adapter_id in indexed:
                raise AdapterRegistryError("Identifiant d’adapter dupliqué.")
            indexed[adapter_id] = adapter
        self._adapters = MappingProxyType(dict(sorted(indexed.items())))

    @property
    def adapter_ids(self) -> tuple[str, ...]:
        """Expose uniquement les identifiants déclarés, dans l’ordre canonique."""
        return tuple(self._adapters)

    def resolve_manifest(self, manifest: MCPManifest) -> Mapping[str, RegisteredRuntimeAdapter]:
        """Résout toutes les capabilities d’un manifest, ou refuse sans exécuter."""
        if not isinstance(manifest, MCPManifest):
            raise AdapterRegistryError("Manifeste MCP invalide pour le registry.")
        resolved: dict[str, RegisteredRuntimeAdapter] = {}
        seen_capabilities: set[str] = set()
        for item in manifest.capabilities:
            if item.capability_id in seen_capabilities:
                raise AdapterRegistryError("Capability dupliquée dans le manifeste MCP.")
            seen_capabilities.add(item.capability_id)
            adapter = self._adapters.get(item.adapter_id)
            if adapter is None:
                raise AdapterRegistryError(
                    f"Adapter déclaré par le manifeste introuvable : {item.adapter_id}."
                )
            resolved[item.capability_id] = adapter
        if not resolved:
            raise AdapterRegistryError("Manifeste MCP sans capability à résoudre.")
        return MappingProxyType(dict(sorted(resolved.items())))

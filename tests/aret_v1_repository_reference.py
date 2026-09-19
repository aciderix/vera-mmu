"""Le dépôt SQLite d'ARET, chargé pour être **exécuté** — son store, ses migrations, ses bundles.

`C02` avait lu `repository.py` dans son arbre syntaxique pour épingler la précédence de résolution
du runtime. `C14` demande autre chose : ce que fait réellement un bundle ARET devant une mémoire,
une altération ou une identité étrangère. Une lecture ne répond pas à cette question ; l'exécution
si, et c'est la méthode que `C13` a inaugurée.

**Le layout versionné rend l'exécution possible sans rien modifier.** `MemoryStore._migrate` et
`_bundle_migrations` cherchent leur DDL à `Path(__file__).parents[1] / "schema"` : depuis
`fixtures/aret_v1/source/repository_reference.py`, cela désigne exactement
`fixtures/aret_v1/schema/`, où les six migrations réelles sont versionnées avec leurs empreintes.
ARET tourne donc sur son propre schéma, pas sur une reconstitution.

La seule dépendance externe du module est `core.addressing`, dont la référence est déjà versionnée
pour `C01`. Elle est présentée sous ce nom, avec son empreinte épinglée elle aussi : charger une
autre source d'adressage ferait tourner un ARET qui n'est pas celui qu'on croit mesurer.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.util
from pathlib import Path
import sys
import types
from types import ModuleType

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "aret_v1"
REFERENCE = FIXTURES / "source" / "repository_reference.py"
ADDRESSING = FIXTURES / "addressing_reference.py"

#: SHA-256 des deux sources, au commit épinglé par le README des fixtures.
REFERENCE_SHA256 = "18031bbe94ccadc41eefaf7c7bd36630bb2dad20f2ffaccdbef533eb73e48bcc"
ADDRESSING_SHA256 = "ebd735929e0e81240b14bc37fb37a668d8532015a59a0b5fd93336cfeb2bbb68"

_module: ModuleType | None = None


def reference_digest() -> str:
    return sha256(REFERENCE.read_bytes()).hexdigest()


def addressing_digest() -> str:
    return sha256(ADDRESSING.read_bytes()).hexdigest()


def _load(name: str, path: Path) -> ModuleType:
    """Charger un module en l'enregistrant **avant** son exécution.

    L'ordre n'est pas cosmétique : `addressing_reference` déclare des `@dataclass`, et le
    décorateur résout `cls.__module__` dans `sys.modules` pendant l'exécution du module. Enregistrer
    après échoue sur un `AttributeError` opaque.
    """
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise AssertionError(f"La référence ARET {path.name} n’est pas chargeable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def aret_repository() -> ModuleType:
    """Charger le dépôt ARET comme module exécutable, une seule fois par session de test."""
    global _module
    if _module is None:
        if "core" not in sys.modules:
            package = types.ModuleType("core")
            package.__path__ = []  # type: ignore[attr-defined]
            sys.modules["core"] = package
        _load("core.addressing", ADDRESSING)
        _module = _load("aret_v1_repository", REFERENCE)
    return _module


def memory_store(path: Path, **options: object):
    """Ouvrir un `MemoryStore` ARET réel, en écriture, sous une racine donnée.

    L'écriture est passée explicitement plutôt que par `ARET_WRITE_ENABLED` : un test qui règle une
    variable d'environnement globale laisse une trace aux suivants, et `C02` a précisément épinglé
    que lire l'environnement est le resserrement qui sépare les deux moteurs.
    """
    return aret_repository().MemoryStore(path, write_enabled=True, **options)

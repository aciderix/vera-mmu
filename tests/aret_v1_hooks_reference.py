"""Les hooks de reprise d'ARET, chargés pour être **exécutés**.

`C15` porte sur une machine à états : une barrière s'arme à l'ouverture d'une session, refuse ou
laisse passer une action, se lève sur un acquittement, se réarme après compaction. Aucune de ces
transitions ne se lit dans le code ; chacune dépend d'un fichier d'état réel, d'un payload réel et
d'un environnement réel. `C13`, `C14`, `C06` puis `C12` ont établi la méthode — la référence tourne.

Quatre fichiers sont versionnés et épinglés :

* `resume_guard.py` est la machine à états elle-même. Il n'importe que la bibliothèque standard, si
  bien qu'il s'exécute tel quel depuis les fixtures.
* `common.py` est le transport : il décide de l'état dégradé et assemble le contexte injecté. Il
  importe `core.repository`, satisfait par la référence de dépôt déjà chargeable pour `C14`, et
  `resume_guard`, présenté sous ce nom avant l'import.
* `session_start.py` et `post_compact.py` sont les deux entrées qui arment réellement la barrière.
  Elles importent `evidence.adapters.pipelines`, satisfait par la référence de pipelines déjà
  chargeable pour `C06`.

Les modules intermédiaires `core`, `evidence` et `evidence.adapters` n'existent pas dans les
fixtures : seules des coquilles de paquet sont enregistrées pour que le chemin d'import se résolve.
Aucun code ARET n'est remplacé — les trois modules feuilles sont les vraies copies épinglées.

`PROJECT_ROOT` que ces fichiers calculent (`parents[1]`) désigne, depuis `fixtures/aret_v1/hooks/`,
la racine des fixtures ; ils l'ajoutent à `sys.path`, ce qui est sans effet ici puisque chaque import
est déjà résolu dans `sys.modules`.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.util
from pathlib import Path
import sys
from types import ModuleType

from tests.aret_v1_pipelines_reference import aret_pipelines
from tests.aret_v1_repository_reference import aret_repository

HOOKS = Path(__file__).resolve().parent / "fixtures" / "aret_v1" / "hooks"

#: SHA-256 des quatre hooks de `aret-memory/hooks/` au commit épinglé par le README des fixtures.
RESUME_GUARD_SHA256 = "2c9d84013497fb14cc53907d5ee2dce85b5f78c92ced4c970ef0fae0ffbff6d7"
COMMON_SHA256 = "22785324b0cab0342ed9c566c5e926b099c0304852acf782863cc2737afbddb2"
SESSION_START_SHA256 = "accd86defe8423a4dcc9c4a9afd7003a80fa22445621137787ef1328b3bbb47e"
POST_COMPACT_SHA256 = "fe7518887a25afd8406f2ca1fc6c9f9d740b2f5d39538fab6b7504f6cd4bf340"

#: L'emplacement que le garde ARET utilise sous le répertoire mémoire, tel que son code l'écrit.
ARET_GUARD_RUNTIME = ("runtime", "resume_guard")

_loaded: dict[str, ModuleType] = {}


def hook_digest(name: str) -> str:
    return sha256((HOOKS / name).read_bytes()).hexdigest()


def _load(module_name: str, file_name: str) -> ModuleType:
    """Charger un hook sous son nom d'import réel, une seule fois par session de test."""
    if module_name in _loaded:
        return _loaded[module_name]
    specification = importlib.util.spec_from_file_location(module_name, HOOKS / file_name)
    if specification is None or specification.loader is None:
        raise AssertionError(f"Le hook ARET {file_name} n’est pas chargeable")
    module = importlib.util.module_from_spec(specification)
    # Enregistré avant l'exécution : les hooks s'importent entre eux par leur nom de module.
    sys.modules[module_name] = module
    _loaded[module_name] = module
    specification.loader.exec_module(module)
    return module


def _package_shell(name: str) -> ModuleType:
    """Une coquille de paquet, seulement pour que `evidence.adapters.pipelines` se résolve."""
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    shell = ModuleType(name)
    shell.__path__ = []  # type: ignore[attr-defined]
    sys.modules[name] = shell
    return shell


def aret_resume_guard() -> ModuleType:
    """La machine à états de reprise d'ARET, sans aucune dépendance hors bibliothèque standard."""
    return _load("resume_guard", "resume_guard.py")


def aret_hook_common() -> ModuleType:
    """Le transport des hooks : dégradation, contexte injecté, enveloppe `run`."""
    if "common" not in _loaded:
        sys.modules["core.repository"] = aret_repository()
        aret_resume_guard()
    return _load("common", "common.py")


def _prepare_hook_imports() -> None:
    aret_hook_common()
    _package_shell("evidence")
    _package_shell("evidence.adapters")
    sys.modules["evidence.adapters.pipelines"] = aret_pipelines()


def aret_session_start() -> ModuleType:
    """Le hook SessionStart réel, celui qui arme la barrière à l'ouverture d'une session."""
    _prepare_hook_imports()
    return _load("aret_v1_session_start", "session_start.py")


def aret_post_compact() -> ModuleType:
    """Le hook PostCompact réel, celui qui réarme la barrière après une perte de contexte."""
    _prepare_hook_imports()
    return _load("aret_v1_post_compact", "post_compact.py")


def guard_state_path(memory_dir: Path, payload: dict[str, object]) -> Path:
    """Le fichier d'état que le garde ARET écrit, calculé par ARET lui-même."""
    return Path(aret_resume_guard().state_path(memory_dir, payload))

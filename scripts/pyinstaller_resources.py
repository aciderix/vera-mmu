"""Les ressources non-Python que `vera_mmu` lit à l'exécution, pour tout bundle PyInstaller.

Ce module existe parce que le défaut a été livré **deux fois**, dans deux emballages construits
séparément : la CLI `vmmu` et le sidecar du bureau. Les deux appelaient
`--collect-submodules vera_mmu` et rien d'autre ; PyInstaller collecte des modules, jamais des
fichiers de données. Les trente-neuf migrations SQL manquaient aux deux binaires.

Dans la CLI, la moitié runtime rendait un refus structuré — mauvais, mais lisible. Dans le
bridge du bureau, `MigrationError` n'était pas rattrapée : le processus **mourait**, et avec lui
la session desktop. Le même oubli, deux gravités.

Une seule définition partagée, énumérée depuis le disque plutôt qu'épinglée : un répertoire de
ressources ajouté demain est embarqué par les deux bundles sans que personne ait à y penser, et
`tests/test_cli_bundle_resources.py` le constate pour les deux.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "vera_mmu"


def package_data_dirs() -> tuple[Path, ...]:
    """Énumère les répertoires de ressources non-Python du paquet, `__pycache__` exclu.

    Embarquer `__pycache__` gonflerait les bundles et y figerait des bytecodes compilés par une
    autre version de Python : l'exclusion est une règle, pas un effet de bord.
    """
    directories = {
        path.parent
        for path in PACKAGE.rglob("*")
        if path.is_file() and path.suffix != ".py" and "__pycache__" not in path.parts
    }
    return tuple(sorted(directories))


def add_data_arguments() -> list[str]:
    """Rend les `--add-data` à insérer dans une commande PyInstaller.

    La destination est `vera_mmu/<chemin relatif>` et non `<chemin relatif>` seul : PyInstaller
    extrait sous `_MEIPASS/<destination>`, et c'est exactement là que
    `Path(__file__).with_name("schema")` résout depuis `_MEIPASS/vera_mmu/migrations.pyc`. Une
    destination approchante embarquerait les fichiers sans les rendre trouvables — le défaut
    intact sous une commande d'apparence corrigée.
    """
    arguments: list[str] = []
    for directory in package_data_dirs():
        destination = Path("vera_mmu") / directory.relative_to(PACKAGE)
        arguments += ["--add-data", f"{directory}{os.pathsep}{destination.as_posix()}"]
    return arguments

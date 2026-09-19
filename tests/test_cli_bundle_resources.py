"""Le bundle CLI embarque-t-il ce que le paquet lit à l'exécution ?

**Mesuré le 19 septembre 2026 sur l'artefact livré** — `vmmu` téléchargé depuis le run CI #66,
sha256 `6c75e49b630b4ce69ee07edb4443dcc06c88a25069f333d14aad1fc141734c1c`, manifest déclarant
`source_revision` `4a24b800`, `vera_mmu` désinstallé de l'environnement pour garantir que rien
du dépôt n'était mesuré à sa place :

    $ ./vmmu init neuf/.vera-mmu/project.yaml
    {"error": "Répertoire de migrations introuvable : /tmp/_MEI…/vera_mmu/schema", "ok": false}

Vingt et une sous-commandes rendaient cette erreur, dont `init` — c'est-à-dire la remédiation
que `doctor` proposait lui-même pour la réparer. La moitié runtime de la CLI livrée était
inatteignable : mémoire, executions, evidences, preuves, promotion, et `serve`, donc le serveur
MCP entier.

**La cause n'était pas dans le Core.** `MigrationRunner` localise ses migrations par
`Path(__file__).with_name("schema")`, ce qui est correct y compris sous PyInstaller. Le bundle,
lui, était construit avec `--collect-submodules vera_mmu` et rien d'autre : PyInstaller collecte
des **modules**, jamais des fichiers de données. Les trente-neuf `.sql` n'y étaient tout
simplement pas, et aucune étape de build ne pouvait le dire — le binaire se construisait et se
lançait très bien.

**Pourquoi tous les tests étaient verts.** Ils s'exécutent contre l'arborescence source, où
`src/vera_mmu/schema/` existe. Le défaut ne vivait que dans l'emballage, donc seul un test qui
regarde l'emballage pouvait le voir. C'est la leçon que la correction de l'utilisateur — « faut
être sûr que c'est bien l'app que tu utilises » — a rendue mesurable.

Ce fichier n'a pas besoin de construire un binaire de 39 Mo pour tenir : il compare ce que le
paquet contient comme ressources à ce que la commande de build déclare. L'énumération est faite
des deux côtés, jamais épinglée en dur, pour qu'un futur répertoire de ressources soit couvert
sans que personne ait à y penser.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "vera_mmu"


def _build_module():
    """Charge le script de build sans l'exécuter comme programme."""
    specification = importlib.util.spec_from_file_location(
        "vera_build_cli_bundle", ROOT / "scripts" / "build_cli_bundle.py"
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


class CliBundleResourceTests(unittest.TestCase):
    """Ce que `vera_mmu` lit à l'exécution doit figurer dans la commande de build."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.build = _build_module()

    def _declared_destinations(self) -> dict[str, str]:
        """Rend les `--add-data` de la commande, sous la forme {destination: source}."""
        spec = self.build.TARGETS["x86_64-unknown-linux-gnu"]
        command = self.build.pyinstaller_command(spec, Path("/tmp/dist"), Path("/tmp/work"))
        declared: dict[str, str] = {}
        for index, argument in enumerate(command):
            if argument == "--add-data":
                source, destination = command[index + 1].rsplit(os.pathsep, 1)
                declared[destination] = source
        return declared

    def test_every_package_resource_directory_is_shipped(self) -> None:
        """Le cœur : aucun répertoire de ressources ne doit manquer à l'appel.

        Les deux côtés sont énumérés depuis le disque, donc ce test reste vrai pour une
        ressource ajoutée demain — et faux le jour où elle est ajoutée sans être embarquée.
        """
        directories = self.build.package_data_dirs()
        self.assertTrue(directories, "Aucun répertoire de ressources détecté : l’énumération est cassée")
        declared = self._declared_destinations()
        for directory in directories:
            destination = (Path("vera_mmu") / directory.relative_to(PACKAGE)).as_posix()
            with self.subTest(ressource=destination):
                self.assertIn(
                    destination,
                    declared,
                    f"`{destination}` est lu à l’exécution mais absent des `--add-data` du bundle",
                )
                self.assertEqual(Path(declared[destination]), directory)

    def test_the_migrations_directory_is_the_one_the_runner_looks_for(self) -> None:
        """La destination déclarée doit être exactement celle que `MigrationRunner` dérive.

        `--add-data src/vera_mmu/schema:vera_mmu/schema` ne vaut que parce que PyInstaller
        l'extrait sous `_MEIPASS/vera_mmu/schema`, là où `Path(__file__).with_name("schema")`
        résout depuis `_MEIPASS/vera_mmu/migrations.pyc`. Une destination approchante — `schema`
        seul, ou `vera_mmu/schema/` — embarquerait les fichiers sans les rendre trouvables, et
        le défaut mesuré resterait intact sous une commande d'apparence corrigée.
        """
        from vera_mmu.migrations import MigrationRunner

        runner = MigrationRunner()
        attendu = Path(runner.schema_dir)
        self.assertEqual(attendu.name, "schema")
        self.assertEqual(attendu.parent.name, "vera_mmu")
        self.assertIn("vera_mmu/schema", self._declared_destinations())

    def test_the_shipped_inventory_is_the_complete_migration_ledger(self) -> None:
        """Embarquer le répertoire ne suffit pas s'il est incomplet : le Core exige 001..N continu.

        `discover()` refuse un inventaire troué ; le mesurer ici lie la ressource embarquée à la
        règle qui la consomme, plutôt qu'à un simple compte de fichiers.
        """
        from vera_mmu.migrations import MigrationRunner

        migrations = MigrationRunner().discover()
        self.assertEqual(migrations[0].version, 1)
        self.assertEqual(
            tuple(migration.version for migration in migrations),
            tuple(range(1, len(migrations) + 1)),
        )
        for migration in migrations:
            with self.subTest(migration=migration.path.name):
                self.assertEqual(migration.path.parent, PACKAGE / "schema")

    def test_the_build_command_still_collects_the_python_modules(self) -> None:
        """La correction ajoute des données ; elle ne doit rien retirer de ce qui marchait."""
        spec = self.build.TARGETS["x86_64-unknown-linux-gnu"]
        command = self.build.pyinstaller_command(spec, Path("/tmp/dist"), Path("/tmp/work"))
        self.assertIn("--collect-submodules", command)
        self.assertEqual(command[command.index("--collect-submodules") + 1], "vera_mmu")
        self.assertIn("--onefile", command)
        self.assertEqual(command[command.index("--name") + 1], "vmmu")

    def test_pycache_is_never_shipped_as_a_resource(self) -> None:
        """`__pycache__` contient des `.pyc` — non-`.py`, donc candidats par accident.

        Les embarquer gonflerait le bundle et y figerait des bytecodes d'une autre version de
        Python. L'exclusion est une règle, pas un effet de bord : elle est mesurée.
        """
        for directory in self.build.package_data_dirs():
            with self.subTest(repertoire=str(directory)):
                self.assertNotIn("__pycache__", directory.parts)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

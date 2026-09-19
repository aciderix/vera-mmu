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


def _load(name: str, path: Path):
    """Charge un script du dépôt sans l'exécuter comme programme."""
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def _build_module():
    return _load("vera_build_cli_bundle", ROOT / "scripts" / "build_cli_bundle.py")


class CliBundleResourceTests(unittest.TestCase):
    """Ce que `vera_mmu` lit à l'exécution doit figurer dans la commande de build."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.build = _build_module()
        cls.resources = _load("vera_pyinstaller_resources", ROOT / "scripts" / "pyinstaller_resources.py")

    @staticmethod
    def _destinations(command: list[str]) -> dict[str, str]:
        """Rend les `--add-data` d'une commande, sous la forme {destination: source}."""
        declared: dict[str, str] = {}
        for index, argument in enumerate(command):
            if argument == "--add-data":
                source, destination = command[index + 1].rsplit(os.pathsep, 1)
                declared[destination] = source
        return declared

    def _declared_destinations(self) -> dict[str, str]:
        spec = self.build.TARGETS["x86_64-unknown-linux-gnu"]
        return self._destinations(self.build.pyinstaller_command(spec, Path("/tmp/dist"), Path("/tmp/work")))

    def test_every_package_resource_directory_is_shipped(self) -> None:
        """Le cœur : aucun répertoire de ressources ne doit manquer à l'appel.

        Les deux côtés sont énumérés depuis le disque, donc ce test reste vrai pour une
        ressource ajoutée demain — et faux le jour où elle est ajoutée sans être embarquée.
        """
        directories = self.resources.package_data_dirs()
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

        **Le répertoire attendu est celui du paquet importé, pas celui du dépôt.** La première
        version de ce test comparait à `src/vera_mmu/schema`, et passait en local uniquement
        parce qu'un `pip install -e .` fait coïncider les deux chemins. La CI, qui installe
        normalement, a rendu `site-packages/…/vera_mmu/schema` et le test est tombé : il était
        vrai pour une raison accidentelle. Au passage, cet échec prouve que l'emballage pip, lui,
        embarquait bien les migrations — seul l'emballage PyInstaller les perdait.
        """
        import vera_mmu
        from vera_mmu.migrations import MigrationRunner

        installed_schema = Path(vera_mmu.__file__).resolve().parent / "schema"
        migrations = MigrationRunner().discover()
        self.assertEqual(migrations[0].version, 1)
        self.assertEqual(
            tuple(migration.version for migration in migrations),
            tuple(range(1, len(migrations) + 1)),
        )
        for migration in migrations:
            with self.subTest(migration=migration.path.name):
                self.assertEqual(migration.path.parent.resolve(), installed_schema)

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
        for directory in self.resources.package_data_dirs():
            with self.subTest(repertoire=str(directory)):
                self.assertNotIn("__pycache__", directory.parts)

    def test_the_desktop_sidecar_ships_the_same_resources_as_the_cli(self) -> None:
        """Le défaut a été livré **deux fois**, dans deux emballages construits séparément.

        La CLI et le sidecar du bureau appelaient chacun `--collect-submodules vera_mmu` et rien
        d'autre. Corriger la CLI seule aurait laissé le launcher graphique cassé — et il l'était
        plus gravement : le bridge ne rattrapait pas `MigrationError`, donc il **mourait** au lieu
        de refuser. Les deux commandes tirent désormais d'une seule définition, et ce test le
        constate côte à côte plutôt que de le supposer.
        """
        sidecar = _load("vera_build_desktop_sidecar", ROOT / "scripts" / "build_desktop_sidecar.py")
        sidecar_declared = self._destinations(
            sidecar.pyinstaller_command("vmmu-desktop-bridge-x86_64-unknown-linux-gnu", Path("/tmp/b"), Path("/tmp/w"))
        )
        cli_declared = self._declared_destinations()
        self.assertEqual(sidecar_declared, cli_declared)
        self.assertIn("vera_mmu/schema", sidecar_declared)
        # Et les deux tirent littéralement de la même définition, pas de deux copies jumelles.
        for module in (self.build, sidecar):
            with self.subTest(script=module.__name__):
                self.assertEqual(
                    Path(module.add_data_arguments.__code__.co_filename),
                    ROOT / "scripts" / "pyinstaller_resources.py",
                )

    def test_i014_the_desktop_bridge_refuses_a_migration_failure_instead_of_dying(self) -> None:
        """Une barrière qui se plante au lieu de refuser ne refuse rien.

        `MigrationError` dérive de `RuntimeError`, pas de `StoreError` : `__main__` la rattrape
        nommément, le bridge ne le faisait pas. **Mesuré sur l'AppImage livrée** : une requête
        `project.doctor` sortait en traceback et tuait le processus, emportant la session
        desktop. Ici, la même erreur doit ressortir en réponse `OPERATION_REFUSED` normalisée.
        """
        import json as _json
        from vera_mmu.desktop_bridge import BRIDGE_FORMAT, DesktopBridge
        from vera_mmu.migrations import MigrationError

        bridge = DesktopBridge(ROOT, nonce="n" * 32)
        def refuse(_: dict) -> dict:
            raise MigrationError("Répertoire de migrations introuvable : /nulle/part")
        bridge._handlers = {**bridge._handlers, "project.doctor": refuse}  # type: ignore[attr-defined]

        response = _json.loads(
            bridge.handle_line(
                _json.dumps(
                    {"format": BRIDGE_FORMAT, "id": "d", "nonce": "n" * 32, "operation": "project.doctor", "input": {}}
                )
            )
        )
        self.assertIs(response["ok"], False)
        self.assertEqual(response["error"]["code"], "OPERATION_REFUSED")
        self.assertIn("migrations introuvable", response["error"]["message"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

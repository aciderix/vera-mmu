"""Chaque fichier publié est-il rattaché au commit qui l'a produit ?

**Le défaut mesuré**, en vérifiant la release `v0.1.0-rc.5` telle que publiée. La chaîne de
provenance se fermait pour la CLI et pour elle seule :

    asset GitHub → SHA256SUMS → release-manifest.json → binaire vmmu → source_revision → tag

Les quatre bundles de bureau n'y figuraient nulle part. Le digest que GitHub affiche dit « ce
fichier n'a pas changé depuis le téléversement », jamais « ce fichier vient de ce commit » — et
c'est la seconde question que ce produit existe pour trancher.

La cause tenait à un ordre : le manifeste était écrit avant que `tauri build` n'ait produit quoi
que ce soit. Un artefact sans provenance publié à côté d'artefacts qui en ont une est pire
qu'inutile, puisqu'il se fait croire couvert.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))

from build_cli_bundle import ReleaseBundleError, canonical_json  # noqa: E402
import seal_release_manifest as scellement  # noqa: E402


def _fichier(chemin: Path, contenu: bytes) -> Path:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_bytes(contenu)
    return chemin


class SealTests(unittest.TestCase):
    """Le scellement couvre tout, ou refuse."""

    CIBLE = "x86_64-unknown-linux-gnu"

    def _atelier(self, racine: Path, *, bundles: tuple[str, ...] = ("VERA.AppImage", "VERA.deb")) -> tuple[Path, Path, Path]:
        cli = racine / "cli"
        _fichier(cli / "vera-mmu-cli_0.1.0-6_linux-x64.tar.gz", b"archive")
        (cli / "release-manifest.json").write_bytes(
            canonical_json(
                {
                    "artifacts": [{"path": "vmmu", "sha256": "0" * 64}],
                    "format": "vera-release-manifest/v1",
                    "platform": "linux-x64",
                    "source_revision": "a" * 40,
                    "target": self.CIBLE,
                    "version": "0.1.0-6",
                }
            )
        )
        paquets = racine / "bundle"
        for nom in bundles:
            _fichier(paquets / "sous-dossier" / nom, nom.encode())
        return cli, paquets, racine / "livrables"

    def test_every_published_file_appears_in_the_manifest(self) -> None:
        with TemporaryDirectory() as repertoire:
            racine = Path(repertoire)
            cli, paquets, sortie = self._atelier(racine)
            scellement.seal(cli, paquets, self.CIBLE, sortie)
            manifeste = json.loads((sortie / f"release-manifest-{self.CIBLE}.json").read_text(encoding="utf-8"))

        chemins = {artefact["path"] for artefact in manifeste["artifacts"]}
        self.assertIn("vera-mmu-cli_0.1.0-6_linux-x64.tar.gz", chemins)
        self.assertIn("VERA.AppImage", chemins)
        self.assertIn("VERA.deb", chemins)
        # Le binaire interne à l'archive reste attesté : le retirer romprait la vérification
        # faite au déballage, qui est la seule à pouvoir parler de ce fichier-là.
        self.assertIn("vmmu", chemins)
        self.assertEqual(manifeste["source_revision"], "a" * 40)

    def test_the_published_manifest_contains_the_one_shipped_inside_the_archive(self) -> None:
        """Les deux manifestes ne peuvent pas se contredire : l'un est un sous-ensemble de l'autre."""
        with TemporaryDirectory() as repertoire:
            racine = Path(repertoire)
            cli, paquets, sortie = self._atelier(racine)
            interne = json.loads((cli / "release-manifest.json").read_text(encoding="utf-8"))
            scellement.seal(cli, paquets, self.CIBLE, sortie)
            publie = json.loads((sortie / f"release-manifest-{self.CIBLE}.json").read_text(encoding="utf-8"))

        for cle in ("format", "platform", "source_revision", "target", "version"):
            with self.subTest(cle=cle):
                self.assertEqual(publie[cle], interne[cle])
        for artefact in interne["artifacts"]:
            self.assertIn(artefact, publie["artifacts"])

    def test_the_checksums_cover_every_published_file_and_the_manifest(self) -> None:
        with TemporaryDirectory() as repertoire:
            racine = Path(repertoire)
            cli, paquets, sortie = self._atelier(racine)
            scellement.seal(cli, paquets, self.CIBLE, sortie)
            sommes = (sortie / f"SHA256SUMS-{self.CIBLE}").read_text(encoding="utf-8")

        noms = {ligne.split("  ", 1)[1] for ligne in sommes.strip().splitlines()}
        self.assertEqual(
            noms,
            {
                "vera-mmu-cli_0.1.0-6_linux-x64.tar.gz",
                "VERA.AppImage",
                "VERA.deb",
                f"release-manifest-{self.CIBLE}.json",
            },
        )

    def test_a_missing_bundle_stops_the_release_rather_than_shrinking_it(self) -> None:
        """Publier une release amputée en silence serait le défaut, pas le refus."""
        with TemporaryDirectory() as repertoire:
            racine = Path(repertoire)
            cli, paquets, sortie = self._atelier(racine, bundles=("VERA.AppImage",))
            with self.assertRaises(ReleaseBundleError) as refus:
                scellement.seal(cli, paquets, self.CIBLE, sortie)
        self.assertIn(".deb", str(refus.exception))

    def test_two_candidates_for_one_suffix_are_refused_rather_than_picked(self) -> None:
        """Choisir au hasard rendrait la provenance dépendante de l'ordre du système de fichiers."""
        with TemporaryDirectory() as repertoire:
            racine = Path(repertoire)
            cli, paquets, sortie = self._atelier(racine)
            _fichier(paquets / "ailleurs" / "AUTRE.deb", b"autre")
            with self.assertRaises(ReleaseBundleError) as refus:
                scellement.seal(cli, paquets, self.CIBLE, sortie)
        self.assertIn("ambigu", str(refus.exception))

    def test_both_publishable_targets_declare_their_bundles(self) -> None:
        """Une cible sans liste déclarée publierait sans rien attester."""
        self.assertEqual(
            set(scellement.EXPECTED_BUNDLES),
            {"x86_64-unknown-linux-gnu", "x86_64-pc-windows-msvc"},
        )
        for cible, suffixes in scellement.EXPECTED_BUNDLES.items():
            with self.subTest(cible=cible):
                self.assertEqual(len(suffixes), 2, "chaque plateforme publie deux bundles")

    def test_the_release_workflow_seals_after_building_the_bundles(self) -> None:
        """Sceller avant le build laisserait les bundles hors du manifeste — c'était le défaut."""
        workflow = (RACINE / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        build = workflow.index("pnpm tauri build")
        sceau = workflow.index("seal_release_manifest.py")
        self.assertLess(build, sceau, "le scellement doit suivre la construction des bundles")
        # Et la publication vérifie la couverture, pas seulement la révision.
        self.assertIn("aucun manifeste ne le mentionne", workflow)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

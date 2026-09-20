"""Le paquet de bureau transporte-t-il la CLI dont sa configuration a besoin ?

**Le défaut mesuré.** La release `v0.1.0-rc.5` n'embarquait, côté bureau, que `vera-mmu-desktop`
et son sidecar `vmmu-desktop-bridge`. Or c'est la CLI `vmmu` qui porte les sous-commandes
`claude-code-local-mcp` et `claude-code-local-hook` que la configuration générée doit nommer.
Faute de l'avoir sous la main, l'installation lancée depuis la fenêtre inscrivait le chemin du
**sidecar** — qui ne connaît pas ces sous-commandes et réclame `--project-root` et `--nonce`.
Aucun serveur MCP ne pouvait démarrer, sur aucune des quatre voies de lancement essayées.

Ce fichier épingle les deux moitiés du correctif : le paquet déclare bien les deux binaires, et
la recette du second dérive de celle de l'archive CLI plutôt que d'en être une copie. Deux
recettes pour un même binaire finissent toujours par diverger — l'oubli de ressources livré
simultanément dans les deux emballages PyInstaller l'a déjà montré dans ce dépôt.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))


class DesktopPackageTests(unittest.TestCase):
    """Ce que Tauri emballe, et ce qui le construit."""

    def test_the_bundle_declares_both_the_sidecar_and_the_cli(self) -> None:
        configuration = json.loads(
            (RACINE / "apps" / "desktop" / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8")
        )
        externes = configuration["bundle"]["externalBin"]
        self.assertIn("binaries/vmmu-desktop-bridge", externes)
        self.assertIn(
            "binaries/vmmu", externes,
            "sans la CLI dans le paquet, la fenêtre ne peut nommer aucune commande qui démarre",
        )

    def test_the_embedded_cli_is_built_by_the_archive_recipe_not_a_copy_of_it(self) -> None:
        """Une seule recette, pour que les deux emballages ne puissent pas diverger."""
        import build_cli_bundle as archive
        import build_desktop_sidecar as bureau

        embarquee = bureau.cli_command("vmmu-x86_64-unknown-linux-gnu", Path("/d"), Path("/w"))
        from types import SimpleNamespace

        publiee = archive.pyinstaller_command(SimpleNamespace(binary_name="vmmu"), Path("/d"), Path("/w"))

        # Même point d'entrée : c'est ce qui fait que le binaire embarqué *est* la CLI.
        self.assertEqual(embarquee[-1], publiee[-1])
        self.assertTrue(str(embarquee[-1]).endswith("cli_entry.py"))

        # Mêmes ressources : le défaut des 39 migrations absentes venait précisément de deux
        # emballages construits séparément.
        def donnees(commande: list[str]) -> list[str]:
            return [str(valeur) for cle, valeur in zip(commande, commande[1:]) if cle == "--add-data"]

        self.assertEqual(donnees(embarquee), donnees(publiee))
        self.assertTrue(donnees(embarquee), "aucune ressource déclarée : le motif ne mord plus")

        # La seule différence admise est le nom de sortie, que Tauri exige suffixé du triplet.
        def sans_nom(commande: list[str]) -> list[str]:
            index = commande.index("--name")
            return [str(element) for position, element in enumerate(commande) if position not in (index, index + 1)]

        self.assertEqual(sans_nom(embarquee), sans_nom(publiee))
        self.assertEqual(embarquee[embarquee.index("--name") + 1], "vmmu-x86_64-unknown-linux-gnu")

    def test_the_sidecar_script_builds_the_cli_too(self) -> None:
        """La CLI doit exister **avant** `cargo test`, que `build.rs` fait passer par Tauri.

        Un lot précédent a mesuré ce que coûte l'ordre inverse : `tauri_build` résout les
        ressources déclarées dès le script de build, et le run avait échoué sur
        « resource path `binaries/vmmu-desktop-bridge-<triple>` doesn't exist ». La même
        contrainte s'applique maintenant à `binaries/vmmu-<triple>`, donc les deux binaires se
        construisent dans la même étape.
        """
        source = (RACINE / "scripts" / "build_desktop_sidecar.py").read_text(encoding="utf-8")
        self.assertIn("cli_command(", source)
        self.assertIn('f"vmmu-{target}"', source)
        # Et le workflow ne rajoute pas une étape séparée qui arriverait trop tard.
        workflow = (RACINE / ".github" / "workflows" / "desktop-packaging.yml").read_text(encoding="utf-8")
        sidecar = workflow.index("build_desktop_sidecar.py")
        essais = workflow.index("cargo test")
        self.assertLess(sidecar, essais, "le sidecar et la CLI doivent précéder `cargo test`")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

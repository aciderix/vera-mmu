"""Le nom du tag de release est-il dérivé de ce que le dépôt déclare, ou saisi à la main ?

Un tag est une affirmation publique : il dit que ce commit **est** cette version. Rien ne
garantissait la cohérence entre le nom demandé et ce que les quatre manifestes portent — on
pouvait poser `v0.1.0-rc.5` sur un arbre disant `0.1.0rc4`, et personne ne relit un tag après
coup.

Ce fichier existe aussi pour une raison de méthode. La vérification aurait pu tenir en une
expression de workflow ; elle n'aurait alors tourné qu'au moment d'une release, c'est-à-dire trop
tard et une fois sur cent. Ce dépôt a mesuré trois fois aujourd'hui qu'*un test que rien ne lance
ne garde rien* : l'ACL Tauri, `adapter_catalog`, le backend desktop. La règle vit donc dans un
module que la suite exerce à chaque run.
"""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from scripts.release_tag import ReleaseTagError, check, declared_version, expected_tag


class ReleaseTagTests(unittest.TestCase):
    """La traduction PEP 440 → SemVer, et le refus de tout écart."""

    def test_a_release_candidate_becomes_a_dotted_tag(self) -> None:
        """`0.1.0rc5` donne `v0.1.0-rc.5` — la convention déjà posée par rc.1 à rc.4.

        Le point avant le numéro n'est pas cosmétique : `v0.1.0-rc4` et `v0.1.0-rc.4` sont deux
        tags distincts, et en poser un second à côté du premier rendrait la lignée illisible.
        """
        self.assertEqual(expected_tag("0.1.0rc5"), "v0.1.0-rc.5")
        self.assertEqual(expected_tag("1.2.3rc10"), "v1.2.3-rc.10")

    def test_a_final_version_carries_no_suffix(self) -> None:
        self.assertEqual(expected_tag("0.1.0"), "v0.1.0")
        self.assertEqual(expected_tag("2.0.0"), "v2.0.0")

    def test_a_version_outside_the_closed_form_is_refused_by_name(self) -> None:
        """Un refus qui tait la valeur reçue oblige à ouvrir le code — défaut déjà corrigé ici."""
        for version in ("0.1", "0.1.0-rc5", "0.1.0a1", "0.1.0.dev1", "", "v0.1.0"):
            with self.subTest(version=version):
                with self.assertRaises(ReleaseTagError) as refus:
                    expected_tag(version)
                self.assertIn(repr(version), str(refus.exception))

    def test_the_repository_declares_a_publishable_version(self) -> None:
        """Le dépôt lui-même doit rester publiable : sinon la release échoue le jour venu."""
        version = declared_version()
        tag = expected_tag(version)
        self.assertTrue(tag.startswith("v"))
        # Et la version déclarée est bien celle que le build exige d'aligner partout.
        import importlib.util
        import sys

        racine = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location("vera_build", racine / "scripts" / "build_cli_bundle.py")
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        # `product_version()` rend la forme SemVer des manifestes (`0.1.0-5`) ; le tag en est la
        # forme publiée (`v0.1.0-rc.5`). Les deux doivent désigner la même version.
        semver = module.product_version()
        attendu = "v" + (semver.replace("-", "-rc.", 1) if "rc" in version else semver)
        self.assertEqual(tag, attendu)

    def test_check_refuses_a_tag_the_manifests_do_not_support(self) -> None:
        """Le cœur : demander un nom que l'arbre ne porte pas doit échouer, pas passer.

        Le message doit nommer les deux — ce qui a été demandé et ce qui était attendu — sans
        quoi le correctif se devine au lieu de se lire.
        """
        with tempfile.TemporaryDirectory() as repertoire:
            racine = Path(repertoire)
            (racine / "pyproject.toml").write_text(
                '[project]\nname = "x"\nversion = "0.1.0rc4"\n', encoding="utf-8"
            )
            self.assertEqual(check("v0.1.0-rc.4", racine), "v0.1.0-rc.4")
            with self.assertRaises(ReleaseTagError) as refus:
                check("v0.1.0-rc.5", racine)
            message = str(refus.exception)
            self.assertIn("v0.1.0-rc.5", message)
            self.assertIn("v0.1.0-rc.4", message)

    def test_the_release_workflow_never_trusts_expression_truthiness_for_the_flag(self) -> None:
        """Dans les expressions GitHub, **toute chaîne non vide est vraie**.

        `${{ inputs.prerelease && '--prerelease' || '' }}` publierait donc une version finale en
        pre-release le jour où cette entrée arriverait comme la chaîne `"false"` — via l'API, un
        workflow appelant, ou un changement de typage. L'erreur serait silencieuse et ne se
        verrait qu'une fois sur cent, au pire moment.

        Le drapeau est donc calculé par une comparaison explicite dans le shell. Ce test épingle
        la règle plutôt que l'instance, pour qu'elle ne revienne pas sous une autre forme.
        """
        workflow = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )
        # La **syntaxe d'expression**, pas les mots : la première version de ce test cherchait
        # `inputs.prerelease &&` et trouvait le commentaire qui explique pourquoi c'est proscrit.
        # Même défaut que celui mesuré sur le smoke check du Dockerfile ARET — chercher dans le
        # texte plutôt que dans ce qui s'exécute.
        self.assertNotIn("${{ inputs.prerelease &&", workflow)
        self.assertIn('if [ "$PRERELEASE" = "true" ]', workflow)

    def test_the_tag_is_created_through_the_api_not_by_pushing(self) -> None:
        """`git push` d'un tag est refusé quand le commit touche un fichier de workflow.

        Mesuré : « refusing to allow a GitHub App to create or update workflow
        `.github/workflows/release.yml` without `workflows` permission ». Cette permission ne peut
        pas être accordée à `GITHUB_TOKEN` — le workflow s'est donc fait refuser par sa propre
        introduction, et le referait à chaque modification de lui-même.

        L'API ne crée qu'une référence vers un objet déjà présent : rien n'est introduit, la
        restriction ne s'applique pas. Deux appels pour garder le tag **annoté**, comme la lignée
        rc.1 à rc.4 — un tag léger romprait la convention.
        """
        workflow = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("git push origin \"${{ inputs.tag }}\"", workflow)
        self.assertIn("git/tags", workflow)
        self.assertIn("git/refs", workflow)
        # L'objet tag porte un message : c'est ce qui en fait un tag annoté.
        self.assertIn('-f message=', workflow)

    def test_the_release_workflow_guards_before_it_writes(self) -> None:
        """Les trois refus doivent précéder toute écriture, sinon ils ne refusent rien.

        Vérifier après avoir tagué laisserait la référence publiée — et un tag ne se retire pas
        proprement une fois que des clones l'ont récupéré.
        """
        workflow = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )
        garde = workflow.index("jobs:\n  guard:")
        publication = workflow.index("  publish:")
        self.assertLess(garde, publication, "le job de garde doit précéder la publication")
        # Et la publication doit en dépendre, sinon l'ordre du fichier ne prouve rien.
        self.assertIn("needs: guard", workflow)
        self.assertIn("needs: package", workflow)
        # La dérivation du nom passe par le module testé, pas par une expression du workflow.
        self.assertIn("scripts/release_tag.py --check", workflow)

    def test_the_command_line_reports_a_refusal_as_a_failure(self) -> None:
        """Le workflow s'arrête sur le code de sortie : il doit être non nul quand le tag ment."""
        from scripts.release_tag import main

        self.assertEqual(main([]), 0)
        self.assertEqual(main(["--check", expected_tag(declared_version())]), 0)
        self.assertEqual(main(["--check", "v99.99.99"]), 1)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

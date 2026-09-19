"""Un refus qui tait ses valeurs admissibles oblige à lire le code pour s'en servir.

C'est une classe de défaut déjà nommée dans ce dépôt : `LOG-0323` l'avait mesurée chez ARET, dont
un refus d'oracle nommait quatre valeurs sur neuf. En exerçant la CLI livrée pour configurer un
projet neuf de bout en bout, elle est réapparue **chez VERA**, deux fois, sur les deux premières
commandes qu'un nouveau projet rencontre :

    $ vmmu init-project . --template python …
    {"error": "Template de projet inconnu.", "ok": false}

    $ vmmu declare-proof-policy … --algorithm HMAC-SHA256
    {"error": "Algorithme de policy de preuve hors catalogue fermé.", "ok": false}

Le premier ne nommait aucun des six templates ; le second taisait qu'une seule valeur existe, et
que l'écart tenait à un tiret contre un souligné. Aucun des deux n'était faux — les deux
obligeaient à ouvrir le code pour avancer.

Ce fichier épingle la règle pour les quatre catalogues fermés qu'un projet neuf rencontre en
premier, plutôt que pour les deux corrigés : c'est la classe qui compte, pas l'instance.
"""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from vera_mmu.project_bootstrap import TEMPLATE_IDS, ProjectBootstrapError, preview_project_initialization
from vera_mmu.proof_policies import HMAC_ALGORITHM, ProofPolicyError, ProofPolicyService


class RefusalsNameTheirCataloguesTests(unittest.TestCase):
    """Chaque refus de catalogue fermé nomme la valeur reçue **et** les valeurs admissibles."""

    def test_an_unknown_project_template_names_every_declared_template(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ProjectBootstrapError) as refused:
                preview_project_initialization(
                    Path(directory), template="python", project_id="p", project_name="P"
                )
        message = str(refused.exception)
        self.assertIn("python", message)
        self.assertGreaterEqual(len(TEMPLATE_IDS), 2)
        for template in sorted(TEMPLATE_IDS):
            with self.subTest(template=template):
                self.assertIn(template, message)

    def test_an_unknown_proof_algorithm_names_the_only_admissible_one(self) -> None:
        """Le cas le plus coûteux : un catalogue à une seule valeur, tue.

        `HMAC-SHA256` contre `HMAC_SHA256` — un caractère. Sans la valeur dans le message, rien ne
        distingue une faute de frappe d'un algorithme réellement absent.
        """
        with self.assertRaises(ProofPolicyError) as refused:
            ProofPolicyService.declare(
                ProofPolicyService.__new__(ProofPolicyService), "HMAC-SHA256", hmac_required=True
            )
        message = str(refused.exception)
        self.assertIn("HMAC-SHA256", message)
        self.assertIn(HMAC_ALGORITHM, message)

    def test_the_capability_contract_says_a_validator_is_always_required(self) -> None:
        """`consumes_validator` et « faut-il en déclarer un » sont deux questions distinctes.

        La lecture du contrat rendait `required_validator: null` pour `NOOP` et
        `OBSERVED_PROCESS` — vrai au sens où ces runners ne s'en servent pas à l'exécution, mais
        lu comme « pas besoin d'en déclarer ». La voie d'écriture, elle, refuse tout contrat sans
        validator, quel que soit le runner. Mesuré sur la CLI livrée : une déclaration `NOOP`
        sans `--validator` sort en `PLACEHOLDER_VALIDATOR`. Les deux voies disent désormais la
        même chose.
        """
        from vera_mmu.capability_builder import VALIDATOR_RUNNERS, capability_contract_options

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            preview = preview_project_initialization(
                root, template=sorted(TEMPLATE_IDS)[0], project_id="projet-mesure", project_name="Projet"
            )
            for item in preview.files:
                target = root / item.path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(item.content, encoding="utf-8")
            options = capability_contract_options(root / ".vera-mmu" / "project.yaml")

        self.assertIs(options["validator"]["required"], True)
        self.assertEqual(options["validator"]["available"], options["validators"])
        # Et la distinction reste lisible : les runners qui consomment un validator sont nommés.
        consuming = {item["id"] for item in options["runners"] if item["consumes_validator"]}
        self.assertEqual(consuming, set(VALIDATOR_RUNNERS))
        self.assertTrue(set(options["runners"][0]) >= {"id", "consumes_validator", "required_validator"})

    def test_an_invalid_project_id_states_the_rule_rather_than_the_verdict(self) -> None:
        """« project_id invalide » ne dit ni ce qui a été reçu ni ce qui est attendu.

        Même classe, même commande : c'est le deuxième refus qu'un projet neuf rencontre, juste
        après le template. La règle tient en une ligne ; la taire coûte un aller-retour.
        """
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ProjectBootstrapError) as refused:
                preview_project_initialization(
                    Path(directory), template=sorted(TEMPLATE_IDS)[0], project_id="X", project_name="P"
                )
        message = str(refused.exception)
        self.assertIn("X", message)
        self.assertIn("minuscules", message)

    def test_the_serve_format_identifier_is_well_formed(self) -> None:
        """`vera-serve//v1` portait une barre en trop, seul format du produit dans ce cas.

        Un identifiant de format est un contrat : un client qui compare la chaîne exacte se serait
        aligné sur la faute, et la corriger plus tard aurait alors cassé quelque chose.
        """
        import re

        from vera_mmu import __main__ as cli

        source = Path(cli.__file__).read_text(encoding="utf-8")
        formats = set(re.findall(r'"format"\s*:\s*"([a-z0-9-]+/+v[0-9]+)"', source))
        self.assertTrue(formats, "Aucun identifiant de format trouvé : le motif ne mord plus")
        for identifier in sorted(formats):
            with self.subTest(format=identifier):
                self.assertNotIn("//", identifier)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

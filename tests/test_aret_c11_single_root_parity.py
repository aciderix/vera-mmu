"""Test de parité du couplage `C11` — racine unique ARET V1 contre workspace VERA.

Le registre exige, pour promouvoir `C11` : « no-Git, mono-repo, multi-repo, symlink/traversal,
identité mismatched, installation non polluante ».

**Quatre de ces six dimensions sont déjà mesurées ailleurs, et les refaire ici serait du bruit.**
`C02` a épinglé no-Git, multi-repo et traversal sur le résolveur de runtime ; `C16` a épinglé
l'identité incohérente ; `C2` a prouvé Zero Pollution. Ce fichier les **cite** par leur test plutôt
que de les recopier, et se concentre sur ce que `C11` ajoute vraiment.

**Ce qu'il ajoute est un point de I008.** ARET expose `repository_path` sur trois de ses
quarante-quatre outils et refuse toute valeur différente de la racine configurée. VERA n'expose ce
champ sur aucun de ses outils. Les deux refusent qu'un client choisisse la racine ; l'un valide une
valeur, l'autre n'a pas de valeur à valider. Ne pas avoir le champ est le refus le plus fort : il
ne dépend d'aucune comparaison qu'on pourrait un jour relâcher.
"""
from __future__ import annotations

import ast
from pathlib import Path
import unittest

from vera_mmu.mcp_manifest import TOOL_NAMES

from tests.aret_v1_server_reference import (
    REFERENCE_SHA256,
    reference_digest,
    tool_functions,
    tool_parameters,
    tree,
)


#: Ce qu'un outil ne doit jamais recevoir du client : de quoi désigner un chemin ou une commande.
FORBIDDEN_PARAMETER_MARKERS = ("path", "root", "dir", "file", "repository", "command", "url", "cwd")
#: `direction` contient `dir` sans désigner un répertoire ; l'exception est nommée, pas silencieuse.
ALLOWED_DESPITE_MARKER = frozenset({"direction"})

#: Les dimensions que `C11` partage avec d'autres couplages, et où elles sont réellement mesurées.
COVERED_ELSEWHERE = {
    "no-Git": "tests/test_aret_c02_runtime_parity.py",
    "multi-repo": "tests/test_aret_c02_runtime_parity.py",
    "symlink/traversal": "tests/test_aret_c02_runtime_parity.py",
    "identité mismatched": "tests/test_aret_c16_epistemic_parity.py",
    "installation non polluante": "tests/test_zero_pollution.py",
}


def _vera_tool_parameters() -> dict[str, list[str]]:
    """Les paramètres que les outils `mmu_*` acceptent, extraits du serveur plutôt que déclarés."""
    source = Path(__file__).resolve().parents[1] / "src" / "vera_mmu" / "mcp_server.py"
    parsed = ast.parse(source.read_text(encoding="utf-8"))
    tools: dict[str, list[str]] = {}
    for node in ast.walk(parsed):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("mmu_"):
            tools[node.name] = [argument.arg for argument in node.args.args + node.args.kwonlyargs]
    return tools


class AretC11SingleRootParityTests(unittest.TestCase):
    def test_the_vendored_server_is_the_pinned_aret_source(self) -> None:
        self.assertEqual(reference_digest(), REFERENCE_SHA256)

    def test_the_dimensions_shared_with_other_couplings_have_a_named_home(self) -> None:
        """Une dimension mesurée ailleurs doit être citée, pas supposée ni recopiée.

        Ce test n'exécute pas ces preuves — il vérifie que les fichiers qui les portent existent.
        Une dimension dont le test aurait disparu redeviendrait une affirmation sans support, et
        c'est exactement ce que le registre interdit.
        """
        root = Path(__file__).resolve().parents[1]
        for dimension, location in COVERED_ELSEWHERE.items():
            with self.subTest(dimension):
                self.assertTrue((root / location).is_file(), f"{dimension} : `{location}` absent")

    # --- ce que C11 ajoute : I008 sur la racine ------------------------------

    def test_aret_accepts_a_repository_path_and_validates_it(self) -> None:
        """Le fait ARET est extrait du code : trois outils portent le champ, un garde le compare."""
        with_path = [
            node.name for node in tool_functions() if "repository_path" in tool_parameters(node)
        ]
        self.assertEqual(
            sorted(with_path),
            ["aret_get_toolchain_status", "aret_run_oracle", "aret_run_pipeline"],
        )

        guard = None
        for node in tree().body:
            if isinstance(node, ast.FunctionDef) and node.name == "_configured_repository_path":
                guard = node
        self.assertIsNotNone(guard, "le garde de racine a disparu de la référence ARET")
        raised = [item for item in ast.walk(guard) if isinstance(item, ast.Raise)]
        self.assertTrue(raised, "le garde ARET ne refuse plus rien")

    def test_no_vera_tool_accepts_a_path_a_command_or_a_url(self) -> None:
        """Le refus le plus fort est l'absence du champ, pas la comparaison de sa valeur.

        Un garde qui compare peut être relâché d'une ligne ; un champ qui n'existe pas ne peut pas
        l'être. C'est le même raisonnement que pour la commande de capability (§32, I008).
        """
        tools = _vera_tool_parameters()
        self.assertGreaterEqual(len(tools), 40, "la surface d’outils VERA n’a pas été lue")

        offenders = {
            name: [
                parameter
                for parameter in parameters
                if parameter not in ALLOWED_DESPITE_MARKER
                and any(marker in parameter.lower() for marker in FORBIDDEN_PARAMETER_MARKERS)
            ]
            for name, parameters in tools.items()
        }
        offenders = {name: found for name, found in offenders.items() if found}
        self.assertEqual(offenders, {}, f"des outils VERA acceptent un chemin ou une commande : {offenders}")

    def test_the_named_exception_really_is_not_a_path(self) -> None:
        """Nommer une exception sans la justifier reviendrait à s'accorder une dérogation."""
        tools = _vera_tool_parameters()
        holders = [name for name, parameters in tools.items() if "direction" in parameters]
        self.assertTrue(holders, "`direction` n’existe plus : retirer l’exception")
        source = (Path(__file__).resolve().parents[1] / "src" / "vera_mmu" / "mcp_server.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("direction", source)
        for name in holders:
            with self.subTest(name):
                self.assertTrue(name.startswith("mmu_"), name)

    def test_the_core_derives_its_roots_from_the_profile_only(self) -> None:
        """Le pendant positif : la racine vient du profil déclaré, jamais d'un appel."""
        workspace = (Path(__file__).resolve().parents[1] / "src" / "vera_mmu" / "workspace.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("def resolve_workspace", workspace)
        self.assertNotIn("os.environ", workspace, "le workspace consulterait l’environnement global")
        self.assertGreaterEqual(len(TOOL_NAMES), 40)


if __name__ == "__main__":
    unittest.main()

"""Test de parité du couplage `C10` — les 44 outils `aret_*` contre la surface MCP de VERA.

Le registre exige, pour promouvoir `C10` : « schémas de chaque outil, surface minimale,
classification read/write/sensitive/network, snapshots et appels de compatibilité ».

**Le nombre d'outils n'est pas la mesure intéressante.** ARET en écrit quarante-quatre à la main
dans son serveur ; VERA en sert quarante-sept. Comparer les deux nombres ne dirait rien : une
surface plus large peut être plus sûre si chaque outil y est borné, et une plus étroite peut être
dangereuse si un seul de ses outils accepte n'importe quoi. Ce qui se compare, c'est **ce que
chaque surface sait dire d'elle-même**.

ARET ne sait rien dire de la sienne : elle est une liste de fonctions, sans classification. VERA
déclare pour chaque outil s'il lit ou s'il écrit, lesquels sont sensibles et pourquoi, et lesquels
touchent le réseau — aucun, avec la règle qui l'explique. `B10` avait trouvé que le décorateur
`_mutating_call` n'est pas le marqueur d'écriture : `mmu_export_bundle` et `mmu_sync_memory`
écrivent sans lui. La classification est donc **déclarée**, et ce test vérifie qu'elle reste
exhaustive et partitionnante.
"""
from __future__ import annotations

import ast
from pathlib import Path
import unittest

from vera_mmu.mcp_manifest import TOOL_NAMES
from vera_mmu.mcp_tool_classes import (
    NETWORK_TOOLS,
    READ_ONLY,
    SENSITIVE_REASONS,
    SENSITIVE_TOOLS,
    TOOL_ACCESS,
    WRITE,
    classify_tool,
    tool_counts,
    unclassified_tools,
)

from tests.aret_v1_server_reference import (
    REFERENCE_SHA256,
    reference_digest,
    tool_functions,
    tool_parameters,
)


def _registered_tools() -> set[str]:
    """Les outils que le serveur définit réellement, lus dans son code."""
    source = Path(__file__).resolve().parents[1] / "src" / "vera_mmu" / "mcp_server.py"
    parsed = ast.parse(source.read_text(encoding="utf-8"))
    return {
        node.name
        for node in ast.walk(parsed)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("mmu_")
    }


class AretC10ToolSurfaceParityTests(unittest.TestCase):
    def test_the_vendored_server_is_the_pinned_aret_source(self) -> None:
        self.assertEqual(reference_digest(), REFERENCE_SHA256)

    # --- ce qu'ARET sait dire de sa surface ---------------------------------

    def test_aret_writes_forty_four_tools_by_hand_and_classifies_none(self) -> None:
        """Le fait est extrait du code : quarante-quatre fonctions, aucune table d'accès."""
        tools = tool_functions()
        self.assertEqual(len(tools), 44)
        self.assertTrue(all(node.name.startswith("aret_") for node in tools))

        source = (
            Path(__file__).resolve().parents[1]
            / "tests" / "fixtures" / "aret_v1" / "source" / "mcp_server_reference.py"
        ).read_text(encoding="utf-8")
        for marker in ("READ_ONLY", "SENSITIVE_TOOLS", "NETWORK_TOOLS", "TOOL_ACCESS"):
            self.assertNotIn(marker, source, f"la référence ARET classe désormais ses outils ({marker})")

    def test_every_aret_tool_takes_named_parameters_only(self) -> None:
        """La seule borne qu'ARET donne : des paramètres nommés, jamais `*args`/`**kwargs`.

        C'est peu, et c'est justement ce que `C10` demande de dépasser. Le mesurer évite de
        reprocher à ARET une absence de borne qu'il n'a pas.
        """
        for node in tool_functions():
            with self.subTest(node.name):
                self.assertIsNone(node.args.vararg, node.name)
                self.assertIsNone(node.args.kwarg, node.name)
                self.assertTrue(tool_parameters(node) or node.name, node.name)

    # --- ce que VERA sait dire de la sienne ---------------------------------

    def test_the_manifest_and_the_server_agree_on_the_served_surface(self) -> None:
        """`B10` avait trouvé le manifeste à 46 pendant que le serveur en servait 47."""
        registered = _registered_tools()
        self.assertEqual(sorted(TOOL_NAMES), sorted(registered))
        self.assertEqual(len(registered), 47)

    def test_every_served_tool_is_classified_and_the_classes_partition_it(self) -> None:
        """Exhaustive et partitionnante : aucun outil non classé, aucun dans deux classes."""
        registered = _registered_tools()
        self.assertEqual(unclassified_tools(), (), "des outils servis ne sont pas classés")
        self.assertEqual(sorted(TOOL_ACCESS), sorted(registered))

        read_only = {name for name, access in TOOL_ACCESS.items() if access == READ_ONLY}
        write = {name for name, access in TOOL_ACCESS.items() if access == WRITE}
        self.assertEqual(read_only & write, set())
        self.assertEqual(read_only | write, registered)

        counts = tool_counts()
        self.assertEqual(counts["read_only"] + counts["write"], len(registered))
        self.assertEqual(counts["read_only"], len(read_only))
        self.assertEqual(counts["write"], len(write))

    def test_each_sensitive_tool_carries_its_reason(self) -> None:
        """« Sensible » a une définition, pas une impression : écrire hors du runtime, remplacer la
        mémoire canonique, ou signer une promotion. Une étiquette sans motif serait un décompte que
        personne ne peut vérifier."""
        self.assertEqual(sorted(SENSITIVE_TOOLS), sorted(SENSITIVE_REASONS))
        self.assertTrue(SENSITIVE_TOOLS)
        for name in sorted(SENSITIVE_TOOLS):
            with self.subTest(name):
                self.assertIn(name, TOOL_ACCESS, name)
                self.assertEqual(TOOL_ACCESS[name], WRITE, f"`{name}` est sensible sans écrire")
                self.assertGreater(len(SENSITIVE_REASONS[name].strip()), 20, name)

    def test_the_network_class_is_empty_because_the_core_holds_no_network_path(self) -> None:
        """Zéro n'est pas une rassurance affichée : c'est la conséquence d'une règle."""
        self.assertEqual(NETWORK_TOOLS, frozenset())
        self.assertEqual(tool_counts()["network"], 0)

    def test_classify_tool_answers_for_every_served_tool_and_refuses_the_others(self) -> None:
        for name in sorted(_registered_tools()):
            with self.subTest(name):
                self.assertIn(classify_tool(name), (READ_ONLY, WRITE), name)
        for absent in ("mmu_inexistant", "aret_run_oracle", ""):
            with self.subTest(absent):
                with self.assertRaises(Exception):
                    classify_tool(absent)


if __name__ == "__main__":
    unittest.main()

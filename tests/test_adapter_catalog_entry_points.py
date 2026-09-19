"""Le catalogue d'adapters : ses entry points existent-ils réellement ?

`ADAPTER_CATALOG` ne tient que des chaînes `module:fonction`, résolues au moment de l'appel par
un `getattr`. Rien, ni à l'import ni au build, ne vérifiait qu'elles désignaient quelque chose.

**Mesuré le 19 septembre 2026 sur la CLI livrée** (`vmmu`, sha256 `6c75e49b…`, révision source
`4a24b800`) : `vmmu install --adapter claude-code-local` sortait en traceback

    AttributeError: module 'vera_mmu.claude_code_local' has no attribute
    'claude_code_local_config_main'. Did you mean: 'claude_code_local_hook_main'?

Deux des douze entrées — les deux de `claude-code-local`, l'adapter phare, celui que la
documentation d'installation donne en premier — nommaient des fonctions jamais écrites. Aucun
fichier de `tests/` ne mentionnait `adapter_catalog` : le module entier était hors mesure, et
c'est exactement pourquoi un registre de découplage vert n'a rien vu. Une capacité que
personne n'exerce n'est pas une capacité attestée.

Ce fichier ferme les deux trous d'un coup :

* les douze entrées se résolvent (`test_every_catalog_entry_point_resolves`) ;
* et une entrée qui ne se résout pas **refuse** au lieu de se planter, pour que le contrat JSON
  `{"ok": false, "error": …}` de la CLI tienne aussi quand le catalogue ment (I014).
"""
from __future__ import annotations

import importlib
import inspect
import unittest

from vera_mmu.adapter_catalog import ADAPTER_CATALOG, AdapterSpec, call_adapter, resolve_adapter_entry
from vera_mmu.store import StoreError


#: Les deux champs du catalogue qui nomment une fonction à appeler.
ENTRY_FIELDS = ("stage_entry", "configure_entry")


class AdapterCatalogEntryPointTests(unittest.TestCase):
    """Ce que le catalogue promet doit exister, et son échec doit rester un refus."""

    def test_every_catalog_entry_point_resolves(self) -> None:
        """Les douze entrées, une par une, avec le nom fautif dans le message d'échec.

        `subTest` est délibéré : une seule assertion globale dirait « le catalogue est cassé »
        sans dire laquelle des douze, ce qui est précisément l'information qui manquait.
        """
        self.assertEqual(len(ADAPTER_CATALOG), 6)
        for adapter, spec in sorted(ADAPTER_CATALOG.items()):
            self.assertIsInstance(spec, AdapterSpec)
            for field in ENTRY_FIELDS:
                entry = getattr(spec, field)
                with self.subTest(adapter=adapter, champ=field, entry=entry):
                    module_name, function_name = entry.split(":", 1)
                    module = importlib.import_module(module_name)
                    self.assertTrue(
                        hasattr(module, function_name),
                        f"`{entry}` est déclaré par le catalogue mais n’existe pas dans {module_name}",
                    )
                    self.assertTrue(callable(getattr(module, function_name)))

    def test_every_entry_point_accepts_the_argument_list_the_cli_sends(self) -> None:
        """Résoudre ne suffit pas : `__main__` envoie une liste d'arguments, pas rien.

        `call_adapter` appelle `function(args)` avec une liste positionnelle. Une fonction qui
        se résout mais n'accepte pas un argument positionnel casserait au même endroit, une
        ligne plus bas — le défaut mesuré, déplacé plutôt que corrigé.
        """
        for adapter, spec in sorted(ADAPTER_CATALOG.items()):
            for field in ENTRY_FIELDS:
                entry = getattr(spec, field)
                with self.subTest(adapter=adapter, champ=field):
                    signature = inspect.signature(resolve_adapter_entry(entry))
                    positional = [
                        parameter
                        for parameter in signature.parameters.values()
                        if parameter.kind
                        in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD, parameter.VAR_POSITIONAL)
                    ]
                    self.assertTrue(positional, f"`{entry}` n’accepte aucun argument positionnel")

    def test_i014_a_missing_entry_point_refuses_instead_of_crashing(self) -> None:
        """Le défaut mesuré sortait du contrat JSON : c'est ça qu'on épingle, pas seulement le nom.

        Corriger les deux fonctions manquantes sans corriger la barrière laisserait la prochaine
        entrée fautive ressortir en traceback. `StoreError` est le seul type que `__main__`
        intercepte pour rendre `{"ok": false, "error": …}`.
        """
        with self.assertRaises(StoreError) as absent:
            resolve_adapter_entry("vera_mmu.claude_code_local:fonction_jamais_ecrite")
        self.assertIn("fonction_jamais_ecrite", str(absent.exception))

        with self.assertRaises(StoreError):
            resolve_adapter_entry("vera_mmu.module_inexistant:quoi_que_ce_soit")

        # Et par la voie réellement empruntée par la CLI, pas seulement par le résolveur.
        with self.assertRaises(StoreError):
            call_adapter("vera_mmu.claude_code_local:fonction_jamais_ecrite", ["--profile", "x"])

    def test_the_local_adapter_is_the_one_the_compiler_binds(self) -> None:
        """Le staging local doit compiler sur la liaison que `mcp_compiler` atteste.

        Si les deux divergeaient, `vmmu compile --adapter claude-code-local` et
        `vmmu install --adapter claude-code-local` produiraient deux plans différents — un
        artefact livré lié à un autre build, exactement la dérive silencieuse que I014 interdit.
        """
        from vera_mmu.claude_code_local import CLAUDE_CODE_LOCAL_BINDING
        from vera_mmu.mcp_compiler import _ADAPTER_BINDINGS

        self.assertEqual(CLAUDE_CODE_LOCAL_BINDING, _ADAPTER_BINDINGS["claude-code-local"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

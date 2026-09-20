"""La configuration écrite par `install` désigne-t-elle des commandes qui existent ?

**Le défaut mesuré, sur les artefacts de release du run #72.** `install --adapter
claude-code-local` écrivait dans `.mcp.json` la commande `vmmu-claude-code-local-mcp`, et dans
`.claude/settings.json` six hooks appelant `vmmu-claude-code-local-hook`. Ce sont des scripts
console déclarés dans `pyproject.toml` : ils n'existent **qu'après un `pip install`**.

Or aucun artefact de release ne les embarque. L'archive CLI ne contient que `vmmu` et son
manifest ; le paquet `.deb` ne contient que `vera-mmu-desktop` et `vmmu-desktop-bridge`. Depuis
la release, l'hôte n'aurait donc jamais pu démarrer le serveur MCP ni exécuter un seul hook.

**Et trois diagnostics se contredisaient sur la même installation :**

* `doctor` → `PASS`, « 1 intégration déclarée et **installée** project-local » ;
* `adapter doctor` → `ok: true`, `CONFIGURED` ;
* `configure --adapter claude-code-local` → `DEGRADED`, `hook_entrypoint: MISSING`,
  `mcp_entrypoint: MISSING`.

Seul le troisième disait vrai, et il passe par `inspect_claude_code_local` — dont l'unique
appelant est l'entry point écrit le jour même. Avant cela, cette détection était **inatteignable**.

Écrire une configuration qui ne peut pas fonctionner puis se déclarer sain est exactement le
défaut que ce produit existe pour empêcher. Ce fichier ferme les deux moitiés : la résolution
rend la release autonome, et le refus empêche d'écrire ce qu'on ne sait pas lancer.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from vera_mmu.claude_code_local import (
    HOOK_ENTRYPOINT,
    HOOK_SUBCOMMAND,
    MCP_ENTRYPOINT,
    MCP_SUBCOMMAND,
    ClaudeCodeLocalError,
    _require_resolvable_entrypoints,
    entrypoint_status,
    resolve_entrypoint,
)


def _absent(_: str) -> None:
    """Une machine où aucun script console VERA n'est installé — le cas de la release."""
    return None


def _present(name: str) -> str:
    """Une machine où `pip install` a posé les scripts console."""
    return f"/usr/local/bin/{name}"


class AdapterEntrypointReachabilityTests(unittest.TestCase):
    """Ce qui est écrit doit pouvoir être lancé, et le contraire doit être refusé."""

    def test_the_console_script_is_preferred_when_it_exists(self) -> None:
        """Ne pas casser les installations `pip` déjà en place est une contrainte, pas un détail.

        Y réécrire un chemin de binaire changerait une configuration qui fonctionnait.
        """
        self.assertEqual(
            resolve_entrypoint(MCP_ENTRYPOINT, MCP_SUBCOMMAND, command_lookup=_present), MCP_ENTRYPOINT
        )
        self.assertEqual(
            resolve_entrypoint(HOOK_ENTRYPOINT, HOOK_SUBCOMMAND, command_lookup=_present), HOOK_ENTRYPOINT
        )

    def test_without_the_console_script_nothing_is_invented(self) -> None:
        """Hors gel et sans script console, la résolution rend `None` plutôt qu'un nom d'espoir.

        La suite de tests tourne sous un interpréteur Python ordinaire, donc `sys.frozen` est
        faux : c'est exactement la branche où une commande inventée serait le plus tentante.
        """
        self.assertIsNone(resolve_entrypoint(MCP_ENTRYPOINT, MCP_SUBCOMMAND, command_lookup=_absent))
        self.assertIsNone(resolve_entrypoint(HOOK_ENTRYPOINT, HOOK_SUBCOMMAND, command_lookup=_absent))

    def test_the_status_reports_both_entrypoints_from_a_single_source(self) -> None:
        """Diagnostic et installation doivent lire la même chose, sinon l'un ment sur l'autre."""
        present = entrypoint_status(command_lookup=_present)
        self.assertEqual(sorted(present), ["hook", "mcp"])
        self.assertEqual(present["mcp"], MCP_ENTRYPOINT)
        absent = entrypoint_status(command_lookup=_absent)
        self.assertIsNone(absent["hook"])
        self.assertIsNone(absent["mcp"])

    def test_install_refuses_to_write_a_configuration_it_cannot_launch(self) -> None:
        """Le cœur : le refus arrive **avant** la première écriture, et nomme ce qui manque.

        Un refus qui tait la commande absente obligerait à ouvrir le code pour comprendre, ce que
        ce dépôt a déjà corrigé ailleurs.
        """
        with self.assertRaises(ClaudeCodeLocalError) as refuse:
            _require_resolvable_entrypoints(command_lookup=_absent)
        message = str(refuse.exception)
        self.assertIn(HOOK_ENTRYPOINT, message)
        self.assertIn(MCP_ENTRYPOINT, message)
        # Et il dit quoi faire, plutôt que de constater.
        self.assertIn("pip install", message)

    def test_install_proceeds_when_both_commands_resolve(self) -> None:
        """Le refus doit être étroit : sur une machine équipée, il ne doit rien bloquer."""
        _require_resolvable_entrypoints(command_lookup=_present)  # ne lève pas

    def test_a_single_missing_command_is_enough_to_refuse(self) -> None:
        """Un hôte à moitié équipé est un hôte cassé, pas un hôte acceptable."""
        def hook_seul(name: str) -> str | None:
            return _present(name) if name == HOOK_ENTRYPOINT else None

        with self.assertRaises(ClaudeCodeLocalError) as refuse:
            _require_resolvable_entrypoints(command_lookup=hook_seul)
        message = str(refuse.exception)
        self.assertIn(MCP_ENTRYPOINT, message)
        self.assertNotIn(HOOK_ENTRYPOINT, message)

    def test_install_itself_refuses_and_writes_nothing(self) -> None:
        """Le test qui manquait, et qu'une mutation a révélé.

        Les cas ci-dessus exercent `_require_resolvable_entrypoints` **directement** : neutraliser
        son appel dans `install_claude_code_local` ne faisait donc rien tomber. Une propriété
        vérifiée par une autre route que celle du produit ne prouve rien du produit.

        Ce test passe par `install` et vérifie les deux moitiés : le refus, et l'absence
        d'écriture. Refuser après avoir écrit laisserait justement la configuration inopérante que
        tout ceci vise à empêcher.
        """
        from tests.playbook_fixture import write_playbook
        from vera_mmu.capabilities import CapabilityService
        from vera_mmu.capability_contracts import CapabilityContractService
        from vera_mmu.capability_policies import CapabilityPolicyService
        from vera_mmu.claude_code_integration import compile_claude_code_integration_plan
        from vera_mmu.claude_code_local import compile_claude_code_local_plan, install_claude_code_local
        from vera_mmu.identity import load_profile
        from vera_mmu.lifecycle_adapters import compile_lifecycle_adapter_plan
        from vera_mmu.mcp_hooks import compile_mcp_hook_plan
        from vera_mmu.mcp_instructions import compile_mcp_instructions
        from vera_mmu.mcp_integration import compile_mcp_integration
        from vera_mmu.mcp_manifest import compile_mcp_manifest
        from vera_mmu.store import MemoryStore

        profil = """
mmu:
  version: "2.0"
project:
  id: "entrypoint-check"
  name: "Entrypoint Check"
  domain: "generic"
workspace:
  root: "."
storage:
  memory_dir: ".vera-mmu"
  sqlite_file: "memory.sqlite"
  artifacts_dir: "artifacts"
identity:
  include_vcs_revision: false
  include_profile_hash: true
"""
        with TemporaryDirectory() as repertoire:
            racine = Path(repertoire)
            chemin = racine / "project.yaml"
            chemin.write_text(profil, encoding="utf-8")
            write_playbook(chemin)
            with MemoryStore.open(load_profile(chemin), chemin) as store:
                CapabilityService(store).create(
                    "alpha-check", "Check alpha", "CHECK", "1.0.0", actor="test"
                )
                CapabilityContractService(store).declare(
                    "alpha-check", "OBSERVED_PROCESS", "DENY_NETWORK", 30,
                    parameter_schema={"type": "object", "additionalProperties": False}, actor="test",
                )
                CapabilityPolicyService(store).declare("alpha-check", "ALLOW", "test", actor="test")

                manifest = compile_mcp_manifest(store, adapter_bindings={"alpha-check": "adapter-alpha-v1"})
                instructions = compile_mcp_instructions(store, manifest)
                integration = compile_mcp_integration(store, manifest, instructions)
                hooks = compile_mcp_hook_plan(store, manifest, instructions, integration)
                review = compile_claude_code_integration_plan(store, manifest, instructions, integration, hooks)
                lifecycle = compile_lifecycle_adapter_plan(
                    store, manifest, adapter_id="claude-code-local-v1",
                    adapter_version="1.0.0", maximum_guard_mode="HARD",
                )
                plan = compile_claude_code_local_plan(
                    store, manifest, instructions, integration, hooks, review, lifecycle
                )

                # Une machine sans script console et sans CLI gelée : le cas de la release.
                with mock.patch("vera_mmu.claude_code_local.shutil.which", _absent):
                    with self.assertRaises(ClaudeCodeLocalError) as refuse:
                        install_claude_code_local(
                            store, manifest, instructions, integration, hooks, review, lifecycle,
                            plan, confirm=True,
                        )
                self.assertIn(MCP_ENTRYPOINT, str(refuse.exception))

                # Et rien n'a été écrit : ni configuration hôte, ni état d'installation.
                for ecriture in (racine / ".claude" / "settings.json", racine / ".mcp.json"):
                    with self.subTest(fichier=ecriture.name):
                        self.assertFalse(ecriture.exists(), f"{ecriture} a été écrit malgré le refus")

    def test_the_cli_carries_the_two_equivalent_subcommands(self) -> None:
        """La release est autonome parce que la CLI unique porte les deux entrées.

        Sans elles, la résolution n'aurait aucune seconde forme à proposer et le refus
        ci-dessus condamnerait la release au lieu de la réparer.
        """
        from vera_mmu.__main__ import main

        for sous_commande in (HOOK_SUBCOMMAND, MCP_SUBCOMMAND):
            with self.subTest(sous_commande=sous_commande):
                with self.assertRaises(SystemExit) as sortie:
                    main([sous_commande, "--help"])
                self.assertEqual(sortie.exception.code, 0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

"""La configuration MCP que le produit écrit peut-elle démarrer, et le rester ?

Ces règles viennent d'une vérification de bout en bout de la release `v0.1.0-rc.5`, téléchargée
depuis GitHub et exercée telle que livrée — archive CLI et AppImage, jamais les sources. Quatre
défauts de production en sont sortis, tous invisibles depuis le dépôt parce qu'ils ne se voient
qu'en lisant la configuration produite, ou en la relisant plus tard.

**1. Le binaire nommé n'était pas le bon, et son chemin ne survivait pas.** Installé depuis la
fenêtre, `.mcp.json` recevait :

    "command": "/tmp/.mount_VERA-MjDbbJp/usr/bin/vmmu-desktop-bridge claude-code-local-mcp"

Le binaire désigné est le sidecar du bureau, qui ne connaît pas cette sous-commande et réclame
`--project-root` et `--nonce` ; et `/tmp/.mount_…` est le point de montage de l'AppImage, démonté
à la fermeture et renommé à chaque lancement. Toute configuration produite par l'application de
bureau était donc morte-née, définitivement. La cause : `sys.frozen` est vrai dans **tout**
binaire PyInstaller, et le produit en livre deux.

**2. `command` portait une espace.** Ce champ nomme un programme ; `args` porte les arguments. Un
client MCP qui exécute sans shell demandait donc un fichier dont le nom contient une espace :

    [Errno 2] No such file or directory: '…/vmmu claude-code-local-mcp'

**3. Éditer son propre playbook rendait le projet inréparable.** Le produit écrit lui-même, dans
le playbook qu'il génère : « Ce playbook est une proposition initiale. Le projet doit le revoir. »
Le faire suffisait à ce que le serveur déclaré refuse de démarrer — l'état attesté ne correspondait
plus — et `install` refusait ensuite de se corriger : « Conflit : serveur MCP VERA existant
divergent », parce qu'il n'acceptait de remplacer que la forme générique, jamais sa propre trace.

**4. Et rien ne le disait.** Pendant que le serveur était mort, `doctor` rendait PASS sur ses
vingt contrôles, `repair` répondait `NOTHING_TO_REPAIR`, et `conclude` certifiait « Les 18 étapes
sont franchies ». Le contrôle `hooks` se contentait de l'existence de l'un de cinq répertoires,
sans regarder lequel : sur un dépôt réel possédant déjà un `.claude/`, il passait avant même que
VERA n'ait rien écrit.

Les quatre relèvent de la même classe, déjà nommée dans ce dépôt : *une propriété satisfaite par
plus d'un chemin n'en prouve aucun*.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from vera_mmu.claude_code_local import (
    CLI_BINARY_NAME,
    CLI_MARKER_VARIABLE,
    ClaudeCodeLocalError,
    HOOK_SUBCOMMAND,
    MCP_ENTRYPOINT,
    MCP_SUBCOMMAND,
    program_is_launchable,
    resolve_entrypoint,
    resolve_launcher,
)

PROFIL = """
mmu:
  version: "2.0"
project:
  id: "lancable"
  name: "Lancable"
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
integrations:
  enabled:
    - "claude-code-local"
"""


#: Un chemin qui existe réellement, pour que « ce programme est-il lançable ? » se mesure
#: plutôt que se simuler. Substituer `Path.is_file` globalement cassait des contrôles sans
#: rapport — le doctor lit `.gitignore` par la même méthode.
BINAIRE_REEL = str(Path(__file__).resolve())


def _absent(_name: str) -> str | None:
    """Ni script console, ni CLI sur le `PATH` : la machine d'un utilisateur de la release."""
    return None


class _Projet:
    """Un projet réel, ouvert, avec une capability ALLOW — le minimum pour compiler un plan."""

    def __init__(self, repertoire: Path) -> None:
        from tests.playbook_fixture import write_playbook
        from vera_mmu.capabilities import CapabilityService
        from vera_mmu.capability_contracts import CapabilityContractService
        from vera_mmu.capability_policies import CapabilityPolicyService
        from vera_mmu.identity import load_profile
        from vera_mmu.store import MemoryStore

        self.racine = repertoire
        self.chemin = repertoire / "project.yaml"
        self.chemin.write_text(PROFIL, encoding="utf-8")
        write_playbook(self.chemin)
        self.store = MemoryStore.open(load_profile(self.chemin), self.chemin)
        CapabilityService(self.store).create("alpha-check", "Check alpha", "CHECK", "1.0.0", actor="t")
        CapabilityContractService(self.store).declare(
            "alpha-check", "OBSERVED_PROCESS", "DENY_NETWORK", 30,
            parameter_schema={"type": "object", "additionalProperties": False}, actor="t",
        )
        CapabilityPolicyService(self.store).declare("alpha-check", "ALLOW", "t", actor="t")

    def plan(self):
        from vera_mmu.claude_code_integration import compile_claude_code_integration_plan
        from vera_mmu.claude_code_local import compile_claude_code_local_plan
        from vera_mmu.lifecycle_adapters import compile_lifecycle_adapter_plan
        from vera_mmu.mcp_hooks import compile_mcp_hook_plan
        from vera_mmu.mcp_instructions import compile_mcp_instructions
        from vera_mmu.mcp_integration import compile_mcp_integration
        from vera_mmu.mcp_manifest import compile_mcp_manifest

        manifest = compile_mcp_manifest(self.store, adapter_bindings={"alpha-check": "claude-code-local-deny-v1"})
        instructions = compile_mcp_instructions(self.store, manifest)
        integration = compile_mcp_integration(self.store, manifest, instructions)
        hooks = compile_mcp_hook_plan(self.store, manifest, instructions, integration)
        review = compile_claude_code_integration_plan(self.store, manifest, instructions, integration, hooks)
        lifecycle = compile_lifecycle_adapter_plan(
            self.store, manifest, adapter_id="claude-code-local-v1",
            adapter_version="1.0.0", maximum_guard_mode="HARD",
        )
        plan = compile_claude_code_local_plan(self.store, manifest, instructions, integration, hooks, review, lifecycle)
        return manifest, instructions, integration, hooks, review, lifecycle, plan

    def installer(self):
        from vera_mmu.claude_code_local import install_claude_code_local

        return install_claude_code_local(self.store, *self.plan(), confirm=True)

    def close(self) -> None:
        self.store.close()


class LauncherShapeTests(unittest.TestCase):
    """`command` nomme un programme ; la sous-commande appartient à `args`."""

    def test_the_launcher_is_a_pair_never_a_line_to_split(self) -> None:
        with mock.patch("vera_mmu.claude_code_local.shutil.which", lambda nom: f"/usr/bin/{nom}"):
            lanceur = resolve_launcher(MCP_ENTRYPOINT, MCP_SUBCOMMAND)
        self.assertIsNotNone(lanceur)
        programme, arguments = lanceur
        self.assertEqual(programme, MCP_ENTRYPOINT)
        self.assertEqual(arguments, ())

    def test_the_program_never_carries_a_space_even_when_a_subcommand_is_needed(self) -> None:
        """Le cœur du défaut n°2 : une espace dans `command` est un `ENOENT` garanti."""
        binaire = BINAIRE_REEL
        with mock.patch("vera_mmu.claude_code_local.shutil.which", lambda nom: binaire if nom == CLI_BINARY_NAME else None):
            lanceur = resolve_launcher(MCP_ENTRYPOINT, MCP_SUBCOMMAND)
        self.assertEqual(lanceur, (binaire, (MCP_SUBCOMMAND,)))
        self.assertNotIn(" ", lanceur[0])

    def test_the_shell_form_quotes_with_double_quotes_on_every_platform(self) -> None:
        """Les hooks prennent bien une ligne de shell — encore faut-il que le shell la lise.

        Mesuré sur le runner Windows : `shlex.quote`, d'abord employé ici, applique les règles
        POSIX et entoure de guillemets **simples** tout ce qui contient une contre-oblique,
        c'est-à-dire tout chemin Windows. `cmd.exe` ne reconnaît pas ce guillemet comme une
        citation. Le défaut était dans le produit, pas dans le test : la commande de hook
        générée sous Windows aurait été illisible.

        Le test compare donc à la forme attendue, et non au résultat de `shlex.split`, qui
        n'aurait fait que redire les conventions POSIX sur une plateforme qui ne les suit pas.
        """
        avec_espace = str(Path("/opt/mon dossier/vmmu"))
        with mock.patch(
            "vera_mmu.claude_code_local.shutil.which",
            lambda nom: avec_espace if nom == CLI_BINARY_NAME else None,
        ):
            ligne = resolve_entrypoint(MCP_ENTRYPOINT, HOOK_SUBCOMMAND)
        self.assertEqual(ligne, f'"{avec_espace}" {HOOK_SUBCOMMAND}')
        self.assertNotIn("'", ligne)

        # Et sans espace, aucun guillemet inutile : une citation de trop se lit comme un nom.
        sans_espace = BINAIRE_REEL
        with mock.patch(
            "vera_mmu.claude_code_local.shutil.which",
            lambda nom: sans_espace if nom == CLI_BINARY_NAME else None,
        ):
            ligne = resolve_entrypoint(MCP_ENTRYPOINT, HOOK_SUBCOMMAND)
        self.assertEqual(ligne, f"{sans_espace} {HOOK_SUBCOMMAND}")

    def test_the_installed_server_puts_the_subcommand_in_args_not_in_command(self) -> None:
        """Mesuré sur le produit, pas sur l'assistant : ce que `install` écrit réellement."""
        binaire = BINAIRE_REEL
        with TemporaryDirectory() as repertoire:
            projet = _Projet(Path(repertoire))
            try:
                with mock.patch(
                    "vera_mmu.claude_code_local.shutil.which",
                    lambda nom: binaire if nom == CLI_BINARY_NAME else None,
                ):
                    projet.installer()
                declare = json.loads((projet.racine / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]
            finally:
                projet.close()
        (serveur,) = declare.values()
        self.assertEqual(serveur["command"], binaire)
        self.assertNotIn(" ", serveur["command"])
        self.assertEqual(serveur["args"][0], MCP_SUBCOMMAND)
        self.assertIn("--profile", serveur["args"])


class CliBinaryIdentityTests(unittest.TestCase):
    """Un binaire gelé n'est pas la CLI VERA du seul fait d'être gelé."""

    @staticmethod
    def _paquet(repertoire: Path, *noms: str) -> Path:
        """Fabrique un répertoire d'installation contenant réellement les binaires nommés.

        Des fichiers plutôt qu'un `Path.is_file` substitué : la substitution globale rendait vrai
        pour *tout* chemin, y compris celui d'une CLI voisine qui n'existe pas — le test aurait
        alors mesuré le contraire de ce qu'il annonce. Elle cassait aussi des contrôles sans
        rapport, le doctor lisant `.gitignore` par la même méthode.
        """
        repertoire.mkdir(parents=True, exist_ok=True)
        for nom in noms:
            (repertoire / nom).write_bytes(b"\x7fELF")
        return repertoire

    def test_a_frozen_process_that_is_not_the_cli_is_refused(self) -> None:
        """Le défaut n°1 : le sidecar du bureau se prenait pour la CLI.

        Sans la marque, `sys.frozen` seul faisait rendre `sys.executable` — c'est-à-dire, depuis
        l'application de bureau, le chemin de `vmmu-desktop-bridge`.

        Le binaire doit **exister** pendant la mesure, et une mutation l'a montré : la première
        version de ce test nommait un chemin absent, si bien que retirer la marque ne faisait
        rien tomber — `is_file()` refusait déjà, pour une tout autre raison que celle mesurée.

        Le paquet ne contient ici que le sidecar : c'est le cas d'une installation de bureau
        antérieure à l'embarquement de la CLI, et c'est celui qui doit être refusé.
        """
        from vera_mmu import claude_code_local

        environnement = {cle: valeur for cle, valeur in os.environ.items() if cle != CLI_MARKER_VARIABLE}
        with TemporaryDirectory() as repertoire:
            paquet = self._paquet(Path(repertoire) / "bin", "vmmu-desktop-bridge")
            with mock.patch.object(claude_code_local.sys, "frozen", True, create=True), \
                 mock.patch.object(claude_code_local.sys, "executable", str(paquet / "vmmu-desktop-bridge")), \
                 mock.patch.dict(os.environ, environnement, clear=True):
                self.assertIsNone(claude_code_local._cli_binary(command_lookup=_absent))

    def test_the_desktop_package_now_carries_the_cli_beside_its_sidecar(self) -> None:
        """Ce que l'embarquement rouvre : la fenêtre peut de nouveau installer un MCP.

        Sur une installation `.deb` les deux binaires atterrissent dans `/usr/bin`, donc le
        `PATH` suffirait ; sur Windows, le répertoire d'installation n'y est presque jamais, et
        sans cette recherche l'application ne verrait pas la CLI qu'elle transporte.
        """
        from vera_mmu import claude_code_local

        environnement = {cle: valeur for cle, valeur in os.environ.items() if cle != CLI_MARKER_VARIABLE}
        with TemporaryDirectory() as repertoire:
            paquet = self._paquet(Path(repertoire) / "bin", "vmmu-desktop-bridge", "vmmu")
            with mock.patch.object(claude_code_local.sys, "frozen", True, create=True), \
                 mock.patch.object(claude_code_local.sys, "executable", str(paquet / "vmmu-desktop-bridge")), \
                 mock.patch.dict(os.environ, environnement, clear=True):
                self.assertEqual(
                    claude_code_local._cli_binary(command_lookup=_absent), str(paquet / "vmmu")
                )

    def test_the_embedded_cli_wins_over_an_unrelated_one_on_the_path(self) -> None:
        """Entre deux CLI, celle du même paquet porte la même version, donc le même plan."""
        from vera_mmu import claude_code_local

        with TemporaryDirectory() as repertoire:
            paquet = self._paquet(Path(repertoire) / "bin", "vmmu-desktop-bridge", "vmmu")
            with mock.patch.object(claude_code_local.sys, "frozen", True, create=True), \
                 mock.patch.object(claude_code_local.sys, "executable", str(paquet / "vmmu-desktop-bridge")):
                self.assertEqual(
                    claude_code_local._cli_binary(command_lookup=lambda _n: "/usr/bin/vmmu"),
                    str(paquet / "vmmu"),
                )

    def test_the_cli_that_declares_itself_is_accepted(self) -> None:
        from vera_mmu import claude_code_local

        with TemporaryDirectory() as repertoire:
            paquet = self._paquet(Path(repertoire) / "bin", "vmmu")
            with mock.patch.object(claude_code_local.sys, "frozen", True, create=True), \
                 mock.patch.object(claude_code_local.sys, "executable", str(paquet / "vmmu")), \
                 mock.patch.dict(os.environ, {CLI_MARKER_VARIABLE: "1"}):
                self.assertEqual(claude_code_local._cli_binary(command_lookup=_absent), str(paquet / "vmmu"))

    def test_an_ephemeral_mount_path_is_refused_even_when_it_is_really_the_cli(self) -> None:
        """L'autre moitié du défaut n°1 : le chemin doit survivre au processus qui l'écrit.

        Une AppImage monte son contenu sous `/tmp/.mount_<nom><aléa>`, démonte à la sortie et
        tire un nouveau nom au lancement suivant. Une configuration qui le nomme fonctionne
        exactement tant que personne ne la relit. Embarquer la CLI dans le paquet **ne change
        rien à ce cas** : elle y est bien, mais à un endroit qui disparaîtra.
        """
        from vera_mmu import claude_code_local

        with mock.patch.object(claude_code_local.sys, "frozen", True, create=True), \
             mock.patch.object(claude_code_local.sys, "executable", "/tmp/.mount_VERA-MjDbbJp/usr/bin/vmmu"), \
             mock.patch.dict(os.environ, {CLI_MARKER_VARIABLE: "1"}), \
             mock.patch("vera_mmu.claude_code_local.Path.is_file", lambda self: True):
            self.assertIsNone(claude_code_local._cli_binary(command_lookup=_absent))

    def test_the_refusal_from_an_appimage_names_the_mount_rather_than_the_command(self) -> None:
        """Depuis une AppImage, « commande introuvable » enverrait chercher au mauvais endroit.

        La CLI **est** dans le paquet, visible à l'œil nu. Ce qui manque n'est pas le binaire
        mais un chemin qui lui survive, et c'est cela que le refus doit dire.
        """
        from vera_mmu import claude_code_local

        with mock.patch.object(claude_code_local.sys, "executable", "/tmp/.mount_VERA-abc/usr/bin/vmmu-desktop-bridge"), \
             mock.patch("vera_mmu.claude_code_local.shutil.which", _absent):
            with self.assertRaises(ClaudeCodeLocalError) as refus:
                claude_code_local._require_resolvable_entrypoints()
        message = str(refus.exception)
        self.assertIn("AppImage", message)
        self.assertIn(".deb", message)

    def test_a_path_under_the_running_appimage_is_refused_too(self) -> None:
        from vera_mmu import claude_code_local

        with mock.patch.dict(os.environ, {"APPDIR": "/somewhere/squashfs-root"}):
            self.assertTrue(claude_code_local._is_ephemeral(Path("/somewhere/squashfs-root/usr/bin/vmmu")))
            self.assertFalse(claude_code_local._is_ephemeral(Path("/somewhere/squashfs-rootless/vmmu")))

    def test_the_cli_declares_itself_before_writing_anything(self) -> None:
        """La marque doit être posée par la CLI elle-même, sinon rien ne la distingue.

        Le poser dans un test suffirait à faire passer les cas ci-dessus sans que le produit
        livré le fasse : on vérifie donc que `main` le pose.
        """
        from vera_mmu.__main__ import main

        environnement = {cle: valeur for cle, valeur in os.environ.items() if cle != CLI_MARKER_VARIABLE}
        with mock.patch.dict(os.environ, environnement, clear=True):
            self.assertNotIn(CLI_MARKER_VARIABLE, os.environ)
            with self.assertRaises(SystemExit):
                main(["--aucune-telle-option"])
            self.assertEqual(os.environ.get(CLI_MARKER_VARIABLE), "1")

    def test_launchability_distinguishes_a_path_from_a_bare_name(self) -> None:
        self.assertFalse(program_is_launchable(""))
        self.assertFalse(program_is_launchable("/n/existe/pas/vmmu"))
        self.assertTrue(program_is_launchable(str(Path(__file__))))
        self.assertTrue(program_is_launchable("vmmu-fictif", command_lookup=lambda _n: "/usr/bin/vmmu-fictif"))
        self.assertFalse(program_is_launchable("vmmu-fictif", command_lookup=_absent))


class ReinstallAfterALegitimateEditTests(unittest.TestCase):
    """Le défaut n°3 : éditer son playbook ne doit pas condamner le projet."""

    def test_install_updates_its_own_entry_instead_of_declaring_a_conflict(self) -> None:
        binaire = BINAIRE_REEL
        with TemporaryDirectory() as repertoire:
            projet = _Projet(Path(repertoire))
            try:
                with mock.patch(
                    "vera_mmu.claude_code_local.shutil.which",
                    lambda nom: binaire if nom == CLI_BINARY_NAME else None,
                ):
                    premier = projet.installer()
                    self.assertEqual(premier.status, "INSTALLED")

                    # L'édition que le produit demande explicitement de faire.
                    playbook = projet.racine / ".vera-mmu" / "playbook.md"
                    playbook.write_text(
                        playbook.read_text(encoding="utf-8") + "\n## Règle propre à ce projet\n\nMARQUEUR.\n",
                        encoding="utf-8",
                    )

                    second = projet.installer()
                    self.assertEqual(second.status, "UPDATED")
                    self.assertNotEqual(second.plan_hash, premier.plan_hash)

                    # Et l'état réécrit est bien celui que le serveur relira.
                    from vera_mmu.claude_code_local import _load_installed_plan

                    self.assertEqual(_load_installed_plan(projet.store).plan_hash, second.plan_hash)
            finally:
                projet.close()

    def test_a_foreign_server_and_foreign_hooks_survive_the_update(self) -> None:
        """Mise à jour n'est pas écrasement : mesuré sur un dépôt réel, dont le serveur
        `aret-memory` et les hooks d'un autre outil ont traversé l'installation intacts."""
        binaire = BINAIRE_REEL
        with TemporaryDirectory() as repertoire:
            racine = Path(repertoire)
            (racine / ".mcp.json").write_text(
                json.dumps({"mcpServers": {"autre-outil": {"command": "/usr/bin/autre"}}}), encoding="utf-8"
            )
            (racine / ".claude").mkdir()
            groupe_etranger = {"hooks": [{"command": "/usr/bin/autre-hook", "timeout": 5, "type": "command"}]}
            (racine / ".claude" / "settings.json").write_text(
                json.dumps({"env": {"MCP_TIMEOUT": "120000"}, "hooks": {"PreCompact": [groupe_etranger]}}),
                encoding="utf-8",
            )
            projet = _Projet(racine)
            try:
                with mock.patch(
                    "vera_mmu.claude_code_local.shutil.which",
                    lambda nom: binaire if nom == CLI_BINARY_NAME else None,
                ):
                    projet.installer()
                    playbook = projet.racine / ".vera-mmu" / "playbook.md"
                    playbook.write_text(playbook.read_text(encoding="utf-8") + "\nMARQUEUR\n", encoding="utf-8")
                    projet.installer()

                mcp = json.loads((racine / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]
                reglages = json.loads((racine / ".claude" / "settings.json").read_text(encoding="utf-8"))
            finally:
                projet.close()

        self.assertEqual(mcp["autre-outil"], {"command": "/usr/bin/autre"})
        self.assertEqual(reglages["env"], {"MCP_TIMEOUT": "120000"})
        self.assertIn(groupe_etranger, reglages["hooks"]["PreCompact"])

    def test_vera_replaces_its_own_hook_group_instead_of_stacking_a_second(self) -> None:
        """Deux générations de hooks VERA au même endroit, c'est le hook joué deux fois.

        Une mutation a dicté la forme de ce test. Le cas précédent réinstallait après une édition
        du playbook — or la commande d'un hook ne dépend pas du playbook, donc les groupes
        restaient identiques et l'empilement n'était jamais exercé : neutraliser le remplacement
        ne faisait rien tomber. Ce qui change réellement une commande de hook, c'est la
        **résolution de l'entry point** : d'abord le script console d'un `pip install`, puis, une
        fois celui-ci retiré, la CLI autonome avec sa sous-commande. C'est un parcours ordinaire,
        et c'est celui-ci qu'il fallait exercer.
        """
        binaire = BINAIRE_REEL
        with TemporaryDirectory() as repertoire:
            projet = _Projet(Path(repertoire))
            try:
                if True:
                    # 1. Le script console est là : les hooks le nomment.
                    with mock.patch("vera_mmu.claude_code_local.shutil.which", lambda nom: f"/usr/bin/{nom}"):
                        projet.installer()
                    premiers = json.loads(
                        (projet.racine / ".claude" / "settings.json").read_text(encoding="utf-8")
                    )["hooks"]
                    # 2. Le script console a disparu ; seule la CLI autonome reste.
                    with mock.patch(
                        "vera_mmu.claude_code_local.shutil.which",
                        lambda nom: binaire if nom == CLI_BINARY_NAME else None,
                    ):
                        projet.installer()
                    seconds = json.loads(
                        (projet.racine / ".claude" / "settings.json").read_text(encoding="utf-8")
                    )["hooks"]
            finally:
                projet.close()

        self.assertNotEqual(premiers, seconds, "la commande de hook aurait dû changer")
        for evenement, groupes in seconds.items():
            with self.subTest(evenement=evenement):
                commandes = [
                    str(gestionnaire.get("command", ""))
                    for groupe in groupes
                    for gestionnaire in groupe.get("hooks", [])
                    if HOOK_SUBCOMMAND in str(gestionnaire.get("command", ""))
                    or MCP_ENTRYPOINT.replace("-mcp", "-hook") in str(gestionnaire.get("command", ""))
                ]
                self.assertEqual(len(commandes), 1, f"{len(commandes)} hooks VERA sur {evenement} : {commandes}")
                self.assertTrue(commandes[0].startswith(binaire), commandes[0])

    def test_a_state_written_by_something_else_is_still_refused(self) -> None:
        """La permissivité ne va pas jusqu'à adopter l'état d'un autre produit."""
        binaire = BINAIRE_REEL
        with TemporaryDirectory() as repertoire:
            projet = _Projet(Path(repertoire))
            try:
                etat = projet.racine / ".vera-mmu" / "generated" / "claude-code-local-install.json"
                etat.parent.mkdir(parents=True, exist_ok=True)
                etat.write_text(json.dumps({"autreProduit": {"quelque": "chose"}}), encoding="utf-8")
                with mock.patch(
                    "vera_mmu.claude_code_local.shutil.which",
                    lambda nom: binaire if nom == CLI_BINARY_NAME else None,
                ):
                    with self.assertRaises(ClaudeCodeLocalError) as refus:
                        projet.installer()
                self.assertIn("divergent", str(refus.exception))
            finally:
                projet.close()


class DoctorSeesTheDeadServerTests(unittest.TestCase):
    """Le défaut n°4 : se déclarer sain sur une configuration morte."""

    def test_a_foreign_claude_directory_is_no_longer_taken_for_an_installation(self) -> None:
        from vera_mmu.doctor import _integration_installed

        with TemporaryDirectory() as repertoire:
            racine = Path(repertoire)
            (racine / ".claude").mkdir()
            (racine / ".claude" / "settings.json").write_text("{}", encoding="utf-8")
            # Le `.claude/settings.json` d'un autre outil existe, mais pas le `.mcp.json` :
            # l'adapter Claude local n'est donc pas installé, et le dire est tout le sujet.
            self.assertFalse(_integration_installed(racine, "claude-code-local"))
            (racine / ".mcp.json").write_text("{}", encoding="utf-8")
            self.assertTrue(_integration_installed(racine, "claude-code-local"))

    def test_each_adapter_is_judged_on_its_own_marker(self) -> None:
        """`del adapter` avait rendu le paramètre décoratif : cinq adapters, un seul verdict."""
        from vera_mmu.doctor import _integration_installed

        with TemporaryDirectory() as repertoire:
            racine = Path(repertoire)
            (racine / ".mcp.json").write_text("{}", encoding="utf-8")
            self.assertTrue(_integration_installed(racine, "generic-mcp"))
            self.assertFalse(_integration_installed(racine, "claude-code-local"))

    def test_the_drift_that_kills_the_server_is_reported(self) -> None:
        """Le `.mcp.json` qui ne correspond plus à l'état attesté est un serveur mort."""
        from vera_mmu.doctor import _claude_local_drift

        with TemporaryDirectory() as repertoire:
            racine = Path(repertoire)
            genere = racine / ".vera-mmu" / "generated"
            genere.mkdir(parents=True)
            serveur = {"command": str(Path(__file__)), "args": ["x"], "env": {}}
            (genere / "claude-code-local-install.json").write_text(
                json.dumps({"claudeCodeLocal": {"mcpServer": {"id": "vera-mmu-p", **serveur}}}), encoding="utf-8"
            )

            (racine / ".mcp.json").write_text(json.dumps({"mcpServers": {"vera-mmu-p": serveur}}), encoding="utf-8")
            self.assertIsNone(_claude_local_drift(racine))

            (racine / ".mcp.json").write_text(
                json.dumps({"mcpServers": {"vera-mmu-p": {**serveur, "args": ["y"]}}}), encoding="utf-8"
            )
            self.assertIn("diverge", str(_claude_local_drift(racine)))

            (racine / ".mcp.json").write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
            self.assertIn("ne déclare plus", str(_claude_local_drift(racine)))

    def test_a_vanished_program_is_reported_rather_than_assumed_present(self) -> None:
        """Le cas de l'AppImage refermée : le fichier nommé n'existe plus."""
        from vera_mmu.doctor import _claude_local_drift

        with TemporaryDirectory() as repertoire:
            racine = Path(repertoire)
            genere = racine / ".vera-mmu" / "generated"
            genere.mkdir(parents=True)
            serveur = {"command": "/tmp/.mount_VERA-disparu/usr/bin/vmmu", "args": [], "env": {}}
            (genere / "claude-code-local-install.json").write_text(
                json.dumps({"claudeCodeLocal": {"mcpServer": {"id": "vera-mmu-p", **serveur}}}), encoding="utf-8"
            )
            (racine / ".mcp.json").write_text(json.dumps({"mcpServers": {"vera-mmu-p": serveur}}), encoding="utf-8")
            self.assertIn("introuvable", str(_claude_local_drift(racine)))

    def test_a_missing_attested_state_is_reported(self) -> None:
        from vera_mmu.doctor import _claude_local_drift

        with TemporaryDirectory() as repertoire:
            racine = Path(repertoire)
            (racine / ".mcp.json").write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
            self.assertIn("sans état attesté", str(_claude_local_drift(racine)))

    def test_editing_the_playbook_is_reported_before_the_server_refuses_to_start(self) -> None:
        """Le cas le plus coûteux, et celui que la première correction manquait encore.

        Éditer `.vera-mmu/playbook.md` laisse `.mcp.json` et l'état attesté parfaitement
        cohérents **entre eux** : la première version de ce contrôle, qui ne comparait que ces
        deux fichiers, restait donc verte pendant que le serveur, lui, recompilait son plan au
        démarrage et le refusait. Mesuré sur le binaire reconstruit : serveur `MORT`, `doctor`
        `hooks PASS`. Il fallait comparer les **entrées** dont le plan dérive, pas seulement ce
        qui en a été écrit.
        """
        from vera_mmu.doctor import diagnose_project

        binaire = BINAIRE_REEL
        with TemporaryDirectory() as repertoire:
            projet = _Projet(Path(repertoire))
            try:
                with mock.patch(
                    "vera_mmu.claude_code_local.shutil.which",
                    lambda nom: binaire if nom == CLI_BINARY_NAME else None,
                ):
                    projet.installer()
                chemin = projet.chemin
            finally:
                projet.close()

            sain = {c.name: c for c in diagnose_project(chemin).checks}
            self.assertEqual(sain["hooks"].status, "PASS", sain["hooks"].detail)

            playbook = Path(repertoire) / ".vera-mmu" / "playbook.md"
            playbook.write_text(
                playbook.read_text(encoding="utf-8") + "\n## Règle du projet\n\nMARQUEUR.\n", encoding="utf-8"
            )
            rapport = diagnose_project(chemin)

        controles = {c.name: c for c in rapport.checks}
        self.assertEqual(controles["hooks"].status, "FAIL", controles["hooks"].detail)
        self.assertIn("playbook.md", controles["hooks"].detail)
        self.assertEqual(rapport.status, "FAIL")

    def test_the_whole_doctor_fails_on_a_dead_server_not_just_the_helper(self) -> None:
        """Par la route du produit, pas par la fonction d'aide — une mutation l'a exigé.

        Les cas ci-dessus appellent `_claude_local_drift` directement : neutraliser son **appel**
        dans `_diagnose_hooks` ne faisait donc rien tomber, et le doctor complet serait resté
        aussi aveugle qu'avant. C'est la leçon déjà écrite dans ce dépôt à propos de
        `_require_resolvable_entrypoints` : *une propriété vérifiée par une autre route que celle
        du produit ne prouve rien du produit.*

        Ce test reproduit la situation mesurée sur la release : un projet installé, correct, puis
        un `.mcp.json` qui ne correspond plus — exactement ce que produisait l'édition du
        playbook. Le verdict d'ensemble doit passer à `FAIL`, et le contrôle `hooks` avec lui.
        """
        from vera_mmu.doctor import diagnose_project

        binaire = BINAIRE_REEL
        with TemporaryDirectory() as repertoire:
            projet = _Projet(Path(repertoire))
            try:
                with mock.patch(
                    "vera_mmu.claude_code_local.shutil.which",
                    lambda nom: binaire if nom == CLI_BINARY_NAME else None,
                ):
                    projet.installer()
                chemin = projet.chemin
            finally:
                projet.close()

            # Installé et cohérent : le contrôle `hooks` passe. Sans cette moitié, le test
            # pourrait échouer pour n'importe quelle autre raison et passer pour probant.
            sain = {c.name: c for c in diagnose_project(chemin).checks}
            self.assertEqual(sain["hooks"].status, "PASS", sain["hooks"].detail)

            # Puis la dérive que l'édition du playbook produisait.
            mcp = Path(repertoire) / ".mcp.json"
            charge = json.loads(mcp.read_text(encoding="utf-8"))
            (identifiant,) = charge["mcpServers"]
            charge["mcpServers"][identifiant]["env"]["VERA_MCP_INSTRUCTIONS_HASH"] = "0" * 64
            mcp.write_text(json.dumps(charge), encoding="utf-8")

            rapport = diagnose_project(chemin)
        controles = {c.name: c for c in rapport.checks}
        self.assertEqual(controles["hooks"].status, "FAIL", controles["hooks"].detail)
        self.assertIn("diverge", controles["hooks"].detail)
        self.assertEqual(rapport.status, "FAIL")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()


class StalenessNamesItsCauseTests(unittest.TestCase):
    """Un refus fail-closed doit rester diagnosticable.

    « État d'installation Claude local périmé ou altéré » est correct et sans appel — et ne dit
    pas s'il faut réinstaller, revenir en arrière, ou chercher ailleurs. Rencontré en vérifiant
    l'installation faite depuis le sidecar : la cause était la résolution de l'entry point, et il
    a fallu recompiler le plan à la main sous deux environnements pour la trouver. Même classe
    que les refus de catalogue déjà corrigés ici : *taire ses valeurs oblige à lire le code*.
    """

    def test_an_edited_playbook_is_named_in_the_refusal(self) -> None:
        from vera_mmu.claude_code_local import _load_installed_plan

        binaire = BINAIRE_REEL
        with TemporaryDirectory() as repertoire:
            projet = _Projet(Path(repertoire))
            try:
                with mock.patch(
                    "vera_mmu.claude_code_local.shutil.which",
                    lambda nom: binaire if nom == CLI_BINARY_NAME else None,
                ):
                    projet.installer()
                    playbook = projet.racine / ".vera-mmu" / "playbook.md"
                    playbook.write_text(playbook.read_text(encoding="utf-8") + "\nMARQUEUR\n", encoding="utf-8")
                    with self.assertRaises(ClaudeCodeLocalError) as refus:
                        _load_installed_plan(projet.store)
            finally:
                projet.close()
        message = str(refus.exception)
        self.assertIn("playbook.md", message)
        self.assertIn("install", message, "le refus doit nommer la marche à suivre")

    def test_a_changed_command_names_both_the_old_and_the_new_one(self) -> None:
        """Le cas qui m'a coûté le plus de temps : la résolution avait changé d'environnement."""
        from vera_mmu.claude_code_local import _load_installed_plan

        with TemporaryDirectory() as repertoire:
            projet = _Projet(Path(repertoire))
            try:
                with mock.patch(
                    "vera_mmu.claude_code_local.shutil.which",
                    lambda nom: BINAIRE_REEL if nom == CLI_BINARY_NAME else None,
                ):
                    projet.installer()
                # Le script console réapparaît — un `pip install` entre-temps suffit.
                with mock.patch("vera_mmu.claude_code_local.shutil.which", lambda nom: f"/usr/bin/{nom}"):
                    with self.assertRaises(ClaudeCodeLocalError) as refus:
                        _load_installed_plan(projet.store)
            finally:
                projet.close()
        message = str(refus.exception)
        self.assertIn(BINAIRE_REEL, message, "la commande attestée doit être nommée")
        self.assertIn(MCP_ENTRYPOINT, message, "celle qui serait écrite aussi")

    def test_an_unreadable_state_says_so_rather_than_blaming_the_content(self) -> None:
        from vera_mmu.claude_code_local import _describe_drift

        self.assertIn("plus lisible", _describe_drift("pas du json", None))  # type: ignore[arg-type]


class SiblingLookupIsForPackagedBinariesOnlyTests(unittest.TestCase):
    """« À côté de moi » ne veut dire « livré avec moi » que pour un exécutable empaqueté.

    Mesuré sur le runner CI, où `pip` pose `vmmu` dans le même répertoire que l'interpréteur :
    la recherche du voisin court-circuitait le `PATH`, donc l'injection par laquelle les tests
    simulent une machine sans CLI, et seize tests sont tombés d'un coup. En local, le lien
    `/usr/local/bin/python3` se résout vers `/usr/bin`, où `pip` n'avait rien posé — la suite
    passait par accident de disposition.
    """

    def test_a_plain_interpreter_never_claims_its_neighbour(self) -> None:
        from vera_mmu import claude_code_local

        with TemporaryDirectory() as repertoire:
            faux = Path(repertoire) / "bin"
            faux.mkdir()
            (faux / "python3").write_bytes(b"#!/bin/sh\n")
            (faux / CLI_BINARY_NAME).write_bytes(b"\x7fELF")
            environnement = {c: v for c, v in os.environ.items() if c != CLI_MARKER_VARIABLE}
            with mock.patch.object(claude_code_local.sys, "executable", str(faux / "python3")), \
                 mock.patch.dict(os.environ, environnement, clear=True):
                # Non gelé : le voisin ne prouve rien, et le `PATH` — substituable — décide seul.
                self.assertFalse(getattr(claude_code_local.sys, "frozen", False))
                self.assertIsNone(claude_code_local._sibling_cli())
                self.assertIsNone(claude_code_local._cli_binary(command_lookup=_absent))

    def test_the_path_lookup_still_decides_for_a_plain_interpreter(self) -> None:
        """Le `PATH` reste la voie d'un `pip install`, et il passe par le point d'injection."""
        from vera_mmu import claude_code_local

        self.assertEqual(
            claude_code_local._cli_binary(command_lookup=lambda nom: BINAIRE_REEL if nom == CLI_BINARY_NAME else None),
            BINAIRE_REEL,
        )

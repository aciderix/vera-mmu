"""Claude Code local lifecycle adapter: attested plan, fixed hooks, opt-in install, and doctor.

This module is intentionally local-only.  It never touches user/home settings, performs no
network/bootstrap/synchronization, and never selects a Domain Pack or executes a capability.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import sys
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Mapping, Sequence

from .claude_code_integration import ClaudeCodeIntegrationError, ClaudeCodeIntegrationPlan, compile_claude_code_integration_plan
from .lifecycle_adapters import LifecycleAdapterPlan, LifecycleAdapterRegistry, compile_lifecycle_adapter_plan
from .mcp_hooks import MCPHookPlan, MCPHookPlanError, compile_mcp_hook_plan
from .mcp_instructions import MCPInstructions, MCPInstructionsError, compile_mcp_instructions
from .mcp_integration import MCPIntegration, MCPIntegrationError, compile_mcp_integration
from .mcp_manifest import MCPManifest, MCPManifestError, compile_mcp_manifest, verify_mcp_manifest
from .mcp_server import DenyRuntimeAdapter, create_server
from .session_lifecycle import GuardDecision, ResumeDossierService, ResumeGuardService, ResumeSectionRequirement
from .profile_resume import compile_profile_resume_dossier, profile_resume_sections
from .store import MemoryStore, StoreError


CLAUDE_CODE_LOCAL_FORMAT = "vera-claude-code-local/v1"
CLAUDE_CODE_LOCAL_ADAPTER_ID = "claude-code-local-v1"
CLAUDE_CODE_LOCAL_ADAPTER_VERSION = "1.0.0"
CLAUDE_CODE_LOCAL_MAXIMUM_GUARD_MODE = "HARD"
HOOK_ENTRYPOINT = "vmmu-claude-code-local-hook"
MCP_ENTRYPOINT = "vmmu-claude-code-local-mcp"
#: Sous-commandes équivalentes portées par la CLI unique, pour la release autonome.
HOOK_SUBCOMMAND = "claude-code-local-hook"
MCP_SUBCOMMAND = "claude-code-local-mcp"


#: Nom de la CLI autonome que les archives de release embarquent. Cherché sur le `PATH` quand le
#: processus courant n'est pas lui-même cette CLI — c'est le cas de l'application de bureau, dont
#: le sidecar est un tout autre binaire.
CLI_BINARY_NAME = "vmmu"

#: Variable que la CLI autonome pose avant de servir une sous-commande, pour se faire reconnaître
#: par le code qui écrit la configuration. Un simple `sys.frozen` ne distingue pas deux binaires
#: PyInstaller différents — et c'est exactement la confusion qui a produit une configuration morte.
CLI_MARKER_VARIABLE = "VERA_MMU_CLI_BINARY"


def resolve_entrypoint(
    entrypoint: str, subcommand: str, *, command_lookup: Callable[[str], str | None] | None = None
) -> str | None:
    """Rend la ligne de commande qui lancera cet entry point, ou `None` si aucune ne le peut.

    Conservée pour les hooks, dont le `command` **est** une ligne de shell. Pour `.mcp.json`, où
    `command` désigne un programme et `args` ses arguments, voir `resolve_launcher`.

    **Le défaut mesuré.** `install` écrivait `vmmu-claude-code-local-mcp` dans `.mcp.json` et
    `vmmu-claude-code-local-hook` dans les hooks. Ce sont des scripts console déclarés dans
    `pyproject.toml` : ils n'existent qu'après un `pip install`. Or **aucun artefact de release ne
    les embarque** — l'archive CLI ne contient que `vmmu`, et le paquet `.deb` que le bureau et son
    sidecar. Depuis la release, la configuration générée pointait donc vers des commandes absentes,
    et l'hôte n'aurait jamais pu démarrer le serveur.

    Deux formes sont acceptées, dans cet ordre : le script console s'il est installé — ce qui
    laisse intactes les installations `pip` existantes — puis la CLI unique invoquée avec sa
    sous-commande équivalente, ce qui rend la release autonome sans rien embarquer de plus.

    `None` est un refus lisible plutôt qu'un chemin inventé : écrire une commande qu'on ne sait
    pas résoudre, c'est produire une configuration qui ne peut pas fonctionner.
    """
    # Résolu à l'appel et non en valeur par défaut : un défaut par défaut capture `shutil.which`
    # au moment de la définition, donc aucun test ne peut le substituer. Le test qui exerce
    # `install` sur une machine sans script console l'a montré en ne voyant aucun refus.
    lanceur = resolve_launcher(entrypoint, subcommand, command_lookup=command_lookup)
    if lanceur is None:
        return None
    programme, arguments = lanceur
    return " ".join(_quote(element) for element in (programme, *arguments))


def _quote(element: str) -> str:
    """Entoure de guillemets **doubles** un élément qui en a besoin, et seulement alors.

    Mesuré sur le runner Windows : `shlex.quote`, employé d'abord ici, applique les règles POSIX
    et entoure de guillemets **simples** tout ce qui sort de `[a-zA-Z0-9_@%+=:,./-]`. Un chemin
    Windows contient des contre-obliques, donc *tout* chemin Windows y passait :

        'D:\\a\\vera-mmu\\...\\vmmu' claude-code-local-hook --profile "..."

    `cmd.exe` ne reconnaît pas le guillemet simple comme une citation : la commande de hook
    aurait été illisible sur la plateforme où elle est justement la plus fragile. Le guillemet
    double, lui, est compris des deux côtés — et c'est déjà celui que la suite de la ligne
    emploie pour l'argument de profil, dont le `${CLAUDE_PROJECT_DIR:-.}` doit rester
    interprétable.
    """
    return f'"{element}"' if any(caractere.isspace() for caractere in element) else element


def resolve_launcher(
    entrypoint: str, subcommand: str, *, command_lookup: Callable[[str], str | None] | None = None
) -> tuple[str, tuple[str, ...]] | None:
    """Rend `(programme, arguments)` — jamais une ligne à découper par celui qui la lit.

    **Le défaut mesuré.** La version précédente rendait la chaîne `"<binaire> <sous-commande>"`,
    et `install` la posait telle quelle dans le champ `command` de `.mcp.json`. Or ce champ
    désigne un **programme**, pas une ligne de commande : `args` porte les arguments. Un client
    qui l'exécute sans passer par un shell — ce que fait un client MCP — demande donc au système
    un fichier dont le nom contient une espace, et reçoit `ENOENT`. Mesuré sur la release :

        [Errno 2] No such file or directory: '…/vmmu claude-code-local-mcp'

    Rendre la paire plutôt que la chaîne supprime la question : chaque appelant compose ensuite
    selon sa cible — `command`/`args` pour MCP, une ligne de shell correctement échappée pour les
    hooks, dont le `command` est bien une ligne de shell.
    """
    # Résolu à l'appel et non en valeur par défaut : un défaut par défaut capture `shutil.which`
    # au moment de la définition, donc aucun test ne peut le substituer. Le test qui exerce
    # `install` sur une machine sans script console l'a montré en ne voyant aucun refus.
    lookup = command_lookup if command_lookup is not None else shutil.which
    if lookup(entrypoint):
        return entrypoint, ()
    binary = _cli_binary(command_lookup=lookup)
    if binary is not None:
        return binary, (subcommand,)
    return None


def _cli_binary(*, command_lookup: Callable[[str], str | None] | None = None) -> str | None:
    """Rend le chemin d'un binaire qui porte réellement les sous-commandes VERA, ou `None`.

    **Le défaut mesuré, et il était grave.** La version précédente rendait `sys.executable` dès
    que `sys.frozen` était vrai. Or cette condition est vraie dans **tout** binaire PyInstaller,
    et le produit en livre deux : la CLI `vmmu`, et le sidecar `vmmu-desktop-bridge` que
    l'application de bureau lance. Quand l'installation partait de la fenêtre, `.mcp.json`
    recevait donc :

        "command": "/tmp/.mount_VERA-MjDbbJp/usr/bin/vmmu-desktop-bridge claude-code-local-mcp"

    Deux fautes en une, chacune fatale. Le binaire désigné est le **bridge**, qui ne connaît pas
    cette sous-commande et exige `--project-root` et `--nonce` : aucune voie de lancement ne pouvait
    aboutir. Et le chemin est le point de montage de l'AppImage, qui disparaît à la fermeture de
    l'application et change de nom à chaque lancement : même un binaire correct aurait été
    introuvable ensuite. **Toute configuration MCP produite depuis la fenêtre était morte-née, et
    définitivement.** Le paquet de bureau n'embarque d'ailleurs pas la CLI — seulement
    `vera-mmu-desktop` et `vmmu-desktop-bridge` — donc aucune supposition ne pouvait la sauver.

    L'ordre suivi n'accepte que ce qui est démontrable :

    1. le processus courant, s'il s'est **déclaré** comme la CLI — un binaire gelé ne se reconnaît
       pas à `sys.frozen`, qui ne distingue pas deux binaires différents, mais à la marque que
       `vmmu` pose avant de servir une sous-commande ;
    2. à défaut, un `vmmu` trouvé sur le `PATH` — c'est la voie de l'application de bureau quand
       l'archive CLI est installée à côté d'elle ;
    3. sinon `None`, qui fait refuser l'installation au lieu d'écrire une commande inerte.

    Un chemin éphémère est écarté dans tous les cas : ce qu'on écrit dans `.mcp.json` doit encore
    exister quand l'hôte le lira, c'est-à-dire après la fin du processus qui l'a écrit.
    """
    marque = os.environ.get(CLI_MARKER_VARIABLE, "").strip()
    if marque and getattr(sys, "frozen", False):
        candidat = Path(sys.executable)
        if candidat.is_file() and not _is_ephemeral(candidat):
            return str(candidat)
    voisin = _sibling_cli()
    if voisin is not None:
        return voisin
    lookup = command_lookup if command_lookup is not None else shutil.which
    trouve = lookup(CLI_BINARY_NAME)
    if trouve:
        chemin = Path(trouve)
        if not _is_ephemeral(chemin):
            return str(chemin)
    return None


def _sibling_cli() -> str | None:
    """Cherche la CLI **livrée à côté** du processus courant.

    Le paquet de bureau embarque désormais `vmmu` aux côtés du sidecar. Sur une installation
    `.deb`, les deux atterrissent dans `/usr/bin`, donc le `PATH` les trouve de toute façon ;
    sur Windows, en revanche, le répertoire d'installation n'est presque jamais dans le `PATH`,
    et sans cette recherche l'application de bureau ne verrait pas la CLI qu'elle transporte.

    Préférée au `PATH` : entre la CLI livrée avec cette application et une autre installée par
    ailleurs, celle qui vient du même paquet porte la même version, donc le même plan compilé.
    """
    try:
        voisin = Path(sys.executable).resolve().parent / CLI_BINARY_NAME
    except OSError:  # pragma: no cover - chemin d'exécutable illisible
        return None
    for candidat in (voisin, voisin.with_suffix(".exe")):
        if candidat.is_file() and not candidat.is_symlink() and not _is_ephemeral(candidat):
            return str(candidat)
    return None


#: Préfixes de points de montage qui ne survivent pas au processus qui les a créés. AppImage monte
#: son squashfs sous `/tmp/.mount_<nom><aléa>` et le démonte à la sortie ; le nom change à chaque
#: lancement, donc même l'écrire correctement ne le rendrait pas retrouvable.
_EPHEMERAL_MARKERS = ("/tmp/.mount_", "/private/tmp/.mount_")


def _is_ephemeral(candidate: Path) -> bool:
    """Le chemin disparaîtra-t-il avec le processus courant ?

    Écrire dans `.mcp.json` un chemin qui ne survivra pas à la fermeture de l'application, c'est
    livrer une configuration qui fonctionne exactement tant que personne ne la relit.
    """
    texte = candidate.as_posix()
    if any(texte.startswith(prefixe) for prefixe in _EPHEMERAL_MARKERS):
        return True
    racine = os.environ.get("APPDIR", "").strip()
    return bool(racine) and (texte == racine or texte.startswith(racine.rstrip("/") + "/"))


def program_is_launchable(program: str, *, command_lookup: Callable[[str], str | None] | None = None) -> bool:
    """Le programme nommé dans une configuration générée peut-il encore être lancé ?

    Un chemin est vérifié comme fichier ; un nom nu est cherché sur le `PATH`. Les deux cas se
    distinguent par la présence d'un séparateur, comme le fait l'exécution elle-même : `foo/bar`
    n'est jamais cherché sur le `PATH`, `bar` l'est toujours.
    """
    if not program:
        return False
    separateurs = [os.sep] + ([os.altsep] if os.altsep else [])
    if any(separateur in program for separateur in separateurs):
        return Path(program).is_file()
    lookup = command_lookup if command_lookup is not None else shutil.which
    return lookup(program) is not None


def entrypoint_status(*, command_lookup: Callable[[str], str | None] | None = None) -> dict[str, str | None]:
    """Rend, pour chaque entry point, la commande qui le lancera — ou `None`.

    Une seule source pour le diagnostic et pour l'installation : les faire diverger reviendrait à
    diagnostiquer autre chose que ce qui est écrit.
    """
    return {
        "hook": resolve_entrypoint(HOOK_ENTRYPOINT, HOOK_SUBCOMMAND, command_lookup=command_lookup),
        "mcp": resolve_entrypoint(MCP_ENTRYPOINT, MCP_SUBCOMMAND, command_lookup=command_lookup),
    }


def _require_resolvable_entrypoints(*, command_lookup: Callable[[str], str | None] | None = None) -> None:
    """Refuse l'installation tant qu'une des deux commandes ne peut pas être lancée."""
    statut = entrypoint_status(command_lookup=command_lookup)
    manquants = sorted(nom for nom, valeur in statut.items() if valeur is None)
    if not manquants:
        return
    attendus = {"hook": HOOK_ENTRYPOINT, "mcp": MCP_ENTRYPOINT}
    # Nommer la cause quand on la connaît. Depuis une AppImage, la CLI **est** là — à côté du
    # sidecar — mais sous un point de montage qui disparaît à la fermeture : un utilisateur qui
    # lit « commande introuvable » alors qu'il voit le binaire dans le paquet chercherait au
    # mauvais endroit. C'est le cas où le refus doit le plus expliquer, puisqu'il est le moins
    # intuitif.
    if _running_from_ephemeral_image():
        raise ClaudeCodeLocalError(
            "Installation refusée : lancée depuis une image dont le contenu est monté "
            "temporairement (AppImage), l'application ne peut désigner aucun chemin qui existera "
            "encore après sa fermeture. Installer VERA par le paquet `.deb`, ou décompresser "
            "l'archive CLI et placer `vmmu` dans le PATH, puis relancer l'installation."
        )
    raise ClaudeCodeLocalError(
        "Installation refusée : la configuration désignerait des commandes introuvables — "
        + ", ".join(f"`{attendus[nom]}`" for nom in manquants)
        + ". Installer le paquet VERA (`pip install vera-mmu`) ou utiliser la CLI autonome, "
        "qui porte les sous-commandes équivalentes."
    )


def _running_from_ephemeral_image() -> bool:
    """Le processus courant tourne-t-il depuis un montage qui ne lui survivra pas ?"""
    try:
        return _is_ephemeral(Path(sys.executable))
    except OSError:  # pragma: no cover - chemin d'exécutable illisible
        return False


_EVENTS = ("SessionStart", "PreToolUse", "PostToolUse", "PreCompact", "PostCompact", "Stop")


class ClaudeCodeLocalError(StoreError):
    """The local Claude lifecycle adapter cannot be compiled, installed, or invoked safely."""


@dataclass(frozen=True)
class ClaudeCodeLocalPlan:
    """Canonical local-only host plan, bound to all upstream snapshots and adapter bindings."""

    format: str
    project_id: str
    mcp_build_hash: str
    instructions_hash: str
    config_hash: str
    hook_plan_hash: str
    review_plan_hash: str
    lifecycle_plan_hash: str
    adapter_bindings: tuple[tuple[str, str], ...]
    plan_hash: str
    json_text: str


@dataclass(frozen=True)
class ClaudeCodeLocalInstallResult:
    status: str
    settings_path: Path
    mcp_path: Path
    state_path: Path
    plan_hash: str


@dataclass(frozen=True)
class ClaudeCodeLocalDoctorReport:
    status: str
    checks: tuple[tuple[str, str], ...]
    install_actions: tuple[str, ...]


class ClaudeCodeLocalSessionAdapter:
    """Read the single active Claude local session recorded by a verified SessionStart hook."""

    adapter_id = CLAUDE_CODE_LOCAL_ADAPTER_ID
    adapter_version = CLAUDE_CODE_LOCAL_ADAPTER_VERSION
    maximum_guard_mode = CLAUDE_CODE_LOCAL_MAXIMUM_GUARD_MODE

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def session_identity(self) -> str | None:
        binding = _read_session_binding(self.store)
        return None if binding is None else binding["session_id"]


def compile_claude_code_local_plan(
    store: MemoryStore,
    manifest: MCPManifest,
    instructions: MCPInstructions,
    integration: MCPIntegration,
    hooks: MCPHookPlan,
    review: ClaudeCodeIntegrationPlan,
    lifecycle: LifecycleAdapterPlan,
) -> ClaudeCodeLocalPlan:
    """Compile the only local Claude adapter plan from fully verified snapshots."""
    if not isinstance(store, MemoryStore):
        raise ClaudeCodeLocalError("Store invalide pour l’adapter Claude local.")
    try:
        verify_mcp_manifest(store, manifest)
        expected_instructions = compile_mcp_instructions(store, manifest)
        expected_integration = compile_mcp_integration(store, manifest, expected_instructions)
        expected_hooks = compile_mcp_hook_plan(store, manifest, expected_instructions, expected_integration)
        expected_review = compile_claude_code_integration_plan(
            store, manifest, expected_instructions, expected_integration, expected_hooks
        )
        expected_lifecycle = compile_lifecycle_adapter_plan(
            store,
            manifest,
            adapter_id=CLAUDE_CODE_LOCAL_ADAPTER_ID,
            adapter_version=CLAUDE_CODE_LOCAL_ADAPTER_VERSION,
            maximum_guard_mode=CLAUDE_CODE_LOCAL_MAXIMUM_GUARD_MODE,
        )
    except (MCPManifestError, MCPInstructionsError, MCPIntegrationError, MCPHookPlanError, ClaudeCodeIntegrationError, StoreError) as exc:
        raise ClaudeCodeLocalError("Snapshots invalides pour l’adapter Claude local.") from exc
    if (
        instructions != expected_instructions
        or integration != expected_integration
        or hooks != expected_hooks
        or review != expected_review
        or lifecycle != expected_lifecycle
    ):
        raise ClaudeCodeLocalError("Snapshot Claude local périmé, altéré ou étranger.")
    bindings = tuple((item.capability_id, item.adapter_id) for item in manifest.capabilities)
    server_id, generic_server = _single_server(integration)
    profile_argument = _profile_argument(generic_server)
    # `command` désigne un programme et `args` ses arguments : la sous-commande appartient donc à
    # `args`, jamais au nom du programme. La version précédente concaténait les deux dans
    # `command`, et tout client MCP qui exécute sans shell y lisait un fichier inexistant.
    lanceur = resolve_launcher(MCP_ENTRYPOINT, MCP_SUBCOMMAND)
    programme, arguments_lanceur = lanceur if lanceur is not None else (MCP_ENTRYPOINT, ())
    local_server = {
        "args": [*arguments_lanceur, "--profile", profile_argument],
        # Résolu plutôt que supposé : voir `resolve_launcher` et `_cli_binary`. Le nom logique
        # reste préféré quand il existe, pour ne pas invalider les installations `pip` en place.
        "command": programme,
        "env": {
            "VERA_CLAUDE_CODE_LOCAL": "1",
            "VERA_MCP_BUILD_HASH": manifest.mcp_build_hash,
            "VERA_MCP_INSTRUCTIONS_HASH": instructions.instructions_hash,
            "VERA_PROJECT_ID": store.identity.project_id,
        },
    }
    hook_commands = _hook_commands(store, server_id, profile_argument)
    payload = {
        "claudeCodeLocal": {
            "adapter": {
                "id": CLAUDE_CODE_LOCAL_ADAPTER_ID,
                "maximum_guard_mode": CLAUDE_CODE_LOCAL_MAXIMUM_GUARD_MODE,
                "version": CLAUDE_CODE_LOCAL_ADAPTER_VERSION,
            },
            "adapterBindings": [{"adapter_id": adapter_id, "capability_id": capability_id} for capability_id, adapter_id in bindings],
            "hooks": hook_commands,
            # Les empreintes des fichiers dont le plan dérive, pour que le vieillissement se lise
            # sans recompiler. `_load_installed_plan` compare déjà le plan à l'octet près, mais
            # il ne parle qu'au démarrage du serveur : le diagnostic, lui, s'interdit d'ouvrir la
            # mémoire et n'avait donc aucun moyen de voir qu'une édition du playbook venait de
            # condamner l'installation. Mesuré sur la release : serveur mort, `doctor` PASS.
            "inputs": _input_digests(store),
            "installation": {"mcpTarget": ".mcp.json", "mode": "OPT_IN", "settingsTarget": ".claude/settings.json"},
            "mcpServer": {"id": server_id, **local_server},
        }
    }
    json_text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    return ClaudeCodeLocalPlan(
        format=CLAUDE_CODE_LOCAL_FORMAT,
        project_id=store.identity.project_id,
        mcp_build_hash=manifest.mcp_build_hash,
        instructions_hash=instructions.instructions_hash,
        config_hash=integration.config_hash,
        hook_plan_hash=hooks.hook_plan_hash,
        review_plan_hash=review.plan_hash,
        lifecycle_plan_hash=lifecycle.lifecycle_plan_hash,
        adapter_bindings=bindings,
        plan_hash=sha256(json_text.encode("utf-8")).hexdigest(),
        json_text=json_text,
    )


def handle_claude_code_local_hook(
    store: MemoryStore,
    lifecycle: LifecycleAdapterPlan,
    plan: ClaudeCodeLocalPlan,
    event: str,
    payload: Mapping[str, object],
) -> dict[str, object]:
    """Translate one fixed Claude event into the local Core lifecycle without shell semantics."""
    _verify_local_plan(store, lifecycle, plan)
    if event not in _EVENTS or not isinstance(payload, Mapping):
        raise ClaudeCodeLocalError("Événement ou payload Claude local invalide.")
    session_id = payload.get("session_id")
    if not isinstance(session_id, str) or not session_id or len(session_id) > 256 or "/" in session_id or "\\" in session_id:
        raise ClaudeCodeLocalError("Identité de session Claude locale absente ou invalide.")
    _verify_cwd(store, payload.get("cwd"))
    guard = ResumeGuardService(store)
    if event == "SessionStart":
        _claim_session(store, session_id)
        source = payload.get("source")
        reason = "RESUME" if source == "resume" else "SESSION_OPEN" if source == "startup" else "CONTEXT_RESTORED"
        dossier = _compile_resume_dossier(store)
        guard.arm(session_id, CLAUDE_CODE_LOCAL_ADAPTER_ID, reason, dossier, mode="HARD")
        return _context(event, "Resume Dossier VERA — lire et acquitter via mmu_acknowledge_resume :\n" + dossier.json_text)
    if _read_session_binding(store) != {"project_id": store.identity.project_id, "session_id": session_id}:
        raise ClaudeCodeLocalError("Session Claude locale non liée au runtime courant.")
    if event == "PreToolUse":
        tool_name = payload.get("tool_name")
        if not isinstance(tool_name, str):
            raise ClaudeCodeLocalError("PreToolUse Claude sans nom de tool.")
        if tool_name == _acknowledgement_tool_name(store):
            return _empty(event)
        outcome = guard.precheck(session_id, CLAUDE_CODE_LOCAL_ADAPTER_ID, tool_name)
        if outcome.decision == GuardDecision.DENY:
            return _deny(event, outcome.reason)
        if outcome.decision == GuardDecision.ALLOW_WITH_NOTICE:
            return _context(event, outcome.reason)
        return _empty(event)
    if event == "PostToolUse":
        outcome = guard.precheck(session_id, CLAUDE_CODE_LOCAL_ADAPTER_ID)
        return _context(event, outcome.reason) if outcome.decision != GuardDecision.ALLOW else _empty(event)
    if event == "PreCompact":
        dossier = _compile_resume_dossier(store)
        guard.arm(session_id, CLAUDE_CODE_LOCAL_ADAPTER_ID, "CONTEXT_PREPARE", dossier, mode="HARD")
        return _context(event, "VERA prépare la reprise de contexte ; le dossier devra être acquitté après compaction.")
    if event == "PostCompact":
        dossier = _compile_resume_dossier(store)
        guard.arm(session_id, CLAUDE_CODE_LOCAL_ADAPTER_ID, "CONTEXT_RESTORED", dossier, mode="HARD")
        return _context(event, "Resume Dossier VERA — lire et acquitter via mmu_acknowledge_resume :\n" + dossier.json_text)
    outcome = guard.session_ending(session_id, CLAUDE_CODE_LOCAL_ADAPTER_ID, already_nudged=False)
    _release_session(store, session_id)
    return _context(event, outcome.reason) if outcome.decision == GuardDecision.NUDGE else _empty(event)


def install_claude_code_local(
    store: MemoryStore,
    manifest: MCPManifest,
    instructions: MCPInstructions,
    integration: MCPIntegration,
    hooks: MCPHookPlan,
    review: ClaudeCodeIntegrationPlan,
    lifecycle: LifecycleAdapterPlan,
    plan: ClaudeCodeLocalPlan,
    *,
    confirm: bool,
) -> ClaudeCodeLocalInstallResult:
    """Install only the attested project-local hooks and local VERA MCP server after confirmation."""
    if confirm is not True:
        raise ClaudeCodeLocalError("Installation Claude locale refusée sans confirmation explicite.")
    # Écrire une configuration dont les commandes n'existent pas, puis se déclarer sain, est
    # exactement le défaut que ce produit existe pour empêcher. Mesuré : `doctor` rendait PASS et
    # « 1 intégration déclarée et installée » sur un `.mcp.json` pointant vers un script console
    # absent de tout artefact de release. Le refus est donc posé ici, avant la première écriture.
    _require_resolvable_entrypoints()
    expected = compile_claude_code_local_plan(store, manifest, instructions, integration, hooks, review, lifecycle)
    if plan != expected:
        raise ClaudeCodeLocalError("Plan Claude local périmé, altéré ou étranger.")
    settings_path = _settings_target(store)
    mcp_path = _mcp_target(store)
    state_path = _installation_state_path(store)
    settings = _load_json_object(settings_path, "settings Claude")
    mcp = _load_json_object(mcp_path, "configuration MCP")
    desired_hooks = _plan_payload(plan)["hooks"]
    desired_server = _plan_payload(plan)["mcpServer"]
    generic_server = _single_server(integration)[1]
    merged_settings, settings_changed = _merge_hooks(settings, desired_hooks)
    merged_mcp, mcp_changed = _merge_local_server(mcp, desired_server, generic_server)
    existing_state = _read_optional_text(state_path)
    # Un état présent mais illisible n'est pas le nôtre : refuser reste juste. Un état qui est
    # bien le nôtre et qui a simplement vieilli doit au contraire être réécrit, sans quoi le
    # serveur déclaré refuserait de démarrer — `_load_installed_plan` compare à l'octet près.
    if existing_state is not None and existing_state != plan.json_text and not _is_our_state(existing_state, plan):
        raise ClaudeCodeLocalError("État d’installation lifecycle local divergent : refus sans écriture.")
    state_changed = existing_state != plan.json_text
    if not settings_changed and not mcp_changed and not state_changed:
        return ClaudeCodeLocalInstallResult("UNCHANGED", settings_path, mcp_path, state_path, plan.plan_hash)
    if settings_changed:
        _atomic_write(settings_path, _canonical_json(merged_settings), ".vera-claude-settings-")
    if mcp_changed:
        _atomic_write(mcp_path, _canonical_json(merged_mcp), ".vera-claude-mcp-")
    if state_changed:
        _atomic_write(state_path, plan.json_text, ".vera-claude-state-")
    statut = "UPDATED" if existing_state is not None else "INSTALLED"
    return ClaudeCodeLocalInstallResult(statut, settings_path, mcp_path, state_path, plan.plan_hash)


def _is_our_state(raw: str, plan: ClaudeCodeLocalPlan) -> bool:
    """L'état déjà présent est-il une trace VERA de ce même adapter pour ce même serveur ?

    Le critère ne porte pas sur le contenu — qui change à chaque édition légitime — mais sur la
    provenance : même format, même adapter, même identifiant de serveur. Tout le reste est
    étranger et reste refusé.
    """
    try:
        charge = json.loads(raw)["claudeCodeLocal"]
        adapter = charge["adapter"]["id"]
        serveur = charge["mcpServer"]["id"]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False
    return adapter == CLAUDE_CODE_LOCAL_ADAPTER_ID and serveur == _plan_payload(plan)["mcpServer"]["id"]


def inspect_claude_code_local(
    store: MemoryStore,
    manifest: MCPManifest,
    instructions: MCPInstructions,
    integration: MCPIntegration,
    hooks: MCPHookPlan,
    review: ClaudeCodeIntegrationPlan,
    lifecycle: LifecycleAdapterPlan,
    plan: ClaudeCodeLocalPlan,
    *,
    command_lookup: Callable[[str], str | None] | None = None,
) -> ClaudeCodeLocalDoctorReport:
    """Observe exact local installation state; never install, approve, or repair."""
    expected = compile_claude_code_local_plan(store, manifest, instructions, integration, hooks, review, lifecycle)
    if plan != expected:
        raise ClaudeCodeLocalError("Plan Claude local périmé, altéré ou étranger.")
    checks: list[tuple[str, str]] = []
    settings_path = _settings_target(store, create=False)
    mcp_path = _mcp_target(store)
    state_path = _installation_state_path(store, create=False)
    expected_payload = _plan_payload(plan)
    settings = _load_json_object(settings_path, "settings Claude")
    mcp = _load_json_object(mcp_path, "configuration MCP")
    hooks_ok = _hooks_installed(settings, expected_payload["hooks"])
    server_ok = _server_installed(mcp, expected_payload["mcpServer"])
    state_ok = _read_optional_text(state_path) == plan.json_text
    checks.extend((("hooks", "PASS" if hooks_ok else "MISSING"), ("mcp", "PASS" if server_ok else "MISSING"), ("state", "PASS" if state_ok else "MISSING")))
    if not hooks_ok and not server_ok and not state_ok:
        return ClaudeCodeLocalDoctorReport("NOT_INSTALLED", tuple(checks), ())
    statut = entrypoint_status(command_lookup=command_lookup)
    hook_entrypoint = statut["hook"]
    mcp_entrypoint = statut["mcp"]
    checks.extend((("hook_entrypoint", "PASS" if hook_entrypoint else "MISSING"), ("mcp_entrypoint", "PASS" if mcp_entrypoint else "MISSING")))
    if hooks_ok and server_ok and state_ok and hook_entrypoint and mcp_entrypoint:
        return ClaudeCodeLocalDoctorReport("READY", tuple(checks), ())
    return ClaudeCodeLocalDoctorReport("DEGRADED", tuple(checks), ())


def _verify_local_plan(store: MemoryStore, lifecycle: LifecycleAdapterPlan, plan: ClaudeCodeLocalPlan) -> None:
    bindings = dict(plan.adapter_bindings)
    try:
        manifest = compile_mcp_manifest(store, adapter_bindings=bindings)
        instructions = compile_mcp_instructions(store, manifest)
        integration = compile_mcp_integration(store, manifest, instructions)
        hooks = compile_mcp_hook_plan(store, manifest, instructions, integration)
        review = compile_claude_code_integration_plan(store, manifest, instructions, integration, hooks)
        expected_lifecycle = compile_lifecycle_adapter_plan(
            store,
            manifest,
            adapter_id=CLAUDE_CODE_LOCAL_ADAPTER_ID,
            adapter_version=CLAUDE_CODE_LOCAL_ADAPTER_VERSION,
            maximum_guard_mode=CLAUDE_CODE_LOCAL_MAXIMUM_GUARD_MODE,
        )
        expected = compile_claude_code_local_plan(store, manifest, instructions, integration, hooks, review, expected_lifecycle)
    except StoreError as exc:
        raise ClaudeCodeLocalError("Plan lifecycle Claude local invérifiable.") from exc
    if lifecycle != expected_lifecycle or plan != expected:
        raise ClaudeCodeLocalError("Plan lifecycle Claude local périmé, altéré ou étranger.")


#: Les fichiers du runtime dont le plan Claude local dérive. Leur empreinte est enregistrée à
#: l'installation pour qu'un diagnostic qui n'ouvre pas la mémoire puisse constater l'écart.
INPUT_FILES = ("playbook.md", "capabilities.yaml", "gates.yaml", "policies.yaml", "agent-profiles.yaml")


def _input_digests(store: MemoryStore) -> dict[str, str]:
    """Empreintes vues depuis la mémoire ouverte — même fonction que côté diagnostic.

    Une seule implémentation, délibérément : deux calculs d'empreinte qui divergeraient d'un
    octet feraient rapporter une dérive permanente, ou aucune. C'est la leçon déjà posée sur
    `entrypoint_status` — diagnostiquer autre chose que ce qui est écrit ne diagnostique rien.
    """
    return input_digests_for(store.locator.runtime_dir)


def input_digests_for(runtime_dir: Path) -> dict[str, str]:
    """Empreinte de chaque fichier dont le plan dépend ; `ABSENT` quand il n'y en a pas."""
    empreintes: dict[str, str] = {}
    for nom in INPUT_FILES:
        chemin = runtime_dir / nom
        try:
            empreintes[nom] = sha256(chemin.read_bytes()).hexdigest() if chemin.is_file() else "ABSENT"
        except OSError:
            empreintes[nom] = "ILLISIBLE"
    return empreintes


def _single_server(integration: MCPIntegration) -> tuple[str, dict[str, object]]:
    try:
        payload = json.loads(integration.json_text)
        servers = payload["mcpServers"]
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ClaudeCodeLocalError("Configuration MCP attestée illisible.") from exc
    if not isinstance(servers, dict) or len(servers) != 1:
        raise ClaudeCodeLocalError("Configuration MCP attestée doit contenir un serveur unique.")
    identifier, server = next(iter(servers.items()))
    if not isinstance(identifier, str) or not isinstance(server, dict):
        raise ClaudeCodeLocalError("Serveur MCP attesté invalide.")
    return identifier, dict(server)


def _profile_argument(server: Mapping[str, object]) -> str:
    args = server.get("args")
    if not isinstance(args, list) or len(args) != 2 or args[0] != "--profile" or not isinstance(args[1], str):
        raise ClaudeCodeLocalError("Argument de profil MCP attesté invalide.")
    return args[1]


def _hook_commands(store: MemoryStore, server_id: str, profile_argument: str) -> dict[str, list[dict[str, object]]]:
    if not server_id.startswith("vera-mmu-"):
        raise ClaudeCodeLocalError("Identifiant serveur VERA local invalide.")
    def group(event: str, *, matcher: str | None = None) -> dict[str, object]:
        lanceur = resolve_entrypoint(HOOK_ENTRYPOINT, HOOK_SUBCOMMAND) or HOOK_ENTRYPOINT
        command = f'{lanceur} --profile "{profile_argument}" --event {event}'
        handler: dict[str, object] = {"command": command, "timeout": 10, "type": "command"}
        payload: dict[str, object] = {"hooks": [handler]}
        if matcher is not None:
            payload["matcher"] = matcher
        return payload
    return {
        "PostCompact": [group("PostCompact")],
        "PostToolUse": [group("PostToolUse", matcher=f"mcp__{server_id}__mmu_acknowledge_resume")],
        "PreCompact": [group("PreCompact")],
        "PreToolUse": [group("PreToolUse")],
        "SessionStart": [group("SessionStart")],
        "Stop": [group("Stop")],
    }


def _compile_resume_dossier(store: MemoryStore):
    return compile_profile_resume_dossier(store, profile_resume_sections(store, "La garde Claude locale attend un acquittement avant toute action contrôlée."))


def _context(event: str, text: str) -> dict[str, object]:
    bounded = text[:18_500]
    return {"hookSpecificOutput": {"additionalContext": bounded, "hookEventName": event}}


def _empty(event: str) -> dict[str, object]:
    return {"hookSpecificOutput": {"hookEventName": event}}


def _deny(event: str, reason: str) -> dict[str, object]:
    return {"hookSpecificOutput": {"hookEventName": event, "permissionDecision": "deny", "permissionDecisionReason": reason}}


def _verify_cwd(store: MemoryStore, value: object) -> None:
    if not isinstance(value, str) or not value:
        raise ClaudeCodeLocalError("Répertoire courant Claude local absent.")
    try:
        Path(value).resolve(strict=False).relative_to(store.workspace.project_root.resolve(strict=False))
    except ValueError as exc:
        raise ClaudeCodeLocalError("Répertoire courant Claude hors projet VERA.") from exc


def _session_binding_path(store: MemoryStore) -> Path:
    target = store.locator.runtime_dir / "lifecycle" / "claude-code-local-session.json"
    _safe_parent(target.parent, "runtime lifecycle")
    if target.is_symlink():
        raise ClaudeCodeLocalError("Liaison de session Claude symlinkée refusée.")
    return target


def _read_session_binding(store: MemoryStore) -> dict[str, str] | None:
    target = _session_binding_path(store)
    if not target.exists():
        return None
    if not target.is_file():
        raise ClaudeCodeLocalError("Liaison de session Claude non régulière.")
    try:
        parsed = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClaudeCodeLocalError("Liaison de session Claude illisible.") from exc
    if not isinstance(parsed, dict) or set(parsed) != {"project_id", "session_id"}:
        raise ClaudeCodeLocalError("Liaison de session Claude ambiguë.")
    if parsed.get("project_id") != store.identity.project_id or not isinstance(parsed.get("session_id"), str):
        raise ClaudeCodeLocalError("Liaison de session Claude étrangère ou invalide.")
    return {"project_id": store.identity.project_id, "session_id": str(parsed["session_id"])}


def _claim_session(store: MemoryStore, session_id: str) -> None:
    existing = _read_session_binding(store)
    candidate = {"project_id": store.identity.project_id, "session_id": session_id}
    if existing is not None and existing != candidate:
        raise ClaudeCodeLocalError("Conflit : une autre session Claude locale est déjà active pour ce projet.")
    if existing is None:
        _atomic_write(_session_binding_path(store), _canonical_json(candidate), ".vera-claude-session-")


def _release_session(store: MemoryStore, session_id: str) -> None:
    target = _session_binding_path(store)
    binding = _read_session_binding(store)
    if binding is not None and binding["session_id"] == session_id:
        try:
            target.unlink()
        except OSError as exc:
            raise ClaudeCodeLocalError("Libération de session Claude locale impossible.") from exc


def _acknowledgement_tool_name(store: MemoryStore) -> str:
    return f"mcp__vera-mmu-{store.identity.project_id}__mmu_acknowledge_resume"


def _settings_target(store: MemoryStore, *, create: bool = True) -> Path:
    directory = store.workspace.project_root / ".claude"
    if directory.is_symlink():
        raise ClaudeCodeLocalError("Répertoire .claude symlinké refusé.")
    if create:
        _safe_parent(directory, "répertoire .claude")
    elif directory.exists() and not directory.is_dir():
        raise ClaudeCodeLocalError("Répertoire .claude ambigu ou non régulier.")
    target = directory / "settings.json"
    if target.is_symlink():
        raise ClaudeCodeLocalError("La cible .claude/settings.json ne peut pas être un lien symbolique.")
    return target


def _mcp_target(store: MemoryStore) -> Path:
    target = store.workspace.project_root / ".mcp.json"
    if target.is_symlink():
        raise ClaudeCodeLocalError("La cible .mcp.json ne peut pas être un lien symbolique.")
    return target


def _installation_state_path(store: MemoryStore, *, create: bool = True) -> Path:
    target = store.locator.runtime_dir / "generated" / "claude-code-local-install.json"
    if target.parent.is_symlink():
        raise ClaudeCodeLocalError("Runtime généré symlinké refusé.")
    if create:
        _safe_parent(target.parent, "runtime généré")
    elif target.parent.exists() and not target.parent.is_dir():
        raise ClaudeCodeLocalError("Runtime généré ambigu ou non régulier.")
    if target.is_symlink():
        raise ClaudeCodeLocalError("État d’installation Claude local symlinké refusé.")
    return target


def _safe_parent(directory: Path, label: str) -> None:
    if directory.is_symlink():
        raise ClaudeCodeLocalError(f"{label} symlinké refusé.")
    try:
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    except OSError as exc:
        raise ClaudeCodeLocalError(f"Création de {label} impossible.") from exc
    if not directory.is_dir() or directory.is_symlink():
        raise ClaudeCodeLocalError(f"{label} ambigu ou non régulier.")


def _load_json_object(target: Path, label: str) -> dict[str, Any]:
    if not target.exists():
        return {}
    if not target.is_file():
        raise ClaudeCodeLocalError(f"La cible {label} doit être un fichier régulier.")
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClaudeCodeLocalError(f"La cible {label} n’est pas un JSON lisible.") from exc
    if not isinstance(value, dict):
        raise ClaudeCodeLocalError(f"La cible {label} doit contenir un objet JSON.")
    return value


def _read_optional_text(target: Path) -> str | None:
    if not target.exists():
        return None
    if not target.is_file() or target.is_symlink():
        raise ClaudeCodeLocalError("État d’installation Claude local non régulier.")
    try:
        return target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ClaudeCodeLocalError("État d’installation Claude local illisible.") from exc


def _plan_payload(plan: ClaudeCodeLocalPlan) -> dict[str, Any]:
    if not isinstance(plan, ClaudeCodeLocalPlan) or plan.plan_hash != sha256(plan.json_text.encode("utf-8")).hexdigest():
        raise ClaudeCodeLocalError("Plan Claude local altéré.")
    try:
        payload = json.loads(plan.json_text)
        result = payload["claudeCodeLocal"]
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ClaudeCodeLocalError("Plan Claude local illisible.") from exc
    if not isinstance(result, dict):
        raise ClaudeCodeLocalError("Plan Claude local hors format fermé.")
    return result


def _merge_hooks(existing: dict[str, Any], desired: object) -> tuple[dict[str, Any], bool]:
    if not isinstance(desired, dict):
        raise ClaudeCodeLocalError("Hooks Claude locaux attestés invalides.")
    existing_hooks = existing.get("hooks", {})
    if not isinstance(existing_hooks, dict):
        raise ClaudeCodeLocalError("hooks existant doit être un objet JSON.")
    merged = dict(existing)
    hooks = {key: list(value) if isinstance(value, list) else value for key, value in existing_hooks.items()}
    changed = False
    for event, groups in desired.items():
        if not isinstance(event, str) or not isinstance(groups, list):
            raise ClaudeCodeLocalError("Groupe de hook Claude local invalide.")
        current = hooks.get(event, [])
        if not isinstance(current, list):
            raise ClaudeCodeLocalError("Événement de hooks existant doit être une liste.")
        # Un groupe portant la commande de hook VERA est un groupe que VERA a écrit : personne
        # d'autre n'invoque `claude-code-local-hook --profile`. Le remplacer est donc la mise à
        # jour de notre propre trace, pas l'écrasement du travail d'autrui — dont les groupes,
        # eux, sont conservés tels quels à leur place.
        #
        # **Le défaut mesuré.** La version précédente refusait tout groupe VERA différent du
        # nouveau : « Conflit : hook VERA Claude local existant divergent ». Comme le plan change
        # dès que le playbook, les policies ou une capability changent, la moindre modification
        # légitime rendait le projet impossible à réinstaller.
        conserves = [groupe for groupe in current if not _contains_vera_hook(groupe)]
        fusionnes = [*conserves, *groups]
        if fusionnes != current:
            hooks[event] = fusionnes
            changed = True
    if changed:
        merged["hooks"] = hooks
    return merged, changed


def _contains_vera_hook(group: object) -> bool:
    if not isinstance(group, dict):
        return False
    handlers = group.get("hooks")
    return isinstance(handlers, list) and any(
        isinstance(handler, dict)
        and isinstance(handler.get("command"), str)
        # Les deux formes comptent : le script console, et la CLI autonome avec sa sous-commande.
        # N'en reconnaître qu'une ferait passer une installation valide pour étrangère.
        and (handler["command"].startswith(HOOK_ENTRYPOINT + " ") or f" {HOOK_SUBCOMMAND} --profile" in handler["command"])
        for handler in handlers
    )


def _merge_local_server(existing: dict[str, Any], desired: object, generic: Mapping[str, object]) -> tuple[dict[str, Any], bool]:
    if not isinstance(desired, dict):
        raise ClaudeCodeLocalError("Serveur MCP Claude local attesté invalide.")
    server_id = desired.get("id")
    server = {key: value for key, value in desired.items() if key != "id"}
    if not isinstance(server_id, str) or not server_id:
        raise ClaudeCodeLocalError("Identifiant serveur MCP Claude local invalide.")
    servers = existing.get("mcpServers", {})
    if not isinstance(servers, dict):
        raise ClaudeCodeLocalError("mcpServers existant doit être un objet JSON.")
    current = servers.get(server_id)
    if current == server:
        return existing, False
    # `vera-mmu-<project_id>` est un espace de noms que VERA possède : une entrée qui s'y trouve
    # est une entrée que VERA a écrite. La remplacer met à jour notre propre trace ; les autres
    # serveurs du fichier, eux, ne sont jamais touchés — mesuré sur un dépôt réel dont le serveur
    # `aret-memory` a survécu intact à l'installation.
    #
    # **Le défaut mesuré.** La version précédente n'acceptait de remplacer que la forme générique,
    # donc jamais une entrée déjà écrite par VERA : « Conflit : serveur MCP VERA existant
    # divergent ». Or le plan change dès qu'on touche au playbook — ce que le produit demande
    # explicitement de faire. Éditer son propre playbook rendait donc le projet inréparable :
    # `install` refusait, `repair` répondait `NOTHING_TO_REPAIR`, et le serveur déclaré ne
    # démarrait plus.
    del generic
    merged = dict(existing)
    merged_servers = dict(servers)
    merged_servers[server_id] = server
    merged["mcpServers"] = merged_servers
    return merged, True


def _hooks_installed(settings: Mapping[str, object], desired: object) -> bool:
    return isinstance(desired, dict) and isinstance(settings.get("hooks"), dict) and all(
        isinstance(settings["hooks"].get(event), list) and all(group in settings["hooks"][event] for group in groups)
        for event, groups in desired.items()
    )


def _server_installed(mcp: Mapping[str, object], desired: object) -> bool:
    if not isinstance(desired, dict):
        return False
    server_id = desired.get("id")
    server = {key: value for key, value in desired.items() if key != "id"}
    servers = mcp.get("mcpServers")
    return isinstance(server_id, str) and isinstance(servers, dict) and servers.get(server_id) == server


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _atomic_write(target: Path, text: str, prefix: str) -> None:
    _safe_parent(target.parent, "répertoire cible")
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=target.parent, prefix=prefix, suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, target)
    except OSError as exc:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
        raise ClaudeCodeLocalError("Écriture atomique Claude locale impossible.") from exc


def _load_installed_plan(store: MemoryStore) -> ClaudeCodeLocalPlan:
    raw = _read_optional_text(_installation_state_path(store))
    if raw is None:
        raise ClaudeCodeLocalError("Adapter Claude local non installé : état attesté absent.")
    try:
        payload = json.loads(raw)["claudeCodeLocal"]
        bindings = tuple((str(item["capability_id"]), str(item["adapter_id"])) for item in payload["adapterBindings"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ClaudeCodeLocalError("État d’installation Claude local hors format fermé.") from exc
    manifest = compile_mcp_manifest(store, adapter_bindings=dict(bindings))
    instructions = compile_mcp_instructions(store, manifest)
    integration = compile_mcp_integration(store, manifest, instructions)
    hooks = compile_mcp_hook_plan(store, manifest, instructions, integration)
    review = compile_claude_code_integration_plan(store, manifest, instructions, integration, hooks)
    lifecycle = compile_lifecycle_adapter_plan(
        store,
        manifest,
        adapter_id=CLAUDE_CODE_LOCAL_ADAPTER_ID,
        adapter_version=CLAUDE_CODE_LOCAL_ADAPTER_VERSION,
        maximum_guard_mode=CLAUDE_CODE_LOCAL_MAXIMUM_GUARD_MODE,
    )
    plan = compile_claude_code_local_plan(store, manifest, instructions, integration, hooks, review, lifecycle)
    if plan.json_text != raw:
        raise ClaudeCodeLocalError(
            "État d’installation Claude local périmé ou altéré : " + _describe_drift(raw, plan)
        )
    return plan


def _describe_drift(raw: str, plan: ClaudeCodeLocalPlan) -> str:
    """Nomme ce qui a changé depuis l'installation, plutôt que de constater qu'il a changé.

    **Pourquoi ce détail vaut son code.** Le refus précédent disait « périmé ou altéré » et rien
    d'autre. Il est correct, il est fail-closed — et il est indiagnosticable : rien n'indique s'il
    faut réinstaller, revenir en arrière, ou chercher ailleurs. Mesuré en le rencontrant
    moi-même sur un cas où la cause était la résolution de l'entry point, invisible depuis le
    message ; il a fallu recompiler le plan à la main sous deux environnements pour la trouver.

    C'est la classe de défaut déjà corrigée deux fois ici : *un refus qui tait ses valeurs oblige
    à lire le code pour s'en servir.* La comparaison se fait clé par clé, et les deux valeurs sont
    nommées quand elles tiennent sur une ligne — c'est presque toujours le cas de celle qui
    compte, la commande.
    """
    try:
        ancien = json.loads(raw)["claudeCodeLocal"]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return "l’état enregistré n’est plus lisible ; réinstaller l’adapter."
    nouveau = _plan_payload(plan)
    differences: list[str] = []
    for cle in sorted(set(ancien) | set(nouveau)):
        avant, apres = ancien.get(cle), nouveau.get(cle)
        if avant == apres:
            continue
        if cle == "inputs" and isinstance(avant, dict) and isinstance(apres, dict):
            fichiers = sorted(nom for nom in set(avant) | set(apres) if avant.get(nom) != apres.get(nom))
            differences.append("les fichiers " + ", ".join(f"`{nom}`" for nom in fichiers) + " ont changé")
            continue
        if cle == "mcpServer" and isinstance(avant, dict) and isinstance(apres, dict):
            if avant.get("command") != apres.get("command"):
                differences.append(
                    f"la commande attestée était `{avant.get('command')}`, celle-ci serait `{apres.get('command')}`"
                )
                continue
        differences.append(f"`{cle}` diffère")
    if not differences:  # pragma: no cover - un écart sans clé divergente serait un bug de sérialisation
        return "la sérialisation diffère sans qu’aucune clé ne diverge."
    return (
        "; ".join(differences)
        + ". Relancer `install … --apply-project --confirm` pour réattester, après relecture du preview."
    )


#: Le runner auquel `mcp_compiler` lie cet adapter ; le staging et la configuration doivent
#: compiler le manifeste sur la même liaison, sinon le plan produit ne serait pas celui que
#: `compile` atteste.
CLAUDE_CODE_LOCAL_BINDING = "claude-code-local-deny-v1"


def _local_snapshots(store: MemoryStore) -> tuple[
    MCPManifest, MCPInstructions, MCPIntegration, MCPHookPlan, ClaudeCodeIntegrationPlan, LifecycleAdapterPlan, ClaudeCodeLocalPlan
]:
    """Recompile the whole attested chain the local plan is bound to, from the store alone."""
    rows = store.connection.execute(
        "SELECT capability_id FROM capability_policy WHERE decision = 'ALLOW' ORDER BY capability_id"
    ).fetchall()
    bindings = {str(row["capability_id"]): CLAUDE_CODE_LOCAL_BINDING for row in rows}
    if not bindings:
        raise ClaudeCodeLocalError("Aucune capability ALLOW à exposer pour Claude local.")
    manifest = compile_mcp_manifest(store, adapter_bindings=bindings)
    instructions = compile_mcp_instructions(store, manifest)
    integration = compile_mcp_integration(store, manifest, instructions)
    hooks = compile_mcp_hook_plan(store, manifest, instructions, integration)
    review = compile_claude_code_integration_plan(store, manifest, instructions, integration, hooks)
    lifecycle = compile_lifecycle_adapter_plan(
        store,
        manifest,
        adapter_id=CLAUDE_CODE_LOCAL_ADAPTER_ID,
        adapter_version=CLAUDE_CODE_LOCAL_ADAPTER_VERSION,
        maximum_guard_mode=CLAUDE_CODE_LOCAL_MAXIMUM_GUARD_MODE,
    )
    plan = compile_claude_code_local_plan(store, manifest, instructions, integration, hooks, review, lifecycle)
    return manifest, instructions, integration, hooks, review, lifecycle, plan


def stage_claude_code_local_runtime(
    store: MemoryStore, plan: ClaudeCodeLocalPlan, *, confirm: bool
) -> ClaudeCodeLocalInstallResult:
    """Write only the local lifecycle state, never the host settings, after confirmation.

    Le staging est la moitié réversible de l’installation : il fige le plan attesté sous
    `.vera-mmu/`, sans jamais toucher `.claude/settings.json` ni `.mcp.json`. `install` lit
    ensuite cet état et refuse s’il diverge, si bien que stager puis installer reste cohérent.
    """
    if confirm is not True:
        raise ClaudeCodeLocalError("Staging Claude local refusé sans confirmation explicite.")
    if plan != _local_snapshots(store)[-1]:
        raise ClaudeCodeLocalError("Plan Claude local périmé, altéré ou étranger.")
    state_path = _installation_state_path(store)
    existing = _read_optional_text(state_path)
    if existing is not None and existing != plan.json_text:
        raise ClaudeCodeLocalError("État d’installation lifecycle local divergent : refus sans écriture.")
    if existing == plan.json_text:
        return ClaudeCodeLocalInstallResult(
            "UNCHANGED", _settings_target(store, create=False), _mcp_target(store), state_path, plan.plan_hash
        )
    _atomic_write(state_path, plan.json_text, ".vera-claude-state-")
    return ClaudeCodeLocalInstallResult(
        "STAGED", _settings_target(store, create=False), _mcp_target(store), state_path, plan.plan_hash
    )


def claude_code_local_config_main(argv: Sequence[str] | None = None) -> int:
    """Preview, then on `--apply-project --confirm` install, the project-local Claude host config.

    C’est l’entry point que `ADAPTER_CATALOG` nommait depuis le début et que personne n’avait
    écrit : `vmmu install --adapter claude-code-local` et `vmmu configure` le routent tous deux.
    Le contrat d’arguments est celui que `__main__` envoie — `--profile`, puis `--apply-project`
    et `--confirm` — et il est identique aux cinq autres adapters.
    """
    parser = argparse.ArgumentParser(description="Configuration hôte Claude Code local VERA-MMU")
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--apply-project", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args(argv)
    try:
        from .identity import load_profile

        with MemoryStore.open(load_profile(args.profile), args.profile) as store:
            manifest, instructions, integration, hooks, review, lifecycle, plan = _local_snapshots(store)
            if args.apply_project:
                result = install_claude_code_local(
                    store, manifest, instructions, integration, hooks, review, lifecycle, plan, confirm=args.confirm
                )
                payload = {
                    "ok": True,
                    "coverage": CLAUDE_CODE_LOCAL_MAXIMUM_GUARD_MODE,
                    "mcpPath": str(result.mcp_path),
                    "planHash": result.plan_hash,
                    "settingsPath": str(result.settings_path),
                    "statePath": str(result.state_path),
                    "status": result.status,
                }
            else:
                report = inspect_claude_code_local(
                    store, manifest, instructions, integration, hooks, review, lifecycle, plan
                )
                payload = {
                    "ok": True,
                    "checks": [{"name": name, "status": status} for name, status in report.checks],
                    "coverage": CLAUDE_CODE_LOCAL_MAXIMUM_GUARD_MODE,
                    "mcpPath": str(_mcp_target(store)),
                    "planHash": plan.plan_hash,
                    "settingsPath": str(_settings_target(store, create=False)),
                    "statePath": str(_installation_state_path(store, create=False)),
                    "status": "PREVIEW",
                    "installedStatus": report.status,
                }
    except StoreError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


def claude_code_local_stage_main(argv: Sequence[str] | None = None) -> int:
    """Stage the attested local lifecycle runtime after confirmation, touching no host file."""
    parser = argparse.ArgumentParser(description="Staging runtime Claude Code local VERA-MMU")
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args(argv)
    try:
        from .identity import load_profile

        with MemoryStore.open(load_profile(args.profile), args.profile) as store:
            result = stage_claude_code_local_runtime(store, _local_snapshots(store)[-1], confirm=args.confirm)
    except StoreError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2
    print(
        json.dumps(
            {"ok": True, "planHash": result.plan_hash, "statePath": str(result.state_path), "status": result.status},
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


def claude_code_local_hook_main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hook lifecycle Claude Code local VERA-MMU")
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--event", choices=_EVENTS, required=True)
    args = parser.parse_args(argv)
    try:
        payload = json.loads(sys.stdin.read())
        if not isinstance(payload, dict):
            raise ClaudeCodeLocalError("Payload JSON de hook Claude requis.")
        from .identity import load_profile
        with MemoryStore.open(load_profile(args.profile), args.profile) as store:
            plan = _load_installed_plan(store)
            manifest = compile_mcp_manifest(store, adapter_bindings=dict(plan.adapter_bindings))
            lifecycle = compile_lifecycle_adapter_plan(
                store,
                manifest,
                adapter_id=CLAUDE_CODE_LOCAL_ADAPTER_ID,
                adapter_version=CLAUDE_CODE_LOCAL_ADAPTER_VERSION,
                maximum_guard_mode=CLAUDE_CODE_LOCAL_MAXIMUM_GUARD_MODE,
            )
            response = handle_claude_code_local_hook(store, lifecycle, plan, args.event, payload)
    except (StoreError, json.JSONDecodeError) as exc:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": args.event, "permissionDecision": "deny", "permissionDecisionReason": str(exc)}}, ensure_ascii=False))
        return 2
    print(json.dumps(response, ensure_ascii=False, sort_keys=True))
    return 0


def claude_code_local_mcp_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Serveur MCP lifecycle Claude Code local VERA-MMU")
    parser.add_argument("--profile", type=Path, required=True)
    args = parser.parse_args(argv)
    from .identity import load_profile
    with MemoryStore.open(load_profile(args.profile), args.profile) as store:
        plan = _load_installed_plan(store)
        manifest = compile_mcp_manifest(store, adapter_bindings=dict(plan.adapter_bindings))
        instructions = compile_mcp_instructions(store, manifest)
        lifecycle = compile_lifecycle_adapter_plan(
            store,
            manifest,
            adapter_id=CLAUDE_CODE_LOCAL_ADAPTER_ID,
            adapter_version=CLAUDE_CODE_LOCAL_ADAPTER_VERSION,
            maximum_guard_mode=CLAUDE_CODE_LOCAL_MAXIMUM_GUARD_MODE,
        )
        server = create_server(
            store,
            runtime_adapter=DenyRuntimeAdapter(),
            manifest=manifest,
            instructions=instructions,
            lifecycle_adapter_registry=LifecycleAdapterRegistry((ClaudeCodeLocalSessionAdapter(store),)),
            lifecycle_adapter_plan=lifecycle,
            actor="vera-claude-code-local",
        )
        server.run("stdio")


if __name__ == "__main__":
    raise SystemExit(claude_code_local_hook_main())

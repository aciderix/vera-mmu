"""Test de parité du couplage `C15` — barrière de reprise ARET V1 contre garde VERA.

Le registre exige, pour promouvoir `C15` : « Fresh session, PostCompact, mode dégradé,
acknowledgement expiré, identité absente, kill-switch et Stop one-shot ». Les sept dimensions sont
couvertes ici, chacune en **exécutant** les deux moteurs sur la même situation.

**ARET est exécuté, pas lu.** `C15` porte sur une machine à états : une barrière s'arme, refuse une
action, se lève sur un acquittement, se réarme après compaction. Rien de tout cela ne se lit dans
le code — chaque transition dépend d'un fichier d'état réel, d'un payload réel, d'un environnement
réel. Les quatre hooks d'ARET sont versionnés, épinglés et chargés par
`tests/aret_v1_hooks_reference.py` ; `session_start.handler` et `post_compact.handler` tournent ici
sur un vrai `MemoryStore` ARET et écrivent un vrai fichier d'état.

**Ce qu'ARET fait bien, et que VERA a repris sans rien y retrancher.** Cinq choses, toutes mesurées
plus bas :

1. *Le kill-switch existe.* Son propre commentaire dit pourquoi — « une barrière ne doit jamais
   pouvoir s'armer sans issue » — et il vient d'un deadlock réellement vécu. VERA le reprend et
   honore même le nom de variable d'ARET, pour qu'un opérateur qui connaît l'un débloque l'autre.
2. *Le mode dégradé ne bloque pas dur.* Sur une mémoire cassée, imposer un rituel rigide sans voie
   de sortie fiable enferme l'agent. ARET arme quand même, injecte un contexte bruyant, et laisse
   passer. VERA fait la même chose.
3. *L'armement a lieu dans tous les cas.* Mesuré : sur une mémoire ARET vierge, le dossier est
   dégradé et `SessionStart` arme malgré tout — le fail-open silencieux est éliminé.
4. *`resume` préserve l'acquittement.* En session web/async, `SessionStart` se redéclenche à chaque
   tour ; réarmer rebloquerait un agent vivant à chaque échange. ARET distingue ce cas, VERA aussi.
5. *L'état reste éphémère et local* — sous `runtime/`, jamais dans SQLite ni dans Git. Vérifié des
   deux côtés en réhachant la base après un armement et un acquittement.

**La divergence porte sur ce qui arrive quand la barrière elle-même est en défaut.** Trois mesures,
toutes du même genre, et c'est exactement ce que `I014` nomme :

*Un état illisible désarme ARET.* `load_state` rend `None` sur un JSON corrompu comme sur un état
de version 2, et `decision` rend alors `None` : aucune décision, donc aucun blocage. La barrière
disparaît précisément là où elle devait tenir. `_read_existing` de VERA lève, et `precheck` refuse.

*Un état acquitté se transplante entre mémoires ARET.* Sa clef est `sha256(identité)[:24]`, sans
aucune identité de projet : le même fichier, copié dans une autre mémoire, y lève la barrière.
Celle de VERA porte `projectId`, `projectHash` et `profileHash`, et sa clef les inclut ; les quatre
couches sont isolées une à une plus bas.

*L'emplacement de l'état suit le payload.* Les wrappers d'ARET lisent `payload["memory_dir"]` avant
l'environnement : un payload qui nomme un autre répertoire ne trouve pas d'état, et la barrière
laisse passer. Celui de VERA vient du store déjà lié, jamais d'une entrée (`I008`).

**Un défaut de VERA trouvé par ce lot, et corrigé.** `precheck` consultait le kill-switch *après*
avoir lu l'état : avec un état illisible, la voie de sortie documentée ne fonctionnait plus — le
cas où l'opérateur en a le plus besoin. Le kill-switch est désormais consulté en premier, comme
chez ARET. Le test `test_kill_switch_lifts_a_state_integrity_denial` l'épingle.

Le comportement propre de VERA est déjà éprouvé par `tests/test_session_lifecycle.py`. Ces
tests-là comparent VERA à ses propres attentes ; celui-ci le confronte à ARET sur les mêmes
situations.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from vera_mmu.identity import load_profile
from vera_mmu.session_lifecycle import (
    GuardDecision,
    LifecycleError,
    ResumeDossierService,
    ResumeGuardService,
    ResumeSectionRequirement,
    barrier_disabled,
)
from vera_mmu.store import MemoryStore

from tests.aret_v1_baseline import temporary_root
from tests.aret_v1_hooks_reference import (
    COMMON_SHA256,
    POST_COMPACT_SHA256,
    RESUME_GUARD_SHA256,
    SESSION_START_SHA256,
    aret_hook_common,
    aret_post_compact,
    aret_resume_guard,
    aret_session_start,
    hook_digest,
)
from tests.aret_v1_repository_reference import memory_store


#: Les six volets du rituel ARET, avec leurs minimums, tels que `RITUAL_FIELDS` les fixe.
ARET_RITUAL = {
    "working_rules": 80,
    "current_state": 60,
    "capabilities": 80,
    "git_state": 40,
    "risks_and_limits": 60,
    "next_action": 30,
}
#: Un hash de contrat valide au sens d'ARET : 64 caractères hexadécimaux.
CONTRACT_A = "a" * 64
CONTRACT_B = "b" * 64

PROFILE = """
mmu:
  version: "2.0"
project:
  id: "{project_id}"
  name: "C15 Parity"
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

#: Le contrat de sections côté VERA. Il est déclaré par le projet, non gravé dans le moteur.
REQUIREMENTS = (
    ResumeSectionRequirement("working-rules", 12, 256),
    ResumeSectionRequirement("current-state", 12, 256),
    ResumeSectionRequirement("next-action", 12, 256),
)


def vera_sections(suffix: str = "") -> dict[str, str]:
    return {
        "working-rules": "Mesurer avant de conclure." + suffix,
        "current-state": "Le lot est borné et daté." + suffix,
        "next-action": "Écrire les tests ciblés." + suffix,
    }


def aret_recap(contract_hash: str = CONTRACT_A, **overrides: str) -> dict[str, str]:
    """Un récapitulatif ARET juste assez long pour satisfaire les six minimums du rituel."""
    recap = {field: "x" * minimum for field, minimum in ARET_RITUAL.items()}
    recap["resume_contract_hash"] = contract_hash
    recap.update(overrides)
    return recap


def acknowledgement(payload: dict[str, object], recap: dict[str, str], **extra: object) -> dict[str, object]:
    """Le payload PostToolUse qu'ARET reconnaît comme une attestation de reprise."""
    return {**payload, "tool_name": "mcp__aret_mmu__aret_acknowledge_resume", "tool_input": recap, **extra}


class C15ResumeGuardParityTests(unittest.TestCase):
    """Sept dimensions, deux moteurs, la même situation posée aux deux."""

    # ----------------------------------------------------------------- outillage

    def vera_store(self, directory: Path, project_id: str = "c15-parity") -> MemoryStore:
        directory.mkdir(parents=True, exist_ok=True)
        profile_path = directory / "project.yaml"
        profile_path.write_text(PROFILE.format(project_id=project_id), encoding="utf-8")
        return MemoryStore.open(load_profile(profile_path), profile_path)

    def vera_dossier(self, store: MemoryStore, suffix: str = ""):
        return ResumeDossierService(store).compile(REQUIREMENTS, vera_sections(suffix))

    # ------------------------------------------------- la référence est bien celle épinglée

    def test_references_are_the_pinned_aret_hooks(self) -> None:
        """Quatre empreintes. Une référence qui dérive mesure autre chose que ce qu'on croit."""
        for name, expected in (
            ("resume_guard.py", RESUME_GUARD_SHA256),
            ("common.py", COMMON_SHA256),
            ("session_start.py", SESSION_START_SHA256),
            ("post_compact.py", POST_COMPACT_SHA256),
        ):
            with self.subTest(hook=name):
                self.assertEqual(hook_digest(name), expected)

    def test_the_aret_ritual_is_fixed_in_code_where_veras_is_declared_by_the_project(self) -> None:
        """Première divergence de forme : qui décide de la forme du rituel.

        Les six volets d'ARET et leurs minimums sont des constantes de module ; les changer
        demande d'éditer le moteur. Le contrat de VERA est déclaré par le projet, transporté dans
        le dossier et **inclus dans son empreinte** : changer un minimum change le contrat, donc
        invalide l'acquittement précédent sans qu'aucune ligne de moteur bouge.
        """
        guard = aret_resume_guard()
        self.assertEqual({field: minimum for field, _, minimum in guard.RITUAL_FIELDS}, ARET_RITUAL)
        with TemporaryDirectory() as directory:
            with self.vera_store(Path(directory)) as store:
                service = ResumeDossierService(store)
                declared = service.compile(REQUIREMENTS, vera_sections())
                widened = service.compile(
                    (ResumeSectionRequirement("working-rules", 13, 256), *REQUIREMENTS[1:]),
                    vera_sections(),
                )
                self.assertNotEqual(declared.resume_contract_hash, widened.resume_contract_hash)
                carried = json.loads(declared.json_text)["resumeDossier"]["requirements"]
                self.assertEqual(
                    carried,
                    [{"id": r.identifier, "maximum": r.maximum_characters, "minimum": r.minimum_characters} for r in REQUIREMENTS],
                )

    # --------------------------------------------------------- 1. session neuve

    def test_i012_i013_a_fresh_session_arms_and_the_first_action_is_refused(self) -> None:
        """Dimension « Fresh session » : les deux arment et les deux refusent la première action."""
        guard = aret_resume_guard()
        with temporary_root() as root:
            memory = root / ".aret-memory"
            memory.mkdir()
            payload = {"session_id": "sess-fresh"}
            state = guard.arm(memory, payload, reason="startup", resume_contract_hash=CONTRACT_A)
            self.assertEqual((state["version"], state["status"], state["mode"]), (3, "awaiting_recap", "hard"))
            self.assertIsNone(state["acknowledged_at"])
            self.assertTrue(guard.state_path(memory, payload).is_file())
            decision = guard.decision(memory, payload)
            self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("récapitulatif rituel", decision["hookSpecificOutput"]["permissionDecisionReason"])

        with TemporaryDirectory() as directory:
            with self.vera_store(Path(directory)) as store:
                service = ResumeGuardService(store)
                dossier = self.vera_dossier(store)
                armed = service.arm("sess-fresh", "c15-adapter", "SESSION_OPEN", dossier, mode="HARD")
                self.assertEqual((armed.status, armed.mode), ("ARMED", "HARD"))
                self.assertIsNone(armed.acknowledged_at)
                self.assertTrue(service.state_path("sess-fresh", "c15-adapter").is_file())
                self.assertEqual(service.precheck("sess-fresh", "c15-adapter").decision, GuardDecision.DENY)

    def test_the_real_sessionstart_hook_arms_soft_on_a_virgin_aret_memory(self) -> None:
        """Le hook réel, exécuté : une mémoire ARET neuve produit un dossier **dégradé**.

        C'est mesuré, pas supposé, et ce n'est pas un reproche : l'armement a bien lieu, le
        contexte injecté commence par un avertissement, et le nudge Stop reste actif. Mais un ARET
        fraîchement installé ne bloque pas dur, et cela ne se lit nulle part dans le code.
        """
        guard = aret_resume_guard()
        common = aret_hook_common()
        with temporary_root() as root:
            store = memory_store(root / ".aret-memory")
            try:
                context, degraded = common.resume_context_or_degraded(store)
                self.assertTrue(degraded)
                self.assertEqual(len(context["resume_dossier"]["contract_hash"]), 64)

                payload = {"session_id": "sess-hook", "source": "startup"}
                result = aret_session_start().handler(store, payload)
                self.assertTrue(result["degraded"])
                self.assertEqual(result["resume_guard"]["status"], "awaiting_recap")
                self.assertEqual(result["resume_ritual"]["tool"], "aret_acknowledge_resume")

                state = guard.load_state(store.memory_dir, payload)
                self.assertEqual(state["mode"], "soft")
                self.assertIsNone(guard.decision(store.memory_dir, payload))
                self.assertIsNotNone(guard.stop_feedback(store.memory_dir, payload))

                injected = common.additional_context(result)
                self.assertIn("REPRISE DÉGRADÉE", injected.splitlines()[0])
                self.assertLessEqual(len(injected.encode("utf-8")), common.HOOK_CONTEXT_MAX_BYTES)
            finally:
                del store

    # ------------------------------------------------------------ 2. PostCompact

    def test_i013_postcompact_re_forces_the_ritual_on_both_engines(self) -> None:
        """Dimension « PostCompact » : une perte de contexte réarme et rebloque des deux côtés."""
        guard = aret_resume_guard()
        with temporary_root() as root:
            memory = root / ".aret-memory"
            memory.mkdir()
            payload = {"session_id": "sess-compact"}
            guard.arm(memory, payload, reason="startup", resume_contract_hash=CONTRACT_A)
            guard.acknowledge(memory, acknowledgement(payload, aret_recap()))
            self.assertIsNone(guard.decision(memory, payload))

            rearmed = guard.arm(memory, payload, reason="PostCompact", resume_contract_hash=CONTRACT_B)
            self.assertEqual(rearmed["status"], "awaiting_recap")
            self.assertIsNone(rearmed["acknowledged_at"])
            self.assertIsNotNone(guard.decision(memory, payload))

        with TemporaryDirectory() as directory:
            with self.vera_store(Path(directory)) as store:
                service = ResumeGuardService(store)
                first = self.vera_dossier(store)
                second = self.vera_dossier(store, " Après compaction.")
                service.arm("sess-compact", "c15-adapter", "SESSION_OPEN", first, mode="HARD")
                self.assertTrue(service.acknowledge("sess-compact", "c15-adapter", first.resume_contract_hash, vera_sections()))
                self.assertEqual(service.precheck("sess-compact", "c15-adapter").decision, GuardDecision.ALLOW)

                restored = service.arm("sess-compact", "c15-adapter", "CONTEXT_RESTORED", second, mode="HARD")
                self.assertEqual(restored.status, "ARMED")
                self.assertIsNone(restored.acknowledged_at)
                self.assertEqual(service.precheck("sess-compact", "c15-adapter").decision, GuardDecision.DENY)

    def test_the_real_postcompact_hook_rearms_with_its_own_reason(self) -> None:
        """Le hook PostCompact réel, exécuté sur la même mémoire qu'un `SessionStart` déjà armé."""
        guard = aret_resume_guard()
        with temporary_root() as root:
            store = memory_store(root / ".aret-memory")
            try:
                payload = {"session_id": "sess-compact-hook"}
                aret_session_start().handler(store, {**payload, "source": "startup"})
                compacted = aret_post_compact().handler(store, payload)
                self.assertEqual(compacted["resume_guard"]["reason"], "PostCompact")
                self.assertEqual(guard.load_state(store.memory_dir, payload)["reason"], "PostCompact")
            finally:
                del store

    def test_resume_preserves_the_acknowledgement_and_adopts_the_new_contract_on_both(self) -> None:
        """Une reprise de session vivante ne rebloque pas — accord complet, et son prix.

        Le motif `resume` / `RESUME` existe parce qu'en session web ou asynchrone `SessionStart` se
        redéclenche à chaque tour : réarmer rebloquerait un agent vivant à chaque échange. Les deux
        moteurs préservent donc l'acquittement.

        Mesuré aussi, et il faut le dire : les deux **adoptent le nouveau hash de contrat** en
        gardant l'acquittement. Un acquittement du contrat A vaut donc pour le contrat B. C'est le
        même compromis des deux côtés, il n'oppose pas les moteurs, mais il n'est pas gratuit.
        """
        guard = aret_resume_guard()
        with temporary_root() as root:
            memory = root / ".aret-memory"
            memory.mkdir()
            payload = {"session_id": "sess-resume"}
            guard.arm(memory, payload, reason="startup", resume_contract_hash=CONTRACT_A)
            guard.acknowledge(memory, acknowledgement(payload, aret_recap()))
            resumed = guard.arm(memory, payload, reason="resume", resume_contract_hash=CONTRACT_B)
            self.assertEqual(resumed["status"], "acknowledged")
            self.assertIsNotNone(resumed["acknowledged_at"])
            self.assertEqual(resumed["resume_contract_hash"], CONTRACT_B)
            self.assertIsNone(guard.decision(memory, payload))

        with TemporaryDirectory() as directory:
            with self.vera_store(Path(directory)) as store:
                service = ResumeGuardService(store)
                first = self.vera_dossier(store)
                second = self.vera_dossier(store, " Variante.")
                service.arm("sess-resume", "c15-adapter", "SESSION_OPEN", first, mode="HARD")
                service.acknowledge("sess-resume", "c15-adapter", first.resume_contract_hash, vera_sections())
                resumed = service.arm("sess-resume", "c15-adapter", "RESUME", second, mode="HARD")
                self.assertEqual(resumed.status, "ACKNOWLEDGED")
                self.assertEqual(resumed.resume_contract_hash, second.resume_contract_hash)
                self.assertIsNotNone(resumed.acknowledgement_hash)
                self.assertEqual(service.precheck("sess-resume", "c15-adapter").decision, GuardDecision.ALLOW)

    # ------------------------------------------------------------ 3. mode dégradé

    def test_i014_degraded_mode_never_hard_blocks_but_aret_says_nothing_at_that_moment(self) -> None:
        """Dimension « mode dégradé » : accord sur le principe, écart sur ce qui est dit.

        Les deux refusent de verrouiller sur une mémoire cassée — c'est la leçon du deadlock
        qu'ARET documente dans `arm()`. Mais au moment de l'action, ARET rend `None` : le hôte ne
        reçoit rien, donc l'opérateur ne voit rien. VERA rend `ALLOW_WITH_NOTICE` porteur de sa
        raison. Les deux laissent passer ; un seul dit pourquoi.
        """
        guard = aret_resume_guard()
        with temporary_root() as root:
            memory = root / ".aret-memory"
            memory.mkdir()
            payload = {"session_id": "sess-degraded"}
            soft = guard.arm(memory, payload, reason="startup", resume_contract_hash=CONTRACT_A, ready=False)
            self.assertEqual(soft["mode"], "soft")
            self.assertIsNone(guard.decision(memory, payload))
            self.assertIsNotNone(guard.stop_feedback(memory, payload))

        with TemporaryDirectory() as directory:
            with self.vera_store(Path(directory)) as store:
                service = ResumeGuardService(store)
                degraded = service.arm("sess-degraded", "c15-adapter", "SESSION_OPEN", self.vera_dossier(store), mode="SOFT")
                self.assertEqual(degraded.status, "DEGRADED")
                outcome = service.precheck("sess-degraded", "c15-adapter")
                self.assertEqual(outcome.decision, GuardDecision.ALLOW_WITH_NOTICE)
                self.assertIn("degraded dossier", outcome.reason)
                self.assertEqual(
                    service.session_ending("sess-degraded", "c15-adapter", already_nudged=False).decision,
                    GuardDecision.NUDGE,
                )

    # ------------------------------------------------ 4. acquittement périmé

    def test_i014_a_stale_contract_hash_is_refused_by_both_engines(self) -> None:
        """Dimension « acknowledgement expiré » : acquitter un autre contrat ne lève rien."""
        guard = aret_resume_guard()
        with temporary_root() as root:
            memory = root / ".aret-memory"
            memory.mkdir()
            payload = {"session_id": "sess-stale"}
            guard.arm(memory, payload, reason="startup", resume_contract_hash=CONTRACT_A)
            refused = guard.acknowledge(memory, acknowledgement(payload, aret_recap(CONTRACT_B)))
            self.assertEqual(refused["status"], "awaiting_recap")
            self.assertIsNotNone(guard.decision(memory, payload))

        with TemporaryDirectory() as directory:
            with self.vera_store(Path(directory)) as store:
                service = ResumeGuardService(store)
                armed = self.vera_dossier(store)
                other = self.vera_dossier(store, " Autre.")
                service.arm("sess-stale", "c15-adapter", "SESSION_OPEN", armed, mode="HARD")
                self.assertFalse(service.acknowledge("sess-stale", "c15-adapter", other.resume_contract_hash, vera_sections()))
                self.assertEqual(service.precheck("sess-stale", "c15-adapter").decision, GuardDecision.DENY)

    def test_aret_also_requires_the_tool_name_and_a_successful_tool_response(self) -> None:
        """Deux gardes d'ARET que VERA n'a pas, parce qu'il n'a pas de transport à croire.

        ARET lit le succès de l'outil dans le payload du hôte : un `is_error` ou un `ok:false`
        annule l'acquittement, et le nom d'outil doit finir par `__aret_acknowledge_resume`. VERA
        n'a pas cette surface — `acknowledge` est un appel de Core, pas un compte rendu d'outil.
        """
        guard = aret_resume_guard()
        recap = aret_recap()
        with temporary_root() as root:
            memory = root / ".aret-memory"
            memory.mkdir()
            payload = {"session_id": "sess-tool"}
            for label, extra, tool in (
                ("outil en erreur", {"tool_response": {"is_error": True}}, "x__aret_acknowledge_resume"),
                ("outil isError", {"tool_response": {"isError": True}}, "x__aret_acknowledge_resume"),
                ("structured ok=false", {"tool_response": {"structured_content": {"ok": False}}}, "x__aret_acknowledge_resume"),
                ("texte ok:false", {"tool_response": '{"ok": false}'}, "x__aret_acknowledge_resume"),
                ("autre outil", {}, "mcp__aret_mmu__aret_get_front"),
            ):
                with self.subTest(cas=label):
                    guard.arm(memory, payload, reason="startup", resume_contract_hash=CONTRACT_A)
                    state = guard.acknowledge(memory, {**payload, "tool_name": tool, "tool_input": recap, **extra})
                    self.assertEqual(state["status"], "awaiting_recap")

            guard.arm(memory, payload, reason="startup", resume_contract_hash=CONTRACT_A)
            accepted = guard.acknowledge(memory, acknowledgement(payload, recap, tool_response={"ok": True}))
            self.assertEqual(accepted["status"], "acknowledged")

    def test_a_recap_that_overflows_is_truncated_by_aret_and_refused_by_vera(self) -> None:
        """Les deux bornent le récapitulatif ; un seul le dit à celui qui l'a écrit.

        ARET tronque à 4000 caractères et enregistre l'acquittement comme complet : l'agent croit
        avoir déposé ce qu'il a écrit. VERA refuse et l'acquittement n'a pas lieu. Même souci des
        deux côtés — borner —, deux réponses opposées quand la borne est franchie.
        """
        guard = aret_resume_guard()
        with temporary_root() as root:
            memory = root / ".aret-memory"
            memory.mkdir()
            payload = {"session_id": "sess-long"}
            guard.arm(memory, payload, reason="startup", resume_contract_hash=CONTRACT_A)
            oversized = {field: "y" * 5000 for field in ARET_RITUAL}
            oversized["resume_contract_hash"] = CONTRACT_A
            state = guard.acknowledge(memory, acknowledgement(payload, oversized))
            self.assertEqual(state["status"], "acknowledged")
            self.assertEqual({len(value) for value in state["recap"].values()}, {4000})

            guard.arm(memory, payload, reason="startup", resume_contract_hash=CONTRACT_A)
            short = guard.acknowledge(memory, acknowledgement(payload, aret_recap(working_rules="trop court")))
            self.assertEqual(short["status"], "awaiting_recap")

        with TemporaryDirectory() as directory:
            with self.vera_store(Path(directory)) as store:
                service = ResumeGuardService(store)
                dossier = self.vera_dossier(store)
                service.arm("sess-long", "c15-adapter", "SESSION_OPEN", dossier, mode="HARD")
                for label, sections in (
                    ("trop long", {**vera_sections(), "working-rules": "z" * 5000}),
                    ("trop court", {**vera_sections(), "working-rules": "court"}),
                    ("non normalisé", {**vera_sections(), "working-rules": "  Mesurer avant de conclure.  "}),
                    ("section inconnue", {**vera_sections(), "surplus": "Une section que le contrat ignore."}),
                ):
                    with self.subTest(cas=label):
                        self.assertFalse(
                            service.acknowledge("sess-long", "c15-adapter", dossier.resume_contract_hash, sections)
                        )
                self.assertTrue(service.acknowledge("sess-long", "c15-adapter", dossier.resume_contract_hash, vera_sections()))

    # ------------------------------------------------------- 5. identité absente

    def test_i013_an_absent_session_identity_is_fail_open_on_aret_until_a_state_exists(self) -> None:
        """Dimension « identité absente » : ARET refuse fail-closed, mais seulement s'il a un état.

        `decision` lit l'état **avant** de regarder l'identité. Sans identité, la clef vaut
        `sha256("unscoped")` : tant que personne n'a armé sous cette clef, `load_state` rend `None`
        et la barrière ne rend aucune décision. Deux sessions non identifiées partagent ensuite ce
        même état unique. VERA refuse d'armer sans identité et refuse l'action dans tous les cas.
        """
        guard = aret_resume_guard()
        with temporary_root() as root:
            memory = root / ".aret-memory"
            memory.mkdir()
            anonymous = {"tool_name": "Bash"}
            self.assertIsNone(guard.session_identity(anonymous))
            self.assertIsNone(guard.decision(memory, anonymous))

            guard.arm(memory, anonymous, reason="startup", resume_contract_hash=CONTRACT_A)
            refusal = guard.decision(memory, anonymous)
            self.assertEqual(refusal["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("identité de session absente", refusal["hookSpecificOutput"]["permissionDecisionReason"])
            self.assertEqual(guard.session_key({"tool_name": "Write"}), guard.session_key(anonymous))
            self.assertEqual(
                guard.acknowledge(memory, acknowledgement(anonymous, aret_recap()))["status"], "awaiting_recap"
            )

        with TemporaryDirectory() as directory:
            with self.vera_store(Path(directory)) as store:
                service = ResumeGuardService(store)
                dossier = self.vera_dossier(store)
                for identity in ("", "   ", "a" * 513):
                    with self.subTest(identite=identity[:8]):
                        with self.assertRaises(LifecycleError):
                            service.arm(identity, "c15-adapter", "SESSION_OPEN", dossier, mode="HARD")
                        self.assertEqual(service.precheck(identity, "c15-adapter").decision, GuardDecision.DENY)
                        self.assertFalse(
                            service.acknowledge(identity, "c15-adapter", dossier.resume_contract_hash, vera_sections())
                        )

    # ----------------------------------------------------------- 6. kill-switch

    def test_the_kill_switch_reads_the_same_values_on_both_engines(self) -> None:
        """Dimension « kill-switch » : même vocabulaire, même normalisation, même variable."""
        guard = aret_resume_guard()
        with temporary_root() as root:
            memory = root / ".aret-memory"
            memory.mkdir()
            payload = {"session_id": "sess-kill"}
            guard.arm(memory, payload, reason="startup", resume_contract_hash=CONTRACT_A)
            with TemporaryDirectory() as directory:
                with self.vera_store(Path(directory)) as store:
                    service = ResumeGuardService(store)
                    service.arm("sess-kill", "c15-adapter", "SESSION_OPEN", self.vera_dossier(store), mode="HARD")
                    runtime = store.locator.runtime_dir
                    for value, disabled in (
                        ("1", True), ("true", True), ("TRUE", True), ("yes", True), ("on", True), (" on ", True),
                        ("0", False), ("", False), ("no", False), ("off", False),
                    ):
                        with self.subTest(valeur=value):
                            with patch.dict(os.environ, {"ARET_MMU_BARRIER_OFF": value}, clear=False):
                                self.assertEqual(guard.barrier_disabled(), disabled)
                                self.assertEqual(barrier_disabled(runtime), disabled)
                                self.assertEqual(guard.decision(memory, payload) is None, disabled)
                                expected = GuardDecision.ALLOW_WITH_NOTICE if disabled else GuardDecision.DENY
                                self.assertEqual(service.precheck("sess-kill", "c15-adapter").decision, expected)

    def test_vera_adds_a_second_and_a_third_way_out_and_refuses_a_symlinked_one(self) -> None:
        """Une variable d'environnement se règle au démarrage ; un fichier se pose en cours de route.

        VERA accepte son propre nom de variable, celui d'ARET, et un fichier sentinelle sous le
        runtime — parce qu'une session déjà lancée ne relit pas son environnement. La sentinelle
        est refusée si c'est un lien symbolique : la voie de sortie ne doit pas pouvoir être
        fabriquée en pointant ailleurs.
        """
        with TemporaryDirectory() as directory:
            with self.vera_store(Path(directory)) as store:
                service = ResumeGuardService(store)
                service.arm("sess-out", "c15-adapter", "SESSION_OPEN", self.vera_dossier(store), mode="HARD")
                runtime = store.locator.runtime_dir
                self.assertEqual(service.precheck("sess-out", "c15-adapter").decision, GuardDecision.DENY)

                with patch.dict(os.environ, {"VERA_MMU_BARRIER_OFF": "1"}, clear=False):
                    self.assertEqual(
                        service.precheck("sess-out", "c15-adapter").decision, GuardDecision.ALLOW_WITH_NOTICE
                    )

                sentinel = runtime / "BARRIER_OFF"
                sentinel.write_text("", encoding="utf-8")
                self.assertTrue(barrier_disabled(runtime))
                self.assertEqual(service.precheck("sess-out", "c15-adapter").decision, GuardDecision.ALLOW_WITH_NOTICE)
                sentinel.unlink()

                # La cible du lien **existe** : sans le refus de symlink, `exists()` suffirait à
                # lever la barrière. Un lien vers un fichier absent aurait prouvé la mauvaise règle.
                pointed_at = runtime / "un-fichier-bien-reel"
                pointed_at.write_text("", encoding="utf-8")
                sentinel.symlink_to(pointed_at)
                self.assertTrue(sentinel.exists())
                self.assertFalse(barrier_disabled(runtime))
                self.assertEqual(service.precheck("sess-out", "c15-adapter").decision, GuardDecision.DENY)
                sentinel.unlink()
                pointed_at.unlink()

    def test_kill_switch_lifts_a_state_integrity_denial(self) -> None:
        """Le défaut que ce lot a trouvé dans VERA, et ce qu'il fallait corriger.

        `precheck` lisait l'état avant de consulter le kill-switch : sur un état illisible, la
        voie de sortie documentée ne fonctionnait plus — le cas où l'opérateur en a le plus
        besoin. Le kill-switch est maintenant consulté en premier, comme chez ARET, et l'issue
        reste tracée. ARET n'a pas ce cas, parce qu'un état illisible y désarme déjà la barrière.
        """
        with TemporaryDirectory() as directory:
            with self.vera_store(Path(directory)) as store:
                service = ResumeGuardService(store)
                service.arm("sess-broken", "c15-adapter", "SESSION_OPEN", self.vera_dossier(store), mode="HARD")
                service.state_path("sess-broken", "c15-adapter").write_text("{ pas du json", encoding="utf-8")
                self.assertEqual(service.precheck("sess-broken", "c15-adapter").decision, GuardDecision.DENY)

                with patch.dict(os.environ, {"VERA_MMU_BARRIER_OFF": "1"}, clear=False):
                    outcome = service.precheck("sess-broken", "c15-adapter")
                    self.assertEqual(outcome.decision, GuardDecision.ALLOW_WITH_NOTICE)
                    self.assertIn("emergency barrier override", outcome.reason)
                    self.assertEqual(service.precheck("", "c15-adapter").decision, GuardDecision.ALLOW_WITH_NOTICE)

    # --------------------------------------------------------- 7. Stop one-shot

    def test_the_stop_nudge_is_bounded_to_one_pass_on_both_engines(self) -> None:
        """Dimension « Stop one-shot » : un seul rappel, et l'écart sur qui le fait taire.

        ARET lit un drapeau du payload du hôte, et strictement : `stop_hook_active is True`, si
        bien qu'une chaîne pourtant vraie au sens usuel ne l'éteint pas. VERA reçoit un booléen de
        son adapter. Écart mesuré ensuite : le kill-switch éteint aussi le rappel d'ARET, pas
        celui de VERA — retirer le blocage n'y retire pas la trace.
        """
        guard = aret_resume_guard()
        with temporary_root() as root:
            memory = root / ".aret-memory"
            memory.mkdir()
            payload = {"session_id": "sess-stop"}
            guard.arm(memory, payload, reason="startup", resume_contract_hash=CONTRACT_A)
            nudge = guard.stop_feedback(memory, payload)
            self.assertEqual(nudge["hookSpecificOutput"]["hookEventName"], "Stop")
            self.assertIn("BARRIÈRE DE REPRISE ARET-MMU ACTIVE", nudge["hookSpecificOutput"]["additionalContext"])
            self.assertIsNone(guard.stop_feedback(memory, {**payload, "stop_hook_active": True}))
            self.assertIsNotNone(guard.stop_feedback(memory, {**payload, "stop_hook_active": "yes"}))
            self.assertIsNotNone(guard.stop_feedback(memory, {**payload, "stop_hook_active": 1}))
            with patch.dict(os.environ, {"ARET_MMU_BARRIER_OFF": "1"}, clear=False):
                self.assertIsNone(guard.stop_feedback(memory, payload))

        with TemporaryDirectory() as directory:
            with self.vera_store(Path(directory)) as store:
                service = ResumeGuardService(store)
                dossier = self.vera_dossier(store)
                service.arm("sess-stop", "c15-adapter", "SESSION_OPEN", dossier, mode="HARD")
                self.assertEqual(
                    service.session_ending("sess-stop", "c15-adapter", already_nudged=False).decision, GuardDecision.NUDGE
                )
                self.assertEqual(
                    service.session_ending("sess-stop", "c15-adapter", already_nudged=True).decision, GuardDecision.ALLOW
                )
                with patch.dict(os.environ, {"VERA_MMU_BARRIER_OFF": "1"}, clear=False):
                    self.assertEqual(
                        service.session_ending("sess-stop", "c15-adapter", already_nudged=False).decision,
                        GuardDecision.NUDGE,
                    )
                service.acknowledge("sess-stop", "c15-adapter", dossier.resume_contract_hash, vera_sections())
                self.assertEqual(
                    service.session_ending("sess-stop", "c15-adapter", already_nudged=False).decision, GuardDecision.ALLOW
                )

    # ------------------------------ ce qui arrive quand la barrière est en défaut

    def test_i014_an_unreadable_guard_state_disarms_aret_and_denies_on_vera(self) -> None:
        """Le cœur de l'écart : une barrière en défaut doit refuser, pas disparaître.

        Trois altérations posées aux deux moteurs. ARET rend `None` à chaque fois — donc aucune
        décision, donc l'action passe. VERA lève à la lecture et `precheck` refuse.
        """
        guard = aret_resume_guard()
        with temporary_root() as root:
            memory = root / ".aret-memory"
            memory.mkdir()
            payload = {"session_id": "sess-corrupt"}
            guard.arm(memory, payload, reason="startup", resume_contract_hash=CONTRACT_A)
            path = guard.state_path(memory, payload)
            healthy = path.read_bytes()
            for label, content in (
                ("json illisible", "{ pas du json"),
                ("version périmée", json.dumps({"version": 2, "status": "awaiting_recap", "mode": "hard"})),
                ("objet remplacé par une liste", json.dumps(["awaiting_recap"])),
            ):
                with self.subTest(alteration=label):
                    path.write_text(content, encoding="utf-8")
                    self.assertIsNone(guard.load_state(memory, payload))
                    self.assertIsNone(guard.decision(memory, payload))
                    self.assertIsNone(guard.stop_feedback(memory, payload))
            path.write_bytes(healthy)
            self.assertIsNotNone(guard.decision(memory, payload))

        with TemporaryDirectory() as directory:
            with self.vera_store(Path(directory)) as store:
                service = ResumeGuardService(store)
                service.arm("sess-corrupt", "c15-adapter", "SESSION_OPEN", self.vera_dossier(store), mode="HARD")
                path = service.state_path("sess-corrupt", "c15-adapter")
                healthy_payload = json.loads(path.read_text(encoding="utf-8"))
                for label, content in (
                    ("json illisible", "{ pas du json"),
                    ("format étranger", json.dumps({**healthy_payload, "format": "vera-session-guard/v0"})),
                    ("statut inconnu", json.dumps({**healthy_payload, "status": "PRESQUE"})),
                    ("mode incohérent", json.dumps({**healthy_payload, "mode": "SOFT"})),
                    ("champ en trop", json.dumps({**healthy_payload, "surplus": 1})),
                ):
                    with self.subTest(alteration=label):
                        path.write_text(content, encoding="utf-8")
                        outcome = service.precheck("sess-corrupt", "c15-adapter")
                        self.assertEqual(outcome.decision, GuardDecision.DENY)
                        self.assertIn("state integrity", outcome.reason)
                        self.assertEqual(
                            service.session_ending("sess-corrupt", "c15-adapter", already_nudged=False).decision,
                            GuardDecision.NUDGE,
                        )

    def test_i011_an_acknowledged_state_transplants_between_aret_memories(self) -> None:
        """L'état d'ARET ne porte aucune identité de projet ; celui de VERA en porte quatre couches.

        La clef d'ARET est `sha256(identité de session)[:24]` : deux mémoires différentes, même
        session, même nom de fichier. L'acquittement obtenu dans l'une lève donc la barrière dans
        l'autre. Côté VERA, les quatre couches sont isolées une à une ci-dessous — réparer l'une
        laisse la suivante refuser — pour qu'aucune ne soit créditée du travail d'une autre.
        """
        guard = aret_resume_guard()
        with temporary_root() as root:
            first = root / "projet-un" / ".aret-memory"
            second = root / "projet-deux" / ".aret-memory"
            first.mkdir(parents=True)
            second.mkdir(parents=True)
            payload = {"session_id": "sess-transplant"}
            guard.arm(first, payload, reason="startup", resume_contract_hash=CONTRACT_A)
            guard.acknowledge(first, acknowledgement(payload, aret_recap()))
            guard.arm(second, payload, reason="startup", resume_contract_hash=CONTRACT_B)
            self.assertIsNotNone(guard.decision(second, payload))

            source = guard.state_path(first, payload)
            target = guard.state_path(second, payload)
            self.assertEqual(source.name, target.name)
            target.write_bytes(source.read_bytes())
            # L'état est **lu et accepté** par la seconde mémoire, pas seulement ignoré : le
            # distinguer compte, puisqu'un état rejeté y laisserait aussi passer l'action.
            transplanted = guard.load_state(second, payload)
            self.assertIsNotNone(transplanted)
            self.assertEqual(transplanted["status"], "acknowledged")
            self.assertEqual(transplanted["resume_contract_hash"], CONTRACT_A)
            self.assertIsNone(guard.decision(second, payload))

    def test_i011_vera_refuses_a_transplanted_state_at_four_independent_layers(self) -> None:
        from vera_mmu.session_lifecycle import _state_key

        with TemporaryDirectory() as directory:
            base = Path(directory)
            with self.vera_store(base / "un", "c15-un") as one:
                service_one = ResumeGuardService(one)
                dossier_one = self.vera_dossier(one)
                service_one.arm("sess-transplant", "c15-adapter", "SESSION_OPEN", dossier_one, mode="HARD")
                service_one.acknowledge("sess-transplant", "c15-adapter", dossier_one.resume_contract_hash, vera_sections())
                source_path = service_one.state_path("sess-transplant", "c15-adapter")
                stolen = json.loads(source_path.read_text(encoding="utf-8"))
                source_name = source_path.name

            with self.vera_store(base / "deux", "c15-deux") as two:
                service_two = ResumeGuardService(two)
                service_two.arm("sess-transplant", "c15-adapter", "SESSION_OPEN", self.vera_dossier(two), mode="HARD")
                target = service_two.state_path("sess-transplant", "c15-adapter")
                # Première couche : le nom de fichier lui-même diffère, la clef portant le projet.
                self.assertNotEqual(source_name, target.name)

                # Chaque couche est isolée en réparant **toutes les autres** : ce qui reste étranger
                # est alors seul en cause. Réparer en cascade aurait laissé la couche suivante
                # faire le travail de la précédente, et n'aurait prouvé ni l'une ni l'autre.
                adopted = {
                    "sessionStateKey": _state_key(two, "sess-transplant", "c15-adapter"),
                    "projectId": two.identity.project_id,
                    "projectHash": two.identity.project_hash,
                    "profileHash": two.identity.profile_hash,
                }
                for label, foreign_fields in (
                    ("clef de session étrangère", ("sessionStateKey",)),
                    ("projet étranger", ("projectId", "projectHash")),
                    ("profil étranger", ("profileHash",)),
                ):
                    with self.subTest(couche=label):
                        state = {**stolen, **adopted}
                        for field in foreign_fields:
                            state[field] = stolen[field]
                        target.write_text(json.dumps(state), encoding="utf-8")
                        self.assertEqual(service_two.precheck("sess-transplant", "c15-adapter").decision, GuardDecision.DENY)

                target.write_text(json.dumps({**stolen, **adopted}), encoding="utf-8")
                # Les quatre couches réparées, l'état n'est plus transplanté : c'est le sien.
                self.assertEqual(service_two.precheck("sess-transplant", "c15-adapter").decision, GuardDecision.ALLOW)

    def test_i008_the_guard_state_location_follows_the_payload_on_aret_and_the_store_on_vera(self) -> None:
        """Où la barrière va chercher son état, et qui décide de cet endroit.

        Les wrappers d'ARET lisent `payload["memory_dir"]` avant `ARET_MEMORY_DIR` et avant le
        défaut : un payload qui nomme un autre répertoire ne trouve pas d'état, et la barrière ne
        rend aucune décision. Sur VERA, l'emplacement se dérive du store déjà lié au projet, et
        aucun paramètre d'entrée ne le déplace.

        Le payload d'un hook est fourni par le hôte, pas par le client : ceci mesure un chemin
        d'entrée, pas un exploit constaté.
        """
        guard = aret_resume_guard()
        with temporary_root() as root:
            memory = root / ".aret-memory"
            elsewhere = root / "ailleurs"
            memory.mkdir()
            elsewhere.mkdir()
            payload = {"session_id": "sess-redirect"}
            guard.arm(memory, payload, reason="startup", resume_contract_hash=CONTRACT_A)
            self.assertIsNotNone(guard.decision(memory, payload))
            self.assertIsNone(guard.decision(elsewhere, payload))

        with TemporaryDirectory() as directory:
            with self.vera_store(Path(directory)) as store:
                service = ResumeGuardService(store)
                service.arm("sess-redirect", "c15-adapter", "SESSION_OPEN", self.vera_dossier(store), mode="HARD")
                located = service.state_path("sess-redirect", "c15-adapter")
                self.assertEqual(located.parent, store.locator.runtime_dir / "lifecycle")
                self.assertEqual(
                    [parameter for parameter in ("memory_dir", "runtime_dir", "state_path") if parameter in
                     ResumeGuardService.precheck.__code__.co_varnames],
                    [],
                )

    def test_i009_the_ritual_never_touches_canonical_memory_and_only_vera_records_it(self) -> None:
        """Accord sur l'essentiel, écart sur la trace.

        Des deux côtés, l'état de la barrière vit sous `runtime/` et la base canonique ne bouge
        pas d'un octet quand on arme puis acquitte. Mais ARET ne laisse **aucune** trace durable
        de son rituel ; VERA écrit deux lignes d'audit. Une reprise que personne ne peut relire
        après coup n'est pas auditable.
        """
        guard = aret_resume_guard()
        with temporary_root() as root:
            store = memory_store(root / ".aret-memory")
            try:
                memory = Path(store.memory_dir)
                database = memory / "aret_memory.sqlite"
                before = sha256(database.read_bytes()).hexdigest()
                payload = {"session_id": "sess-trace"}
                guard.arm(memory, payload, reason="startup", resume_contract_hash=CONTRACT_A)
                guard.acknowledge(memory, acknowledgement(payload, aret_recap()))
                self.assertEqual(sha256(database.read_bytes()).hexdigest(), before)
                self.assertEqual(
                    guard.state_path(memory, payload).relative_to(memory).parts[:2], ("runtime", "resume_guard")
                )
            finally:
                del store

        with TemporaryDirectory() as directory:
            with self.vera_store(Path(directory)) as store:
                service = ResumeGuardService(store)
                dossier = self.vera_dossier(store)
                service.arm("sess-trace", "c15-adapter", "SESSION_OPEN", dossier, mode="HARD")
                service.acknowledge("sess-trace", "c15-adapter", dossier.resume_contract_hash, vera_sections())
                state_path = service.state_path("sess-trace", "c15-adapter")
                self.assertEqual(state_path.parent.name, "lifecycle")
                self.assertEqual(state_path.parent.parent, store.locator.runtime_dir)
                with store.transaction() as connection:
                    actions = [
                        row[0]
                        for row in connection.execute(
                            "SELECT action FROM store_audit WHERE action LIKE 'RESUME_GUARD%' ORDER BY id"
                        ).fetchall()
                    ]
                self.assertEqual(actions, ["RESUME_GUARD_ARMED", "RESUME_GUARD_ACKNOWLEDGED"])

    def test_i001_the_core_guard_knows_nothing_about_aret(self) -> None:
        """Le Core doit rester indépendant de ce contre quoi on le compare."""
        source = (Path(__file__).resolve().parents[1] / "src" / "vera_mmu" / "session_lifecycle.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("aret-memory", source)
        self.assertNotIn("resume_guard.py", source)
        self.assertNotIn("hookSpecificOutput", source)
        # Une seule mention d'ARET est admise, et elle est nommée : la compatibilité du kill-switch.
        self.assertEqual(source.count("ARET"), 1)
        self.assertIn("ARET_MMU_BARRIER_OFF", source)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

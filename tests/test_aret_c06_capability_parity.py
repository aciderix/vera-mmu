"""Test de parité du couplage `C06` — catalogue `PIPELINES` d'ARET contre celui de VERA.

Le registre exige, pour promouvoir `C06` : « Rejet capability inconnue, paramètres hors schéma,
timeout, policy, artifact hash, dry-run et snapshot de catalogue ».

**ARET est exécuté.** Son adaptateur de pipelines tourne contre son vrai `MemoryStore`, et les
plans sont construits pour de bon — `C06` porte sur ce qui se décide **avant** l'exécution, donc
un dry-run suffit et c'est le bon périmètre. L'exécution réelle est `C07`/`C08`, qui demandent
Wine et MinGW.

**Ce qu'ARET fait bien, dit en premier.** Son catalogue est une **liste fermée de 27 pipelines
nommés** : aucun client ne fournit de commande, et l'argv est construit par le moteur. Un nom
inconnu est refusé, un timeout hors borne est refusé, et les trois policies non triviales —
`GENERATE`, `NETWORK`, `SENSITIVE` — exigent chacune une confirmation nommée avant toute
exécution. C'est un dessin sérieux, et ce n'est pas un couplage où VERA serait simplement meilleur.

**La divergence porte sur les paramètres, et elle est structurelle.** Le catalogue d'ARET déclare
un nom, une policy, des dépendances, un timeout et un runner — **jamais un schéma de paramètres**.
Les paramètres sont un `dict` libre, validé au coup par coup à l'intérieur de chaque runner. Mesuré
en l'exécutant : `{"intrus": "valeur inventee", "rm": "-rf /"}` traverse sans un mot et se retrouve
tel quel dans le plan rendu.

Ce n'est **pas** une injection de commande — l'argv reste fermé, et ces valeurs ne sont lues par
personne. C'est autre chose, et de plus insidieux : rien ne dit quels paramètres un pipeline lit
réellement. Mesuré aussi — un `binary_pathh` mal orthographié et un `binary_path` absent rendent la
**même** erreur, « Asset introuvable :  », avec un chemin vide. L'appelant ne peut pas distinguer
« tu as mal tapé la clef » de « tu as oublié la clef ». C'est exactement ce qu'un schéma déclaré
empêche, et c'est ce que `C06` demande d'ajouter.

VERA déclare `parameter_schema` dans le contrat, le valide contre un sous-ensemble fermé de JSON
Schema, et refuse à l'exécution tout paramètre non déclaré quand `additionalProperties` est faux.
Et son catalogue dit une chose qu'ARET ne peut pas dire : `command` y est rendu
`NOT_APPLICABLE`, avec son motif.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import unittest

from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_builder import capability_contract_options
from vera_mmu.capability_contracts import (
    NETWORK_POLICIES,
    RUNNER_PROFILES,
    CapabilityContractError,
    CapabilityContractService,
)
from vera_mmu.capability_policies import POLICY_DECISIONS, CapabilityPolicyService
from vera_mmu.executions import ExecutionError, ExecutionService
from vera_mmu.identity import load_profile
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization
from vera_mmu.store import MemoryStore

from tests.aret_v1_baseline import temporary_root
from tests.aret_v1_pipelines_reference import (
    REFERENCE_SHA256,
    aret_pipelines,
    reference_digest,
    repository_stub,
)
from tests.aret_v1_repository_reference import aret_repository, memory_store


#: Relevé sur le catalogue **exécuté**, pas transcrit de la source.
ARET_POLICY_COUNTS = {"READ_ONLY": 15, "GENERATE": 9, "NETWORK": 2, "SENSITIVE": 1}
ARET_PIPELINE_TOTAL = 27
#: Les trois policies qu'ARET fait confirmer, et le nom du drapeau de chacune.
ARET_CONFIRMATIONS = {
    "generate_codepage_cp1252": ("GENERATE", "confirm_apply"),
    "fetch_wall_corpus": ("NETWORK", "confirm_network"),
    "capture_snapshot": ("SENSITIVE", "confirm_sensitive"),
}


def _vera_project(root, project_id: str):
    root.mkdir(parents=True, exist_ok=True)
    preview = preview_project_initialization(
        root, template="software", project_id=project_id, project_name=project_id
    )
    apply_project_initialization(root, preview, confirm=True)
    return root / ".vera-mmu" / "project.yaml"


def _capability(store: MemoryStore, identifier: str, schema: dict, *, decision: str = "ALLOW") -> None:
    """Déclarer une capability complète : contrat, schéma de paramètres et policy."""
    CapabilityService(store).create(identifier, identifier.upper(), "CHECK", "1.0.0")
    CapabilityContractService(store).declare(
        identifier, "NOOP", "DENY_NETWORK", 30, parameter_schema=schema
    )
    CapabilityPolicyService(store).declare(identifier, decision, "policy de parité C06")


class AretC06CapabilityParityTests(unittest.TestCase):
    def test_the_vendored_pipelines_source_is_the_pinned_aret_file(self) -> None:
        self.assertEqual(reference_digest(), REFERENCE_SHA256)

    # --- snapshot de catalogue ----------------------------------------------

    def test_arets_catalogue_is_a_closed_list_of_twenty_seven_named_pipelines(self) -> None:
        """Le catalogue est relevé sur un appel **exécuté**, et compté, pas décrit.

        Vingt-sept noms, quatre policies, des dépendances et un timeout par entrée. Le contrat que
        le catalogue s'écrit à lui-même annonce « liste fermée, argv contrôlés, aucun shell
        arbitraire », et le nombre confirme qu'il n'y a pas d'échappatoire par un vingt-huitième.
        """
        module = aret_pipelines()
        catalogue = module.pipeline_catalog()

        self.assertEqual(len(module.PIPELINES), ARET_PIPELINE_TOTAL)
        self.assertEqual(dict(Counter(spec.policy for spec in module.PIPELINES.values())), ARET_POLICY_COUNTS)
        self.assertEqual(sum(len(items) for items in catalogue["policies"].values()), ARET_PIPELINE_TOTAL)
        self.assertEqual(set(catalogue["policies"]), set(ARET_POLICY_COUNTS))
        for marker in ("liste fermée", "argv contrôlés", "aucun shell arbitraire"):
            self.assertIn(marker, catalogue["contract"], marker)
        for flag in ("network_confirmation_required", "sensitive_confirmation_required", "generate_apply_confirmation_required"):
            self.assertTrue(catalogue[flag], flag)

    def test_arets_catalogue_entries_declare_no_parameter_schema(self) -> None:
        """Ce que le catalogue **ne dit pas**, et c'est la divergence de `C06`.

        Chaque entrée porte un nom, un type, une description, ses dépendances et son timeout. Il
        n'y a nulle part de quoi savoir quels paramètres le pipeline lit. Le fait est relevé sur les
        vingt-sept entrées et sur le `PipelineSpec` lui-même, pour qu'un champ ajouté un jour fasse
        tomber ce test au lieu de passer inaperçu.
        """
        module = aret_pipelines()
        catalogue = module.pipeline_catalog()
        entries = [item for items in catalogue["policies"].values() for item in items]

        self.assertEqual(len(entries), ARET_PIPELINE_TOTAL)
        for entry in entries:
            with self.subTest(entry["name"]):
                self.assertEqual(
                    set(entry), {"name", "kind", "description", "dependencies", "timeout_seconds"}
                )
        declared = set(module.PipelineSpec.__dataclass_fields__)
        self.assertEqual(
            declared,
            {"name", "kind", "policy", "description", "dependencies", "timeout_seconds", "runner", "requires_aret_binary"},
        )
        self.assertFalse(
            [field for field in declared if "param" in field or "schema" in field],
            "`PipelineSpec` déclarerait désormais un schéma de paramètres",
        )

    def test_veras_catalogue_says_there_is_no_command_field_at_all(self) -> None:
        """Le pendant : un catalogue qui déclare l'absence plutôt que de la laisser deviner.

        Une case vide dans un formulaire se lit « à remplir ». `NOT_APPLICABLE` accompagné de son
        motif se lit « il n'y en a pas, et voici pourquoi ». C'est la même règle qu'en `C11` : la
        borne la plus forte est celle qui ne laisse pas la valeur entrer.
        """
        with temporary_root() as root:
            profile_path = _vera_project(root / "projet", "c06-catalogue")
            options = capability_contract_options(profile_path)

        self.assertEqual(options["command"]["status"], "NOT_APPLICABLE")
        self.assertIn("aucun champ de commande", options["command"]["reason"])
        self.assertIn("I008", options["command"]["reason"])
        self.assertEqual(options["network_policy"]["editable"], False)
        self.assertEqual(sorted(options["network_policy"]["available"]), sorted(NETWORK_POLICIES))
        self.assertEqual({runner["id"] for runner in options["runners"]}, set(RUNNER_PROFILES))
        self.assertEqual(options["mutation"], "NONE")

    # --- rejet d'une capability inconnue -------------------------------------

    def test_both_refuse_a_name_that_is_not_in_their_catalogue(self) -> None:
        """Le point d'accord, mesuré des deux côtés plutôt que supposé."""
        repository = aret_repository()
        module = aret_pipelines()
        with temporary_root() as root:
            store = memory_store(root / "memoire")
            depot = repository_stub(root / "depot")
            with self.assertRaises(repository.AretError) as aret_refused:
                module.run_pipeline(store, depot, "pipeline_qui_nexiste_pas")

            profile_path = _vera_project(root / "projet", "c06-inconnue")
            with MemoryStore.open(load_profile(profile_path), profile_path) as vera:
                with self.assertRaises(CapabilityContractError) as vera_refused:
                    CapabilityContractService(vera).declare(
                        "capability-absente", "NOOP", "DENY_NETWORK", 30
                    )

        self.assertIn("Pipeline inconnu", str(aret_refused.exception))
        self.assertIn("Capability inconnue", str(vera_refused.exception))

    # --- paramètres hors schéma ---------------------------------------------

    def test_aret_carries_an_invented_parameter_all_the_way_into_its_plan(self) -> None:
        """Le cœur de `C06`, mesuré en l'exécutant.

        Deux clefs inventées traversent la validation, arrivent dans le plan et y sont rendues à
        l'appelant. Ce n'est pas une injection : l'argv est fermé et ces valeurs ne sont lues par
        personne — le test l'épingle aussi, pour ne pas laisser croire à une faille qui n'existe
        pas. Ce qu'il montre est qu'aucun contrat ne dit quels paramètres comptent.
        """
        module = aret_pipelines()
        intruders = {"intrus": "valeur inventee", "rm": "-rf /"}
        with temporary_root() as root:
            store = memory_store(root / "memoire")
            depot = repository_stub(root / "depot")
            plan = module.run_pipeline(store, depot, "run_regression_gate", parameters=dict(intruders))

        self.assertTrue(plan["dry_run"])
        self.assertEqual(plan["parameters"], intruders, "les clefs inventées ont été filtrées")
        self.assertEqual(plan["command"][0], "bash")
        self.assertEqual(len(plan["command"]), 2, "l’argv a changé de forme")
        for value in intruders.values():
            self.assertNotIn(value, plan["command"], "une valeur cliente est entrée dans l’argv")

    def test_a_misspelled_parameter_is_indistinguishable_from_a_missing_one(self) -> None:
        """La conséquence pratique, et c'est elle qui coûte cher à l'usage.

        Sans schéma, une clef mal tapée n'est pas une clef inconnue : c'est une clef requise
        absente. Les deux situations rendent le même message, avec un chemin vide. Personne ne peut
        savoir laquelle des deux s'est produite.
        """
        repository = aret_repository()
        module = aret_pipelines()
        with temporary_root() as root:
            store = memory_store(root / "memoire")
            depot = repository_stub(root / "depot")
            messages = []
            for parameters in ({"binary_pathh": "target/release/aret"}, {}):
                with self.assertRaises(repository.AretError) as refused:
                    module.run_pipeline(store, depot, "inspect_binary", parameters=parameters)
                messages.append(str(refused.exception))

        self.assertEqual(messages[0], messages[1], "les deux cas se distinguent désormais")
        self.assertIn("Asset introuvable", messages[0])

    def test_vera_refuses_an_undeclared_parameter_and_a_wrongly_typed_one(self) -> None:
        """Le pendant : le schéma est déclaré dans le contrat, et il mord à l'exécution."""
        schema = {
            "type": "object",
            "properties": {"seuil": {"type": "integer"}},
            "required": ["seuil"],
            "additionalProperties": False,
        }
        with temporary_root() as root:
            profile_path = _vera_project(root / "projet", "c06-schema")
            with MemoryStore.open(load_profile(profile_path), profile_path) as store:
                _capability(store, "bornee", schema)
                executions = ExecutionService(store)
                accepted = executions.run_noop("exec-ok", "bornee", {"seuil": 3})
                with self.assertRaises(ExecutionError) as undeclared:
                    executions.run_noop("exec-intrus", "bornee", {"seuil": 3, "intrus": "x"})
                with self.assertRaises(ExecutionError) as mistyped:
                    executions.run_noop("exec-type", "bornee", {"seuil": "trois"})
                with self.assertRaises(ExecutionError) as missing:
                    executions.run_noop("exec-absent", "bornee", {})

        self.assertEqual(accepted.parameters, {"seuil": 3})
        for refusal in (undeclared, mistyped, missing):
            self.assertIn("hors contrat fermé", str(refusal.exception))

    def test_veras_schema_subset_is_itself_closed(self) -> None:
        """Un schéma de paramètres qui accepterait n'importe quel JSON Schema ne bornerait rien."""
        with temporary_root() as root:
            profile_path = _vera_project(root / "projet", "c06-sous-ensemble")
            with MemoryStore.open(load_profile(profile_path), profile_path) as store:
                CapabilityService(store).create("libre", "LIBRE", "CHECK", "1.0.0")
                contracts = CapabilityContractService(store)
                for label, schema in {
                    "clef racine inconnue": {"type": "object", "patternProperties": {}},
                    "racine non object": {"type": "array"},
                    "required non déclaré": {"type": "object", "properties": {}, "required": ["absent"]},
                }.items():
                    with self.subTest(label):
                        with self.assertRaises(CapabilityContractError):
                            contracts.declare("libre", "NOOP", "DENY_NETWORK", 30, parameter_schema=schema)

    # --- timeout --------------------------------------------------------------

    def test_both_bound_the_timeout_and_neither_lets_the_caller_widen_it(self) -> None:
        """Deux bornes, et la nuance qui les sépare : la sienne, ou la même pour tous.

        ARET borne au timeout **du pipeline** — jusqu'à 14400 s pour le plus long. VERA borne à
        3600 s pour toute capability. La seconde est plus stricte ; la première est plus fine. Ce
        qui compte pour `C06` est qu'aucune des deux n'accepte qu'un appelant l'élargisse, et c'est
        cela qui est mesuré.

        **Côté VERA la borne est tenue deux fois**, et le test nomme les deux couches plutôt que
        d'en laisser une invisible. Mesuré : relâcher la garde Python laissait ce test vert, parce
        que le `CHECK` du schéma refuse la ligne de toute façon. Le motif exigé ici est donc celui
        de la garde Python, et le `CHECK` est épinglé séparément dans le DDL — neutraliser l'une ou
        l'autre se voit.
        """
        repository = aret_repository()
        module = aret_pipelines()
        with temporary_root() as root:
            store = memory_store(root / "memoire")
            depot = repository_stub(root / "depot")
            spec = module.PIPELINES["run_regression_gate"]
            with self.assertRaises(repository.AretError) as too_long:
                module.run_pipeline(store, depot, "run_regression_gate", timeout_seconds=spec.timeout_seconds + 1)
            with self.assertRaises(repository.AretError):
                module.run_pipeline(store, depot, "run_regression_gate", timeout_seconds=0)
            within = module.run_pipeline(store, depot, "run_regression_gate", timeout_seconds=spec.timeout_seconds)

            profile_path = _vera_project(root / "projet", "c06-timeout")
            with MemoryStore.open(load_profile(profile_path), profile_path) as store:
                CapabilityService(store).create("bornee", "BORNEE", "CHECK", "1.0.0")
                contracts = CapabilityContractService(store)
                options = capability_contract_options(profile_path)
                maximum = int(options["timeout_seconds"]["maximum"])
                for value in (maximum + 1, 0, -1, True):
                    with self.subTest(value):
                        with self.assertRaises(CapabilityContractError) as refused:
                            contracts.declare("bornee", "NOOP", "DENY_NETWORK", value)
                        self.assertIn("Timeout hors borne", str(refused.exception))

            # La seconde ceinture, nommée : le schéma refuse la ligne même si la garde cédait.
            ddl = (Path(__file__).resolve().parents[1] / "src" / "vera_mmu" / "schema" / "015_capability_contracts.sql").read_text(encoding="utf-8")
            self.assertIn("CHECK (timeout_seconds BETWEEN 1 AND 3600)", ddl)

        self.assertIn(str(spec.timeout_seconds), str(too_long.exception))
        self.assertTrue(within["dry_run"])
        self.assertEqual(maximum, 3600)
        self.assertGreater(spec.timeout_seconds, maximum, "les bornes ne se comparent plus comme décrit")

    # --- policy ---------------------------------------------------------------

    def test_arets_three_confirmations_are_each_demanded_by_name(self) -> None:
        """Trois policies, trois drapeaux distincts : refuser en bloc serait moins informatif."""
        repository = aret_repository()
        module = aret_pipelines()
        with temporary_root() as root:
            store = memory_store(root / "memoire")
            depot = repository_stub(root / "depot")
            for name, (policy, flag) in ARET_CONFIRMATIONS.items():
                with self.subTest(name):
                    self.assertEqual(module.PIPELINES[name].policy, policy)
                    with self.assertRaises(repository.AretError) as refused:
                        module.run_pipeline(store, depot, name, dry_run=False)
                    self.assertIn(flag, str(refused.exception), flag)

    def test_arets_confirmations_guard_the_execution_and_not_the_plan(self) -> None:
        """Une nuance qu'il faut dire, parce qu'elle est défendable et qu'elle surprend.

        Le plan d'un pipeline sensible se rend **sans** confirmation : `dry_run` est la valeur par
        défaut, et il annonce lui-même quelles confirmations seraient exigées. La garde porte sur
        l'exécution, pas sur la consultation — ce qui est cohérent, mais signifie qu'un argv
        sensible est lisible avant toute autorisation.
        """
        module = aret_pipelines()
        with temporary_root() as root:
            store = memory_store(root / "memoire")
            depot = repository_stub(root / "depot")
            plan = module.run_pipeline(store, depot, "capture_snapshot", parameters={"pid": 4321})

        self.assertTrue(plan["dry_run"])
        self.assertEqual(plan["policy"], "SENSITIVE")
        self.assertTrue(plan["confirmation_required"]["confirm_sensitive"])
        self.assertFalse(plan["confirmation_required"]["confirm_apply"])
        self.assertIn("4321", " ".join(plan["command"]))

    def test_vera_requires_an_explicit_allow_and_refuses_deny_and_confirm(self) -> None:
        """Trois décisions déclarées, et seule `ALLOW` laisse passer une exécution."""
        self.assertEqual(POLICY_DECISIONS, frozenset({"ALLOW", "DENY", "CONFIRM"}))
        schema = {"type": "object", "properties": {}, "additionalProperties": False}
        with temporary_root() as root:
            profile_path = _vera_project(root / "projet", "c06-policy")
            with MemoryStore.open(load_profile(profile_path), profile_path) as store:
                for index, decision in enumerate(("DENY", "CONFIRM")):
                    identifier = f"policy-{decision.lower()}"
                    _capability(store, identifier, schema, decision=decision)
                    with self.subTest(decision):
                        with self.assertRaises(ExecutionError) as refused:
                            ExecutionService(store).run_noop(f"exec-{index}", identifier, {})
                        self.assertIn("ALLOW", str(refused.exception))
                _capability(store, "policy-allow", schema)
                allowed = ExecutionService(store).run_noop("exec-allow", "policy-allow", {})

        self.assertEqual(allowed.status, "COMPLETED")

    # --- artifact hash et dry-run --------------------------------------------

    def test_aret_hashes_its_artifact_and_vera_refuses_one_that_is_not_a_digest(self) -> None:
        """Les deux attachent une empreinte à une exécution ; une seule en vérifie la forme.

        Le fait ARET est lu dans sa source plutôt qu'exécuté : produire un artefact demanderait de
        lancer un processus, ce qui est le périmètre de `C07`. Ce qui est vérifiable ici est que
        l'artefact est bien haché et que le hash est consigné avec la ligne d'exécution.
        """
        source = aret_pipelines().__file__
        text = __import__("pathlib").Path(source).read_text(encoding="utf-8")
        self.assertIn("artifact_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest()", text)
        self.assertIn("artifact_hash=artifact_hash", text)

        schema = {"type": "object", "properties": {}, "additionalProperties": False}
        with temporary_root() as root:
            profile_path = _vera_project(root / "projet", "c06-artefact")
            with MemoryStore.open(load_profile(profile_path), profile_path) as store:
                CapabilityService(store).create("observee", "OBSERVEE", "CHECK", "1.0.0")
                CapabilityContractService(store).declare(
                    "observee", "OBSERVED_PROCESS", "DENY_NETWORK", 30, parameter_schema=schema
                )
                CapabilityPolicyService(store).declare("observee", "ALLOW", "policy de parité C06")
                executions = ExecutionService(store)
                for label, digest in {"trop court": "abc", "hors hexadécimal": "z" * 64, "vide": ""}.items():
                    with self.subTest(label):
                        with self.assertRaises(ExecutionError):
                            executions.record_observed_process(
                                f"exec-{label.replace(' ', '-')}", "observee", {},
                                environment={}, exit_code=0, artifact_hash=digest, result={},
                            )

    def test_arets_dry_run_is_the_default_and_renders_the_argv_it_would_launch(self) -> None:
        """Dernière dimension : ce qu'un dry-run rend, et ce que VERA n'a pas à rendre.

        ARET rend l'argv complet, chemins résolus. C'est utile et c'est honnête. VERA n'a pas
        d'argv : ses quatre profils de runner n'exécutent aucun processus, et sa source
        d'exécution ne contient pas un `subprocess` — mesuré ici, parce qu'une affirmation de ce
        genre doit être vérifiable.
        """
        module = aret_pipelines()
        signature = __import__("inspect").signature(module.run_pipeline)
        self.assertIs(signature.parameters["dry_run"].default, True)

        with temporary_root() as root:
            store = memory_store(root / "memoire")
            depot = repository_stub(root / "depot")
            plan = module.run_pipeline(store, depot, "run_gauntlet")

        self.assertTrue(plan["dry_run"])
        self.assertEqual(plan["command"][0], "bash")
        # Le chemin est comparé par ses **composants**, pas par une chaîne. ARET résout un `Path`
        # et `str()` en rend la forme native : sur Windows, `…\bench\gauntlet\score.sh`, et un
        # `endswith("bench/gauntlet/score.sh")` y est faux. Mesuré au run #54 — c'était le
        # séparateur codé en dur dans ce test, pas un comportement d'ARET.
        self.assertEqual(Path(plan["command"][1]).parts[-3:], ("bench", "gauntlet", "score.sh"))

        from pathlib import Path as _Path

        for name in ("executions.py", "capabilities.py", "capability_contracts.py"):
            with self.subTest(name):
                text = (_Path(__file__).resolve().parents[1] / "src" / "vera_mmu" / name).read_text(encoding="utf-8")
                for forbidden in ("subprocess", "os.system", "Popen", "shell=True"):
                    self.assertNotIn(forbidden, text, f"{name} exécuterait un processus ({forbidden})")


if __name__ == "__main__":
    unittest.main()

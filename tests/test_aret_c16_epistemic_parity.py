"""Test de parité du couplage `C16` — noyau épistémique ARET V1 contre celui de VERA.

Le registre exige, pour promouvoir `C16` : « promotion sans preuve, HMAC, hash d'artefact, rewrite
append-only, relation lifecycle/supersession, audit et import croisé refusé ».

**La baseline montre la règle en train de tenir, et c'est le fait le plus intéressant du lot.** Elle
porte quatre preuves, toutes `PASS` et toutes `exit_code=0`. Aucune n'est admissible, aucune ne porte
de reçu HMAC. `KN-0011` est liée à trois d'entre elles — et n'est **pas** `PROVEN`. Cinq cent
trente-deux connaissances, zéro promotion. I004 n'est donc pas une intention de conception : c'est un
comportement observable dans des données de production, et VERA doit refuser la même situation.

**Les deux moteurs ne placent pas la règle au même endroit, et il faut le dire.** ARET garde une
colonne `status` sur `knowledge` et la protège par deux triggers. VERA n'a pas de statut à faire
basculer : une promotion **est** une ligne de `knowledge_proof`, table dont le `CHECK` n'admet que
`PROVEN` et que deux triggers rendent append-only. Exiger que VERA promeuve une colonne serait
inventer un défaut ; exiger qu'il refuse sans preuve admissible est la vraie parité.

**L'append-only d'ARET est plus étroit qu'il n'en a l'air, et c'est mesuré, pas lu.** Exécuté sur son
propre DDL : l'insertion directe en `PROVEN`, la promotion sans preuve admissible et la réécriture du
contenu sont refusées — mais la mise à jour du seul statut **et la suppression d'une connaissance**
passent. ARET protège le contenu, pas l'existence. VERA refuse toute mise à jour et toute
suppression.
"""
from __future__ import annotations

from pathlib import Path
import sqlite3
import unittest

from vera_mmu.admission import AdmissionError, AdmissionService
from vera_mmu.admission_policies import AdmissionPolicyService
from vera_mmu.capabilities import CapabilityService
from vera_mmu.capability_contracts import CapabilityContractService
from vera_mmu.capability_policies import CapabilityPolicyService
from vera_mmu.evidence import EvidenceService
from vera_mmu.executions import ExecutionService
from vera_mmu.identity import load_profile
from vera_mmu.knowledge import KnowledgeService
from vera_mmu.proof_policies import ProofPolicyService
from vera_mmu.proofs import ProofError, ProofService
from vera_mmu.store import MemoryStore, StoreIdentityError

from tests.aret_v1_baseline import BASELINE, SCHEMA_DIR, temporary_root


#: Les trois triggers par lesquels ARET tient ses règles épistémiques.
ARET_TRIGGERS = (
    "reject_unproven_insert",
    "reject_unproven_promotion",
    "reject_knowledge_content_rewrite",
)


def _aret_database(path: Path) -> sqlite3.Connection:
    """Une base au schéma réel d'ARET, avec une connaissance ordinaire à éprouver."""
    connection = sqlite3.connect(path)
    for migration in sorted(SCHEMA_DIR.glob("*.sql")):
        connection.executescript(migration.read_text(encoding="utf-8"))
    connection.execute(
        "INSERT INTO knowledge(id, type, status, title, content, version, content_hash, "
        "created_at, updated_at, created_by) VALUES "
        "('K1','RULE','OBSERVED','titre','contenu',1,'h','2026-01-01T00:00:00Z','2026-01-01T00:00:00Z','parity')"
    )
    connection.commit()
    return connection


def _accepts(connection: sqlite3.Connection, statement: str) -> bool:
    """Exécuter puis annuler : ce qui compte est l'acceptation, pas l'effet."""
    try:
        connection.execute(statement)
    except sqlite3.Error:
        connection.rollback()
        return False
    connection.rollback()
    return True


class AretC16EpistemicParityTests(unittest.TestCase):
    def setUp(self) -> None:
        # `temporary_root` est un gestionnaire de contexte, pas l'objet `TemporaryDirectory` :
        # `enter_context` le tient ouvert pour la durée du test et le referme au démontage.
        self.root = self.enterContext(temporary_root())
        runtime = self.root / ".vera-mmu"
        runtime.mkdir()
        self.profile_path = runtime / "project.yaml"
        self.profile_path.write_text(
            'mmu:\n  version: "2.0"\n'
            'project:\n  id: "c16-parity"\n  name: "C16 parity"\n  domain: "generic"\n'
            'workspace:\n  root: "."\n'
            'storage:\n  memory_dir: ".vera-mmu"\n  sqlite_file: "memory.sqlite"\n  artifacts_dir: "artifacts"\n'
            'identity:\n  include_vcs_revision: false\n  include_profile_hash: true\n',
            encoding="utf-8",
        )

    def _store(self) -> MemoryStore:
        return MemoryStore.open(load_profile(self.profile_path), self.profile_path)

    @staticmethod
    def _ready(store: MemoryStore, *, verdict: str = "PASS", admitted: bool = True, hmac_required: bool = False) -> None:
        """Monter la chaîne complète jusqu'au seuil de promotion, sans la franchir."""
        knowledge = KnowledgeService(store)
        knowledge.register_type("fact", "Fact")
        knowledge.append("k", "fact", "OBSERVED", "Titre", "contenu")
        CapabilityService(store).create("c", "C", "CHECK", "1.0.0")
        CapabilityContractService(store).declare("c", "NOOP", "DENY_NETWORK", 30)
        CapabilityPolicyService(store).declare("c", "ALLOW", "policy de parité")
        ExecutionService(store).run_noop("x", "c", {})
        EvidenceService(store).record("e", "x", "TEST_PROOF", verdict, {})
        AdmissionPolicyService(store).declare("PASS_EVIDENCE")
        AdmissionService(store).decide("a", "e", "ADMITTED" if admitted else "REJECTED", "parité")
        ProofPolicyService(store).declare("HMAC_SHA256", hmac_required=hmac_required)

    # --- ce que la baseline montre déjà ------------------------------------

    def test_the_real_memory_holds_passing_proofs_and_no_promotion(self) -> None:
        """I004 observé en production, pas seulement voulu en conception."""
        proofs = BASELINE["proofs"]
        self.assertEqual(len(proofs), 4)
        self.assertTrue(all(item["result"] == "PASS" for item in proofs))
        self.assertTrue(all(item["exit_code"] == 0 for item in proofs))
        self.assertTrue(all(item["admissible"] == 0 for item in proofs), "une preuve admissible changerait la démonstration")
        self.assertTrue(all(item["receipt_hmac"] == "" for item in proofs))

        linked = {item["knowledge_id"] for item in BASELINE["proof_links"]}
        self.assertEqual(linked, {"KN-0011"})
        self.assertEqual(len(BASELINE["proof_links"]), 3)
        self.assertNotIn("PROVEN", BASELINE["knowledge_statuses"])
        self.assertEqual(sum(BASELINE["knowledge_statuses"].values()), BASELINE["knowledge_total"])
        self.assertEqual(BASELINE["knowledge_total"], 532)

    def test_every_real_proof_carries_an_artifact_and_a_payload_hash(self) -> None:
        """« Hash d'artefact » : une preuve sans empreinte ne se rejoue pas."""
        for item in BASELINE["proofs"]:
            with self.subTest(item["id"]):
                self.assertEqual(len(item["artifact_hash"]), 64, item["id"])
                self.assertEqual(len(item["payload_hash"]), 64, item["id"])

    # --- où chaque moteur place la règle ------------------------------------

    def test_aret_guards_a_mutable_status_and_vera_has_none_to_guard(self) -> None:
        """Exiger de VERA qu'il promeuve une colonne serait inventer un défaut.

        ARET porte `knowledge.status` et le protège par deux triggers. VERA fait de la promotion une
        ligne de `knowledge_proof`, dont le `CHECK` n'admet que `PROVEN` : il n'y a pas d'état à
        faire basculer, donc rien à garder de ce côté-là.
        """
        aret_schema = (SCHEMA_DIR / "001_initial.sql").read_text(encoding="utf-8")
        for trigger in ARET_TRIGGERS:
            self.assertIn(trigger, aret_schema, trigger)

        vera_schema = (
            Path(__file__).resolve().parents[1] / "src" / "vera_mmu" / "schema" / "018_knowledge_proofs.sql"
        ).read_text(encoding="utf-8")
        self.assertIn("CHECK(status='PROVEN')", vera_schema)
        self.assertIn("knowledge_proof_no_update", vera_schema)
        self.assertIn("knowledge_proof_no_delete", vera_schema)

    # --- append-only : la frontière, mesurée des deux côtés -----------------

    def test_arets_append_only_protects_content_but_not_existence(self) -> None:
        """Mesuré en exécutant sur son propre DDL, pas déduit de la lecture des triggers."""
        with temporary_root() as directory:
            connection = _aret_database(Path(directory) / "aret.sqlite")
            try:
                refused = {
                    "insertion directe en PROVEN": _accepts(
                        connection,
                        "INSERT INTO knowledge(id,type,status,title,content,version,content_hash,"
                        "created_at,updated_at,created_by) VALUES "
                        "('K2','RULE','PROVEN','t','c',1,'h','2026-01-01T00:00:00Z','2026-01-01T00:00:00Z','x')",
                    ),
                    "promotion sans preuve admissible": _accepts(
                        connection, "UPDATE knowledge SET status='PROVEN' WHERE id='K1'"
                    ),
                    "réécriture du contenu": _accepts(
                        connection, "UPDATE knowledge SET content='autre' WHERE id='K1'"
                    ),
                }
                accepted = {
                    "mise à jour du seul statut": _accepts(
                        connection, "UPDATE knowledge SET status='ACTIVE' WHERE id='K1'"
                    ),
                    "suppression de la connaissance": _accepts(
                        connection, "DELETE FROM knowledge WHERE id='K1'"
                    ),
                }
            finally:
                connection.close()

        self.assertEqual(refused, {key: False for key in refused})
        self.assertEqual(accepted, {key: True for key in accepted}, "la frontière ARET a bougé")

    def test_vera_refuses_both_the_rewrite_and_the_deletion(self) -> None:
        """Le resserrement : VERA protège l'existence, pas seulement le contenu."""
        with self._store() as store:
            knowledge = KnowledgeService(store)
            knowledge.register_type("fact", "Fact")
            knowledge.append("k", "fact", "OBSERVED", "Titre", "contenu")
            for statement in (
                "UPDATE knowledge SET title='autre' WHERE id='k'",
                "UPDATE knowledge SET status='ACTIVE' WHERE id='k'",
                "DELETE FROM knowledge WHERE id='k'",
            ):
                with self.subTest(statement):
                    with self.assertRaises(sqlite3.Error):
                        store.connection.execute(statement)

    # --- promotion : refus et acceptation -----------------------------------

    def test_promotion_is_refused_without_an_admitted_evidence(self) -> None:
        """La situation exacte de la baseline : une evidence `PASS` que rien n'admet."""
        with self._store() as store:
            self._ready(store, admitted=False)
            with self.assertRaises(ProofError):
                ProofService(store).promote("p", "k", "e", "a", actor="parity")
            self.assertEqual(
                store.connection.execute("SELECT COUNT(*) FROM knowledge_proof").fetchone()[0], 0
            )

    def test_a_failing_evidence_is_refused_one_layer_earlier_than_in_aret(self) -> None:
        """Le refus n'est pas au même étage, et le dire vaut mieux que de le contourner.

        ARET laisse entrer une preuve `FAIL` dans sa table et la barre au moment de la promotion,
        par le trigger `reject_unproven_promotion` qui exige `result='PASS' AND admissible=1`. VERA
        refuse dès l'admission : `AdmissionService` n'admet qu'une evidence `PASS`, donc une
        evidence `FAIL` n'atteint jamais le seuil de promotion. Les deux refusent ; VERA refuse plus
        tôt, ce qui laisse moins d'états intermédiaires à raisonner.
        """
        aret_schema = (SCHEMA_DIR / "001_initial.sql").read_text(encoding="utf-8")
        promotion = aret_schema[aret_schema.index("CREATE TRIGGER IF NOT EXISTS reject_unproven_promotion") :]
        promotion = promotion[: promotion.index("END;")]
        self.assertIn("p.result = 'PASS'", promotion)
        self.assertIn("p.admissible = 1", promotion)

        with self._store() as store:
            with self.assertRaises(AdmissionError):
                self._ready(store, verdict="FAIL")
            self.assertEqual(
                store.connection.execute("SELECT COUNT(*) FROM evidence_admission").fetchone()[0], 0
            )

    def test_promotion_succeeds_only_on_an_admitted_passing_evidence(self) -> None:
        """Et la connaissance elle-même ne change pas d'état : la preuve est une ligne à part."""
        with self._store() as store:
            self._ready(store)
            proof = ProofService(store).promote("p", "k", "e", "a", actor="parity")
            self.assertEqual(proof.status, "PROVEN")
            self.assertEqual(KnowledgeService(store).get("k").status, "OBSERVED")

    def test_a_required_hmac_without_a_secret_refuses_the_promotion(self) -> None:
        """« HMAC » : les quatre preuves réelles n'en portent aucun, et ne sont pas admissibles."""
        with self._store() as store:
            self._ready(store, hmac_required=True)
            with self.assertRaises(ProofError):
                ProofService(store).promote("p", "k", "e", "a", actor="parity")
            proof = ProofService(store, hmac_secret=b"secret-de-parite").promote(
                "p", "k", "e", "a", actor="parity"
            )
            self.assertEqual(len(proof.hmac_digest), 64)

    # --- relations, supersession et audit -----------------------------------

    def test_the_real_supersession_chain_is_coherent(self) -> None:
        """`KN-0010` v1 `SUPERSEDED` cède à `KN-0011` v2 `ACTIVE`, qui la désigne."""
        chain = {item["id"]: item for item in BASELINE["supersession_chain"]}
        self.assertEqual(chain["KN-0010"]["status"], "SUPERSEDED")
        self.assertEqual(chain["KN-0010"]["version"], 1)
        self.assertIsNone(chain["KN-0010"]["supersedes_id"])
        self.assertEqual(chain["KN-0011"]["status"], "ACTIVE")
        self.assertEqual(chain["KN-0011"]["version"], 2)
        self.assertEqual(chain["KN-0011"]["supersedes_id"], "KN-0010")
        self.assertEqual(BASELINE["knowledge_statuses"]["SUPERSEDED"], 1)
        self.assertEqual(BASELINE["relation_statuses"], {"ACTIVE": 47})
        self.assertEqual(BASELINE["relation_types"]["SUPERSEDES"], 4)

    def test_the_real_memory_carries_exactly_one_audit_event_per_knowledge(self) -> None:
        """« Audit » : 532 connaissances, 532 `APPEND_KNOWLEDGE`. Aucune écriture muette."""
        self.assertEqual(BASELINE["audit_operations"]["APPEND_KNOWLEDGE"], BASELINE["knowledge_total"])
        self.assertEqual(sum(BASELINE["audit_operations"].values()), BASELINE["audit_total"])
        self.assertEqual(BASELINE["audit_operations"]["ADD_RELATION"], sum(BASELINE["relation_types"].values()))

    def test_vera_records_an_audit_event_for_every_append(self) -> None:
        with self._store() as store:
            knowledge = KnowledgeService(store)
            knowledge.register_type("fact", "Fact")
            for index in range(3):
                knowledge.append(f"k{index}", "fact", "OBSERVED", f"T{index}", "contenu")
            appended = store.connection.execute(
                "SELECT COUNT(*) FROM store_audit WHERE action = 'KNOWLEDGE_APPENDED'"
            ).fetchone()[0]

        self.assertEqual(appended, 3)

    # --- import croisé -------------------------------------------------------

    def test_a_memory_bound_to_another_project_is_refused(self) -> None:
        """I011 : une mémoire reste liée à son projet, et le dire ne suffit pas."""
        with self._store() as store:
            KnowledgeService(store).register_type("fact", "Fact")
            database = store.workspace.runtime_dir / "memory.sqlite"

        other = self.root / "autre" / ".vera-mmu"
        other.mkdir(parents=True)
        other_profile = other / "project.yaml"
        other_profile.write_text(
            self.profile_path.read_text(encoding="utf-8").replace("c16-parity", "c16-autre"),
            encoding="utf-8",
        )
        (other / "memory.sqlite").write_bytes(database.read_bytes())

        with self.assertRaises(StoreIdentityError):
            with MemoryStore.open(load_profile(other_profile), other_profile):
                pass


if __name__ == "__main__":
    unittest.main()

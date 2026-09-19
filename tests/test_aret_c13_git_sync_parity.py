"""Test de parité du couplage `C13` — le Git borné d'ARET contre la synchronisation mémoire de VERA.

Le registre exige, pour promouvoir `C13` : « NoVCS, Git, changements hors scope, WAL occupé,
HEAD détachée, refus de push et policy invalide ».

**Ce fichier exécute ARET.** Les douze couplages précédents avaient extrait les faits ARET de
l'arbre syntaxique de sa source : c'était la bonne méthode pour une constante, une table ou une
signature. Ici la question porte sur un comportement — que fait ce code devant un dépôt réel —
et une lecture n'y répond pas. La référence versionnée est donc chargée comme module et ses
fonctions tournent sur de vrais dépôts Git montés pour l'occasion, à côté de celles de VERA.

**La mesure a trouvé un défaut dans ARET V1**, et il n'est pas mineur : `invoke()` applique
`.strip()` à la sortie entière de `git status --porcelain=v1`, ce qui mange l'espace de tête de la
première ligne quand celle-ci décrit une modification non indexée. `changes()` découpe ensuite à
une position fixe, et rend un chemin amputé de son premier caractère. `validate_scope` conclut
alors qu'un fichier **situé dans** le Memory Store est **hors** du Memory Store. Le cas où cela se
produit est précisément le cas ordinaire : la base mémoire modifiée en place et rien d'autre.
Conséquence mesurée ci-dessous : `automatic_sync` refuse de committer une mémoire parfaitement
propre, et `sync_memory_only` ne commite rien en annonçant « aucun changement ».

Ce défaut n'est **pas corrigé ici** : la référence est une copie octet pour octet dont le hash est
épinglé, et la réparer reviendrait à mesurer autre chose qu'ARET. Il est consigné.

**VERA n'a pas ce défaut, et pas par chance.** Elle ne réimplémente pas le format de sortie de
Git : elle passe le périmètre à Git sous forme de pathspec et ne lit de la réponse que son
caractère vide ou non. Il n'y a pas de chemin à découper, donc pas de découpe à rater. C'est la
même règle que partout ailleurs dans ce registre — ne pas reproduire un format qu'un autre
programme possède déjà.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
import sqlite3
import subprocess
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.identity import load_profile
from vera_mmu.memory_sync import automatic_memory_sync
from vera_mmu.store import MemoryStore
from vera_mmu.vcs import inspect_vcs

from tests.aret_v1_git_reference import (
    ARET_MEMORY_DIR,
    REFERENCE,
    REFERENCE_SHA256,
    aret_git,
    build_repository,
    git,
    reference_digest,
    touch_memory,
)


VERA_PROFILE = """
mmu:
  version: "2.0"
project:
  id: "c13-git-parity"
  name: "C13 Git Parity"
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
""".strip() + "\n"

ENABLED = {
    "format": "vera-memory-sync-policy/v1",
    "auto_commit": True,
    "auto_push": False,
    "remote": "origin",
    "branch": "CURRENT",
}


def _vera_store(
    root: Path, *, policy: dict[str, object] | None, repository: bool = True, remote: bool = False
) -> MemoryStore:
    """Monter un projet VERA à la forme que sa propre synchronisation attend.

    `remote` monte un vrai dépôt nu et l'enregistre sous `origin`. Il ne sert pas au confort :
    sans lui, un refus de policy et un refus faute de remote donnent tous deux un motif où le mot
    « origin » apparaît, et un test qui cherche ce mot passerait sans que la policy ait rien
    refusé. Mesuré : c'est exactement ce qui se produisait.
    """
    root.mkdir(parents=True, exist_ok=True)
    if repository:
        git(root, "init", "-b", "main")
        git(root, "config", "user.name", "VERA parity tests")
        git(root, "config", "user.email", "vera-tests@example.invalid")
    memory = root / ".vera-mmu"
    memory.mkdir()
    profile = memory / "project.yaml"
    profile.write_text(VERA_PROFILE, encoding="utf-8")
    store = MemoryStore.open(load_profile(profile), profile)
    store.connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
    if policy is not None:
        (memory / "sync-policy.json").write_text(json.dumps(policy, sort_keys=True) + "\n", encoding="utf-8")
    (memory / ".gitignore").write_text("*.sqlite-wal\n*.sqlite-shm\nruntime/\n", encoding="utf-8")
    if repository:
        git(root, "add", "--", ".vera-mmu")
        git(root, "commit", "-m", "VERA memory baseline")
    if remote:
        bare = root.parent / f"{root.name}-remote.git"
        subprocess.run(["git", "init", "--bare", str(bare)], check=True, text=True, capture_output=True)
        git(root, "remote", "add", "origin", str(bare))
        git(root, "push", "-u", "origin", "main")
    return store


def _mutate(store: MemoryStore) -> dict[str, object]:
    with store.transaction() as connection:
        store.append_audit(connection, "C13_PARITY_MUTATION", {"source": "parity"})
    return store.last_sync_status


class AretC13GitSyncParityTests(unittest.TestCase):
    def test_the_vendored_git_source_is_the_pinned_aret_file(self) -> None:
        self.assertEqual(reference_digest(), REFERENCE_SHA256)

    # --- le défaut, mesuré en exécutant ARET --------------------------------

    def test_arets_status_parser_misreads_an_unstaged_change_as_outside_the_memory(self) -> None:
        """Le défaut, isolé à sa cause : `.strip()` puis une découpe à position fixe.

        La sortie brute de Git commence par un espace ; `invoke()` le retire ; `changes()` découpe
        toujours à l'indice 3 ; le chemin perd son premier caractère. On l'épingle sur les deux
        faces — le chemin rendu et les deux caractères d'état, qui se retrouvent décalés eux aussi —
        pour qu'une réécriture du parseur qui corrigerait l'un sans l'autre se voie.
        """
        module = aret_git()
        with TemporaryDirectory() as temp:
            root = Path(temp) / "aret"
            memory = build_repository(root)
            touch_memory(memory)

            raw = git(root, "status", "--porcelain=v1", "--untracked-files=all")
            parsed = module.changes(root)

        self.assertTrue(raw.startswith(" M "), "la sortie Git n’a plus la forme mesurée")
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["path"], "ret-memory/.aret-memory/aret_memory.sqlite")
        self.assertEqual((parsed[0]["index"], parsed[0]["worktree"]), ("M", " "))

    def test_arets_automatic_sync_refuses_a_memory_that_is_the_only_thing_that_changed(self) -> None:
        """La conséquence : le cas nominal est refusé, et le motif cite un fichier de la mémoire."""
        module = aret_git()
        with TemporaryDirectory() as temp:
            root = Path(temp) / "aret"
            memory = build_repository(root, policy=json.dumps({"auto_commit": True, "auto_push": False}))
            touch_memory(memory)
            head_before = git(root, "rev-parse", "HEAD").strip()
            outcome = module.automatic_sync(root, None, "PARITY")
            head_after = git(root, "rev-parse", "HEAD").strip()

        self.assertTrue(outcome["enabled"])
        self.assertFalse(outcome["committed"])
        self.assertTrue(outcome["refused"])
        self.assertIn("hors du Memory Store", str(outcome["reason"]))
        self.assertIn("ret-memory/.aret-memory", str(outcome["reason"]))
        self.assertEqual(head_after, head_before, "ARET aurait finalement committé")

    def test_arets_end_of_turn_sync_commits_nothing_and_reports_no_error(self) -> None:
        """Le pire des deux : le tour se termine sur un succès apparent, mémoire non versionnée.

        `sync_memory_only` ne lève jamais, par conception — c'est un point de fin de tour. Mais il
        filtre son périmètre avec le même parseur, ne trouve donc aucun changement mémoire, et
        annonce « aucun changement à committer » alors que la base est modifiée sur le disque.
        """
        module = aret_git()
        with TemporaryDirectory() as temp:
            root = Path(temp) / "aret"
            memory = build_repository(root)
            touch_memory(memory)
            head_before = git(root, "rev-parse", "HEAD").strip()
            outcome = module.sync_memory_only(root, None, "PARITY", do_push=False)
            remaining = git(root, "status", "--porcelain=v1").strip()

        self.assertNotIn("error", outcome, "la fonction aurait signalé quelque chose")
        self.assertFalse(outcome["committed"])
        self.assertIn("Aucun changement", str(outcome["reason"]))
        self.assertEqual(outcome["head"], head_before)
        self.assertIn("aret-memory/.aret-memory/aret_memory.sqlite", remaining)

    def test_the_defect_hides_as_soon_as_another_line_comes_first(self) -> None:
        """Pourquoi personne ne l'a vu : il suffit d'un fichier indexé au tri pour que ça marche.

        Une ligne indexée commence par une lettre, `.strip()` n'a plus rien à retirer, et toutes
        les lignes — y compris celle de la mémoire — se découpent correctement. Un test écrit avec
        un `git add` préalable passe donc, et ne dit rien du cas ordinaire.
        """
        module = aret_git()
        with TemporaryDirectory() as temp:
            root = Path(temp) / "aret"
            memory = build_repository(root)
            touch_memory(memory)
            (root / "aaa.txt").write_text("indexé\n", encoding="utf-8")
            git(root, "add", "aaa.txt")
            paths = [item["path"] for item in module.changes(root)]

        self.assertIn("aret-memory/.aret-memory/aret_memory.sqlite", paths)
        self.assertNotIn("ret-memory/.aret-memory/aret_memory.sqlite", paths)

    def test_vera_versions_the_same_situation_because_it_parses_no_path_at_all(self) -> None:
        """Le pendant VERA de la situation exacte qui fait échouer ARET.

        Deux faces : le comportement — la mémoire est bien committée — et la raison — la source ne
        découpe aucun chemin, elle délègue le périmètre à Git sous forme de pathspec. La seconde
        est ce qui empêche le défaut de revenir par une autre porte.
        """
        with TemporaryDirectory() as temp:
            root = Path(temp) / "vera"
            store = _vera_store(root, policy=ENABLED)
            try:
                result = _mutate(store)
                committed = git(root, "show", "--format=", "--name-only", "HEAD").split()
            finally:
                store.close()

        self.assertEqual(result["status"], "COMMITTED")
        self.assertTrue(result["committed"])
        self.assertTrue(committed)
        self.assertTrue(all(path.startswith(".vera-mmu") for path in committed), committed)

        source = (Path(__file__).resolve().parents[1] / "src" / "vera_mmu" / "memory_sync.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("--porcelain=v1", source, "VERA n’interroge plus le statut")
        self.assertIn("return bool(changed)", source, "VERA lit désormais autre chose que le vide")
        self.assertNotIn("line[3:]", source)
        self.assertNotIn("splitlines()", source, "VERA découperait la sortie de Git ligne à ligne")

    # --- NoVCS ---------------------------------------------------------------

    def test_without_git_aret_propagates_gits_own_error_and_vera_answers_without_running_it(self) -> None:
        """Même absence, deux natures de réponse : une erreur d'outil, ou une observation.

        VERA répond sur deux canaux et les deux sont épinglés : `inspect_vcs` constate `NO_VCS`
        sans lancer la moindre commande, et la synchronisation rend un refus non fatal — la
        transaction SQLite déjà validée n'est pas annulée parce que Git manque.
        """
        module = aret_git()
        with TemporaryDirectory() as temp:
            aret_root = Path(temp) / "aret"
            (aret_root / ARET_MEMORY_DIR).mkdir(parents=True)
            with self.assertRaises(module.GitMemoryError) as raised:
                module.status(aret_root, None)

            vera_root = Path(temp) / "vera"
            store = _vera_store(vera_root, policy=ENABLED, repository=False)
            try:
                observed = inspect_vcs(store).as_dict()
                result = _mutate(store)
                audited = store.connection.execute(
                    "SELECT COUNT(*) FROM store_audit WHERE action = 'C13_PARITY_MUTATION'"
                ).fetchone()[0]
            finally:
                store.close()

        self.assertIn("not a git repository", str(raised.exception))
        self.assertEqual(observed, {"provider": "NONE", "status": "NO_VCS"})
        self.assertEqual(result["status"], "REFUSED")
        self.assertFalse(result["committed"])
        self.assertEqual(audited, 1, "la mutation aurait été perdue faute de Git")

    # --- changements hors scope ---------------------------------------------

    def test_out_of_scope_changes_block_aret_entirely_and_only_narrow_vera(self) -> None:
        """La divergence que le registre annonçait, mesurée des deux côtés.

        ARET raisonne sur l'arbre de travail entier : un fichier de code en cours suffit à faire
        refuser la persistance de la mémoire. VERA raisonne par périmètre : elle commite la
        mémoire et laisse le fichier en cours exactement où il était. Le plus permissif n'est pas
        le moins sûr ici — c'est l'inverse, puisque le refus global d'ARET laisse la mémoire non
        versionnée sans que personne n'ait décidé de la laisser ainsi.

        Le hors-scope est **suivi et modifié**, pas seulement non suivi : mesuré, un fichier non
        suivi seul laisse passer un `commit -a`, et le test n'aurait donc rien dit du périmètre.
        """
        module = aret_git()
        with TemporaryDirectory() as temp:
            aret_root = Path(temp) / "aret"
            memory = build_repository(aret_root, policy=json.dumps({"auto_commit": True, "auto_push": False}))
            touch_memory(memory)
            (aret_root / "source.txt").write_text("modification non demandée\n", encoding="utf-8")
            (aret_root / "work-in-progress.txt").write_text("code en cours\n", encoding="utf-8")
            aret_outcome = module.automatic_sync(aret_root, None, "PARITY")

            vera_root = Path(temp) / "vera"
            store = _vera_store(vera_root, policy=ENABLED)
            try:
                tracked = vera_root / "source.txt"
                tracked.write_text("version committée\n", encoding="utf-8")
                git(vera_root, "add", "--", "source.txt")
                git(vera_root, "commit", "-m", "code baseline")
                tracked.write_text("modification non demandée\n", encoding="utf-8")
                (vera_root / "work-in-progress.txt").write_text("code en cours\n", encoding="utf-8")
                vera_outcome = _mutate(store)
                worktree = git(vera_root, "status", "--porcelain=v1").strip().splitlines()
                committed = git(vera_root, "show", "--format=", "--name-only", "HEAD").split()
            finally:
                store.close()

        self.assertTrue(aret_outcome["refused"])
        self.assertIn("work-in-progress.txt", str(aret_outcome["reason"]))

        self.assertEqual(vera_outcome["status"], "COMMITTED")
        self.assertEqual(
            sorted(line.strip() for line in worktree),
            ["?? work-in-progress.txt", "M source.txt"],
            "VERA a touché au travail en cours",
        )
        self.assertTrue(all(path.startswith(".vera-mmu") for path in committed), committed)

    # --- WAL occupé ----------------------------------------------------------

    def test_a_busy_memory_stops_both_but_only_one_of_them_raises(self) -> None:
        """Le même refus, et deux façons de le rendre.

        ARET lève depuis le checkpoint, et l'exception traverse `automatic_sync` : l'appelant doit
        l'attraper. VERA rend un refus dans sa valeur de retour, parce qu'une mutation déjà validée
        ne redevient pas invalide quand la synchronisation ne peut pas se faire (I014 porte sur
        l'incertitude critique, pas sur un Git momentanément indisponible).
        """
        module = aret_git()
        with TemporaryDirectory() as temp:
            aret_root = Path(temp) / "aret"
            memory = build_repository(aret_root, policy=json.dumps({"auto_commit": True, "auto_push": False}))
            holder = sqlite3.connect(memory / "aret_memory.sqlite")
            try:
                holder.execute("PRAGMA journal_mode=WAL")
                holder.execute("BEGIN IMMEDIATE")
                holder.execute("INSERT INTO probe VALUES ('occupée')")
                with self.assertRaises(module.GitMemoryError) as raised:
                    module.automatic_sync(aret_root, None, "PARITY")
            finally:
                holder.close()

            vera_root = Path(temp) / "vera"
            store = _vera_store(vera_root, policy=ENABLED)
            blocker = sqlite3.connect(vera_root / ".vera-mmu" / "memory.sqlite")
            try:
                blocker.execute("PRAGMA journal_mode=WAL")
                blocker.execute("BEGIN IMMEDIATE")
                blocker.execute("CREATE TABLE IF NOT EXISTS c13_blocker (value TEXT)")
                vera_outcome = automatic_memory_sync(store, "C13_BUSY")
            finally:
                blocker.close()
                store.close()

        self.assertIn("Checkpoint WAL", str(raised.exception))
        self.assertEqual(vera_outcome["status"], "REFUSED")
        self.assertFalse(vera_outcome["committed"])
        self.assertIn("Checkpoint WAL", str(vera_outcome["reason"]))

    # --- HEAD détachée -------------------------------------------------------

    def test_on_a_detached_head_aret_pushes_a_name_from_a_file_and_vera_refuses(self) -> None:
        """Ce qu'on pousse quand il n'y a pas de branche courante.

        `sync_memory_only` résout la branche et saute le push proprement. Mais `automatic_sync`,
        le chemin déclenché par la policy, **ne consulte jamais HEAD** : il pousse le nom écrit
        dans `sync_policy.json`. Sur une HEAD détachée, cela pousse une référence qui n'est pas
        celle où le commit vient d'être fait. Le fait est extrait de l'arbre syntaxique d'ARET —
        exécuter ce cas demanderait un remote, et c'est l'absence d'appel qui est la preuve.

        VERA ne dispose d'aucun nom de branche à pousser : sa policy n'accepte que `CURRENT`, et
        `CURRENT` se résout par `symbolic-ref`, qui n'a pas de réponse sur une HEAD détachée.

        **Ce test a trouvé une règle morte dans VERA en écrivant ce cas.** `symbolic-ref --quiet`
        ne rend pas une sortie vide sur une HEAD détachée : il **sort en erreur**. Le refus passait
        donc par le gestionnaire générique — « Git a refusé l'opération 'symbolic-ref' » — et le
        diagnostic dédié, écrit juste en dessous, n'était atteignable par aucun chemin. Le refus
        avait lieu, mais il ne disait pas ce qui s'était passé. L'appel est désormais fait
        directement et le motif exigé ici est le diagnostic, pas l'erreur d'outil.
        """
        module = aret_git()
        with TemporaryDirectory() as temp:
            aret_root = Path(temp) / "aret"
            build_repository(aret_root)
            git(aret_root, "checkout", "--detach", "HEAD")
            self.assertIsNone(module.current_branch(aret_root))

            vera_root = Path(temp) / "vera"
            store = _vera_store(vera_root, policy={**ENABLED, "auto_push": True})
            try:
                git(vera_root, "checkout", "--detach", "HEAD")
                vera_outcome = _mutate(store)
            finally:
                store.close()

        tree = ast.parse(REFERENCE.read_text(encoding="utf-8"))
        automatic = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "automatic_sync"
        )
        called = {
            node.func.id for node in ast.walk(automatic)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertNotIn("current_branch", called, "ARET consulte désormais HEAD dans `automatic_sync`")
        pushes = [
            node for node in ast.walk(automatic)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "invoke"
            and any(isinstance(item, ast.Constant) and item.value == "push" for item in node.args)
        ]
        self.assertEqual(len(pushes), 1, "la référence ARET ne pousse plus au même endroit")
        destination = [ast.unparse(argument) for argument in pushes[0].args[-2:]]
        self.assertEqual(destination, ["policy['remote']", "policy['branch']"])

        self.assertEqual(vera_outcome["status"], "REFUSED")
        self.assertFalse(vera_outcome["pushed"])
        self.assertIn("HEAD détachée", str(vera_outcome["reason"]))

    # --- refus de push -------------------------------------------------------

    def test_aret_gates_the_push_on_a_flag_and_vera_has_no_destination_to_take(self) -> None:
        """Deux refus, et une seule des deux surfaces accepte qu'on lui nomme une destination.

        ARET refuse sans `--yes` : la garde est bonne, mais elle protège une commande dont le
        remote et la branche viennent de `argv`. VERA n'a rien de tel à garder — sa policy n'admet
        qu'`origin` et la branche courante, et refuse tout autre couple. C'est I008 : la borne la
        plus forte est celle qui ne laisse pas la valeur entrer (§32, cf. `C11`).
        """
        module = aret_git()
        with TemporaryDirectory() as temp:
            aret_root = Path(temp) / "aret"
            build_repository(aret_root)
            with self.assertRaises(module.GitMemoryError) as refused:
                module.push(aret_root, None, "origin", "main", False)

            vera_root = Path(temp) / "vera"
            store = _vera_store(
                vera_root, policy={**ENABLED, "auto_push": True, "remote": "ailleurs"}, remote=True
            )
            baseline = git(vera_root, "rev-parse", "HEAD").strip()
            try:
                elsewhere = _mutate(store)
                remote_tip = git(vera_root, "rev-parse", "origin/main").strip()
            finally:
                store.close()

            unreachable_root = Path(temp) / "vera-sans-remote"
            store = _vera_store(unreachable_root, policy={**ENABLED, "auto_push": True})
            try:
                unreachable = _mutate(store)
            finally:
                store.close()

        self.assertIn("--yes", str(refused.exception))

        parser = next(
            line for line in REFERENCE.read_text(encoding="utf-8").splitlines() if '"--remote"' in line
        )
        self.assertIn("default=", parser, "la référence ARET ne prend plus le remote en argument")

        self.assertEqual(elsewhere["status"], "REFUSED")
        self.assertIn("La politique VERA impose origin", str(elsewhere["reason"]))
        self.assertFalse(elsewhere["committed"], "la policy est lue avant tout commit")
        self.assertEqual(remote_tip, baseline, "le remote a reçu quelque chose malgré le refus")
        self.assertEqual(unreachable["status"], "REFUSED")
        self.assertFalse(unreachable["pushed"], "VERA aurait annoncé un push sans remote")

    # --- policy invalide -----------------------------------------------------

    def test_an_unknown_policy_key_is_dropped_by_aret_and_refused_by_vera(self) -> None:
        """Le contrat fermé, mesuré sur la même clef inventée.

        ARET ne retient que les clefs qu'il connaît : un `command` glissé dans le fichier disparaît
        sans un mot, et la policy est acceptée. VERA compare l'ensemble des clefs au contrat et
        refuse. Une clef ignorée en silence est une clef dont personne ne saura qu'elle n'a rien
        fait — et si un jour elle en faisait une, personne ne saurait non plus qu'elle a commencé.
        """
        module = aret_git()
        intruder = {"auto_commit": True, "auto_push": False, "command": "git push ailleurs"}
        with TemporaryDirectory() as temp:
            aret_root = Path(temp) / "aret"
            memory = build_repository(aret_root, policy=json.dumps(intruder))
            aret_policy = module.load_sync_policy(memory)

            vera_root = Path(temp) / "vera"
            store = _vera_store(vera_root, policy={**ENABLED, "command": "git push ailleurs"})
            try:
                vera_outcome = _mutate(store)
            finally:
                store.close()

        self.assertTrue(aret_policy["auto_commit"], "ARET a refusé la policy")
        self.assertNotIn("command", aret_policy)
        self.assertEqual(vera_outcome["status"], "REFUSED")
        self.assertIn("contrat fermé", str(vera_outcome["reason"]))

    def test_both_refuse_an_unreadable_policy_and_a_push_without_a_commit(self) -> None:
        """Ce sur quoi les deux sont d'accord, dit aussi — sinon la parité ne serait qu'un réquisitoire.

        Un JSON cassé et un `auto_push` sans `auto_commit` sont refusés des deux côtés. La
        divergence de `C13` porte sur le périmètre et sur le contrat fermé, pas sur ces deux-là.
        """
        module = aret_git()
        with TemporaryDirectory() as temp:
            aret_root = Path(temp) / "aret"
            memory = build_repository(aret_root)
            (memory / "sync_policy.json").write_text("{ pas du json", encoding="utf-8")
            with self.assertRaises(module.GitMemoryError):
                module.load_sync_policy(memory)
            (memory / "sync_policy.json").write_text(
                json.dumps({"auto_commit": False, "auto_push": True}), encoding="utf-8"
            )
            with self.assertRaises(module.GitMemoryError) as inconsistent:
                module.load_sync_policy(memory)

            vera_root = Path(temp) / "vera"
            store = _vera_store(vera_root, policy=None)
            try:
                (vera_root / ".vera-mmu" / "sync-policy.json").write_text("{ pas du json", encoding="utf-8")
                unreadable = _mutate(store)
                (vera_root / ".vera-mmu" / "sync-policy.json").write_text(
                    json.dumps({**ENABLED, "auto_commit": False, "auto_push": True}), encoding="utf-8"
                )
                contradictory = _mutate(store)
            finally:
                store.close()

        self.assertIn("auto_push exige auto_commit", str(inconsistent.exception))
        self.assertEqual(unreadable["status"], "REFUSED")
        self.assertEqual(contradictory["status"], "REFUSED")
        self.assertIn("auto_push exige auto_commit", str(contradictory["reason"]))

    def test_an_absent_policy_leaves_both_silent(self) -> None:
        """Le défaut par défaut : sans fichier, aucune des deux ne commite quoi que ce soit."""
        module = aret_git()
        with TemporaryDirectory() as temp:
            aret_root = Path(temp) / "aret"
            memory = build_repository(aret_root)
            touch_memory(memory)
            aret_policy = module.load_sync_policy(memory)
            aret_outcome = module.automatic_sync(aret_root, None, "PARITY")

            vera_root = Path(temp) / "vera"
            store = _vera_store(vera_root, policy=None)
            try:
                head_before = git(vera_root, "rev-parse", "HEAD").strip()
                vera_outcome = _mutate(store)
                head_after = git(vera_root, "rev-parse", "HEAD").strip()
            finally:
                store.close()

        self.assertFalse(aret_policy["auto_commit"])
        self.assertFalse(aret_outcome["enabled"])
        self.assertEqual(vera_outcome["status"], "DISABLED")
        self.assertEqual(head_after, head_before)


if __name__ == "__main__":
    unittest.main()

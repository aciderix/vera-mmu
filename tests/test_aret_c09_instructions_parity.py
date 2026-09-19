"""Test de parité du couplage `C09` — `SERVER_INSTRUCTIONS` d'ARET contre les instructions de VERA.

Le registre exige, pour promouvoir `C09` : « même entrée de profile/packs = même instruction/hash ;
aucune instruction ARET dans une instance Core sans pack ; snapshots ARET ».

**La différence est de nature, pas de contenu.** ARET embarque sa doctrine dans une constante de
module : un texte Python statique, identique pour tout projet qui lance ce serveur. VERA **compile**
les siennes depuis le profil, les catalogues et le playbook, et en publie le hash. Un texte statique
ne peut pas mentir sur le projet qu'il décrit — il ne le décrit pas ; c'est précisément le problème,
puisque la reprise s'appuie dessus.

**Le hash est la dimension qui se mesure.** Même entrée doit donner la même instruction, et une
entrée différente doit la déplacer — sinon le hash n'atteste rien. Les deux sens sont épinglés :
un hash qui ne bouge jamais et un hash qui bouge sans raison sont deux façons de ne rien prouver.
"""
from __future__ import annotations

import ast
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

import yaml

from vera_mmu.__main__ import main
from vera_mmu.project_bootstrap import apply_project_initialization, preview_project_initialization

from tests.aret_v1_server_reference import REFERENCE_SHA256, module_constant, reference_digest, tree


#: Des marqueurs de la doctrine ARET : s'ils apparaissent dans un Core sans pack, la frontière a cédé.
ARET_DOCTRINE_MARKERS = ("ARET-MMU", "aret_run_pipeline", "aret_run_oracle", "ARET://")


def _project(root: Path, project_id: str, *, template: str = "software") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    preview = preview_project_initialization(
        root, template=template, project_id=project_id, project_name=project_id
    )
    apply_project_initialization(root, preview, confirm=True)
    return root / ".vera-mmu" / "project.yaml"


def _generate(profile_path: Path, *, prepare: bool = True) -> dict:
    """Préparer la mémoire si besoin, compiler, et rendre la génération entière."""
    if prepare:
        with redirect_stdout(StringIO()):
            assert main(["init", str(profile_path)]) == 0
            assert main(["sync-capabilities", str(profile_path)]) == 0
    output = StringIO()
    with redirect_stdout(output):
        assert main(["generate", str(profile_path), "--adapter", "generic-mcp"]) == 0
    return json.loads(output.getvalue())["generation"]


def _instructions_hash(profile_path: Path) -> tuple[str, str]:
    """Compiler et rendre `(instructions_hash, mcp_build_hash)` pour un projet prêt."""
    generation = _generate(profile_path)
    return generation["instructions_hash"], generation["mcp_build_hash"]


class AretC09InstructionsParityTests(unittest.TestCase):
    def test_the_vendored_server_is_the_pinned_aret_source(self) -> None:
        self.assertEqual(reference_digest(), REFERENCE_SHA256)

    # --- ce qu'ARET embarque ------------------------------------------------

    def test_arets_instructions_are_a_static_module_constant(self) -> None:
        """Extrait de l'arbre syntaxique : c'est une constante, pas une valeur dérivée.

        Si `SERVER_INSTRUCTIONS` devenait un appel de fonction, la nature du couplage changerait et
        ce test le dirait — au lieu de continuer à décrire un texte statique qui n'existerait plus.
        """
        constant = module_constant("SERVER_INSTRUCTIONS")
        self.assertIsNotNone(constant, "`SERVER_INSTRUCTIONS` n’est plus une constante de module")
        self.assertIsInstance(constant.value, str)
        self.assertGreater(len(constant.value), 500)
        for marker in ("PROVEN exige une preuve PASS admissible", "aret_run_pipeline"):
            self.assertIn(marker, constant.value, marker)

    def test_arets_instructions_mention_no_project_of_their_own(self) -> None:
        """Un texte identique pour tout projet ne peut rien dire du projet en cours.

        Ce n'est pas un reproche gratuit : la reprise s'appuie sur ces instructions, et c'est
        exactement ce que `C09` demande de remplacer par une compilation.
        """
        constant = module_constant("SERVER_INSTRUCTIONS")
        assigned = [
            node for node in tree().body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "SERVER_INSTRUCTIONS" for target in node.targets)
        ]
        self.assertEqual(len(assigned), 1)
        self.assertNotIsInstance(assigned[0].value, (ast.Call, ast.JoinedStr, ast.BinOp))
        self.assertNotIn("{", constant.value.replace("{}", ""), "le texte porterait un gabarit")

    # --- ce que VERA compile ------------------------------------------------

    def test_the_same_project_compiles_the_same_instructions_twice(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            profile_path = _project(Path(directory) / "projet", "c09-stable")
            first = _instructions_hash(profile_path)
            second = _generate(profile_path, prepare=False)

        self.assertEqual(first[0], second["instructions_hash"])
        self.assertEqual(first[1], second["mcp_build_hash"])
        self.assertEqual(len(first[0]), 64)

    def test_two_different_projects_compile_different_instructions(self) -> None:
        """Un hash qui ne bouge jamais n'atteste rien de plus qu'une constante."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            left = _instructions_hash(_project(root / "un", "c09-projet-un"))
            right = _instructions_hash(_project(root / "deux", "c09-projet-deux"))

        self.assertNotEqual(left[0], right[0], "l’instruction ne dépend pas du projet")
        self.assertNotEqual(left[1], right[1])

    def test_changing_the_playbook_moves_the_instruction_hash(self) -> None:
        """Les instructions citent le playbook verbatim ; le changer doit se voir dans le hash."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "projet"
            profile_path = _project(root, "c09-playbook")
            before = _instructions_hash(profile_path)
            playbook = root / ".vera-mmu" / "playbook.md"
            playbook.write_text(
                playbook.read_text(encoding="utf-8") + "\n- Une règle de projet ajoutée.\n",
                encoding="utf-8",
            )
            after = _generate(profile_path, prepare=False)

        self.assertNotEqual(before[0], after["instructions_hash"])

    def test_a_core_instance_without_the_pack_carries_no_aret_doctrine(self) -> None:
        """« Aucune instruction ARET dans une instance Core sans pack » — vérifié sur le texte."""
        with tempfile.TemporaryDirectory() as directory:
            profile_path = _project(Path(directory) / "projet", "c09-sans-pack")
            instructions = _generate(profile_path)["outputs"]["instructions"]

        self.assertGreater(len(instructions), 200)
        for marker in ARET_DOCTRINE_MARKERS:
            with self.subTest(marker):
                self.assertNotIn(marker, instructions, f"doctrine ARET dans un Core sans pack : {marker}")

    def test_the_project_reaches_the_instructions_by_each_of_its_two_routes(self) -> None:
        """Le pendant positif, épinglé route par route.

        L'identifiant entre deux fois : par l'identité du manifeste, qui donne l'en-tête `Project:`,
        et par le playbook, dont le titre le porte. Un test qui se contenterait de le chercher
        n'importe où dans le texte passerait encore si l'une des deux routes était coupée — mesuré :
        figer l'identifiant côté manifeste laissait ce test vert, parce que le playbook le portait
        toujours. Les deux sont donc exigées séparément.
        """
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "projet"
            profile_path = _project(root, "c09-domaine")
            instructions = _generate(profile_path)["outputs"]["instructions"]
            declared = yaml.safe_load(profile_path.read_text(encoding="utf-8"))

        identifier = declared["project"]["id"]
        self.assertIn(f"Project: {identifier}", instructions, "route du manifeste coupée")
        self.assertIn(f"— {identifier}", instructions, "route du playbook coupée")
        self.assertEqual(
            sum(1 for line in instructions.splitlines() if identifier in line), 2,
            "le nombre de routes a changé : la preuve doit être revue, pas élargie",
        )


if __name__ == "__main__":
    unittest.main()

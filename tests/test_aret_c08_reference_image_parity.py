"""Test de parité du couplage `C08` — les préconditions d'ARET et son image de référence.

Le registre exige, pour promouvoir `C08` : « Core installable sans toolchain ; doctor précise les
manques ; exécutabilité mesurée dans une image de référence ; tests `SKIPPED` explicites ». Les
trois premières dimensions et la quatrième sont couvertes ici et dans
`tests/test_aret_c07_c08_oracle_parity.py`, qui porte tout ce qui se mesure sans conteneur.

**Ce fichier porte la dimension qui manquait : l'image.** `docker/ci-toolchain/Dockerfile` est
versionné sous `fixtures/aret_v1/config/` et épinglé. Sa définition est lue ; et, quand l'image est
construite et que `VERA_C08_RUN_REFERENCE_IMAGE=1` est posé, **elle est exécutée** : la référence
d'oracles épinglée y est chargée par le `python3` du conteneur, et son propre `required_tools` y est
interrogé pour les neuf oracles.

**Pourquoi il ne suffisait pas de mesurer le préflight.** `C07` a établi que
`required_tools == []` ne prouve pas qu'un oracle peut tourner : `funcdiff` et `cpudiff` rendent
`[]` sur une machine sans `libunicorn`, qu'ils ne déclarent pas. Clore `C08` sur le seul préflight
aurait donc refait l'erreur que ce lot venait de documenter. Un oracle est donc **réellement
exécuté** dans l'image — `winehash`, qui compile un corpus au MinGW et le lance sous Wine, deux
outils absents de la machine hôte.

**Mesuré le 19 septembre 2026**, image construite depuis le Dockerfile épinglé :

* Les neuf oracles y ont `required_tools == []`, contre sept sur neuf en manque sur l'hôte.
* `winehash` y tourne réellement : 135 s, sortie de 295 lignes, artefact de 18 046 octets dont
  l'empreinte annoncée égale la recalculée.
* Son verdict est `UNKNOWN` — pas un défaut, la règle voulue : sa sortie est une mesure à comparer
  au runner Windows, jamais un gate de conformité. Ce que `C07` avait épinglé sur une chaîne
  fabriquée se vérifie ici sur une exécution réelle.

**Ce que l'image fait bien, et qui mérite d'être dit.** Elle se termine par un **smoke check de
construction** — `gcc -m32`, MinGW, `pkg-config unicorn`, SDL2 i386, wine, z3, clang, Xvfb. Une
image incomplète échoue bruyamment à la construction au lieu de sauter des oracles en silence à
l'exécution. C'est précisément le contraire du défaut de préflight que `C07` a mesuré, et dans le
même dépôt.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest

DOCKERFILE = (
    Path(__file__).resolve().parent / "fixtures" / "aret_v1" / "config" / "ci_toolchain_reference.Dockerfile"
)
#: SHA-256 de `docker/ci-toolchain/Dockerfile` du dépôt toolkit, commit `f052541`.
DOCKERFILE_SHA256 = "472f54aade554b872e956301ffae0e06822c705103e42800e6fbf55e564436e8"
IMAGE = os.environ.get("VERA_C08_IMAGE", "aret-ci-toolchain:local")
TOOLKIT = Path("/home/user/Automatic-reverse-engineering-toolkit")
VERA = Path(__file__).resolve().parents[1]

#: Les neuf oracles fermés d'ARET.
ARET_ORACLES = (
    "cpudiff", "difftest", "ehdiff", "funcdiff", "gnuehdiff",
    "stdcall_audit", "transpilediff", "winediff", "winehash",
)

#: Le script exécuté **dans** l'image : il ne dépend que de la bibliothèque standard.
IN_IMAGE = r"""
import json, sys
from pathlib import Path
sys.path.insert(0, "/vera")
from tests.aret_v1_oracles_reference import aret_oracles
oracles = aret_oracles()
print(json.dumps({
    "required_tools": {
        name: oracles.required_tools(oracles.ORACLES[name], Path("/toolkit"))
        for name in sorted(oracles.ORACLES)
    },
    "libunicorn": sorted(str(p) for p in Path("/usr/lib").rglob("libunicorn.so*"))[:2],
}))
"""


class C08ReferenceImageParityTests(unittest.TestCase):
    """L'image de référence : sa définition, puis son exécution."""

    # ------------------------------------------- la définition, sans conteneur

    def test_the_reference_image_definition_is_the_pinned_one(self) -> None:
        self.assertEqual(sha256(DOCKERFILE.read_bytes()).hexdigest(), DOCKERFILE_SHA256)

    def test_the_image_pins_its_base_and_declares_the_whole_oracle_stack(self) -> None:
        """Une image de référence qui ne fixe pas sa base n'est pas une référence.

        Le `FROM` est épinglé à `ubuntu:24.04`, et le Dockerfile dit pourquoi dans ses propres
        commentaires : les constantes Wine mesurées viennent de cette distribution, et une version
        plus récente les déplacerait **en silence** — « a REAL divergence must stay a finding,
        never an environment drift ».
        """
        text = DOCKERFILE.read_text(encoding="utf-8")
        self.assertIn("FROM ubuntu:24.04", text)
        self.assertIn("never an environment drift", text)
        for package in (
            "wine", "wine32:i386", "gcc-mingw-w64-i686", "g++-mingw-w64-i686",
            "libunicorn-dev", "z3", "clang", "xvfb", "fonts-liberation",
        ):
            with self.subTest(paquet=package):
                self.assertIn(package, text)
        # L'ordre d'installation est une leçon apprise, pas un détail : `libgd3:i386` d'abord.
        self.assertLess(text.index("libgd3:i386"), text.index("wine32:i386"))

    def test_the_image_fails_loudly_at_build_time_rather_than_skipping_at_run_time(self) -> None:
        """Le contraire exact du défaut de préflight que `C07` a mesuré, dans le même dépôt.

        `C07` a montré qu'ARET annonce « prêt » pour des oracles qui ne peuvent pas tourner, faute
        de déclarer `libunicorn`. Ce Dockerfile, lui, vérifie la pile entière **à la construction**
        et échoue si elle manque. La même équipe, deux disciplines opposées : il fallait mesurer
        les deux plutôt que juger l'une par l'autre.
        """
        text = DOCKERFILE.read_text(encoding="utf-8")
        smoke = text[text.index("RUN set -e;"):]
        # Les **instructions** du smoke check, pas son texte : sa bannière finale cite
        # `$(wine --version)`, si bien qu'une simple recherche de sous-chaîne trouvait la bannière
        # au lieu de la sonde et survivait à son retrait. Une mutation l'a montré.
        statements = [
            line.strip().rstrip("\\").strip()
            for line in smoke.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        statements = [line for line in statements if not line.startswith('echo "ARET CI toolchain ready')]
        for probe in (
            "gcc -m32", "i686-w64-mingw32-gcc --version", "pkg-config --exists unicorn",
            "wine --version", "z3 --version", "clang --version", "Xvfb",
        ):
            with self.subTest(sonde=probe):
                self.assertTrue(
                    any(probe in statement for statement in statements),
                    f"La sonde {probe!r} ne figure dans aucune instruction du smoke check",
                )

    # ------------------------------------ l'image elle-même, quand elle est là

    def _require_image(self) -> None:
        if os.environ.get("VERA_C08_RUN_REFERENCE_IMAGE", "").strip() != "1":
            self.skipTest(
                "Mesure dans l’image non demandée : poser VERA_C08_RUN_REFERENCE_IMAGE=1 "
                "(exige docker et l’image construite depuis le Dockerfile épinglé)"
            )
        if shutil.which("docker") is None:
            self.skipTest("docker absent de cette machine")
        if not TOOLKIT.is_dir():
            self.skipTest("Le dépôt toolkit de référence n’est pas monté dans ce conteneur")
        present = subprocess.run(
            ["docker", "image", "inspect", IMAGE], capture_output=True, text=True, check=False
        )
        if present.returncode != 0:
            self.skipTest(f"L’image {IMAGE} n’est pas construite")

    def _docker(self, *arguments: str, timeout: int) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "docker", "run", "--rm",
                "-v", f"{VERA}:/vera:ro",
                "-v", f"{TOOLKIT}:/toolkit:ro",
                IMAGE, *arguments,
            ],
            capture_output=True, text=True, timeout=timeout, check=False,
        )

    def test_i013_every_oracle_becomes_executable_inside_the_reference_image(self) -> None:
        """La dimension que `C08` réclamait : l'exécutabilité, mesurée **dans** l'image.

        La référence d'oracles épinglée est chargée par le `python3` du conteneur — elle ne dépend
        que de la bibliothèque standard — et c'est le `required_tools` d'ARET lui-même qui répond.
        Sur l'hôte, sept des neuf oracles ont des dépendances manquantes ; ici, aucun.
        """
        self._require_image()
        completed = self._docker("python3", "-c", IN_IMAGE, timeout=300)
        self.assertEqual(completed.returncode, 0, completed.stderr[-800:])
        report = json.loads(completed.stdout)

        self.assertEqual(tuple(sorted(report["required_tools"])), ARET_ORACLES)
        for name, missing in sorted(report["required_tools"].items()):
            with self.subTest(oracle=name):
                self.assertEqual(missing, [])
        # Et la bibliothèque qu'aucune spec ne déclare est bien là, elle aussi.
        self.assertTrue(any(path.endswith("libunicorn.so.2") for path in report["libunicorn"]))

    def test_i013_a_real_wine_oracle_executes_inside_the_reference_image(self) -> None:
        """Et il faut le faire tourner, parce qu'un préflight « prêt » ne prouve rien.

        `C07` a mesuré que `required_tools == []` peut mentir. Clore `C08` sur le seul préflight
        répéterait cette erreur. `winehash` est donc **exécuté** : il compile le corpus au MinGW et
        le lance sous Wine, deux outils absents de l'hôte.

        Son verdict est `UNKNOWN` par conception — sa sortie est une mesure à comparer au runner
        Windows, pas un gate. C'est la règle que `C07` avait épinglée sur une chaîne fabriquée,
        vérifiée ici sur une exécution réelle.
        """
        self._require_image()
        script = r"""
import hashlib, json, sys, tempfile
from pathlib import Path
sys.path.insert(0, "/vera")
from tests.aret_v1_oracles_reference import aret_oracles
from tests.aret_v1_repository_reference import memory_store
oracles = aret_oracles()
directory = tempfile.TemporaryDirectory()
store = memory_store(Path(directory.name).resolve(strict=True) / ".aret-memory")
outcome = oracles.run_oracle(store, Path("/toolkit"), "winehash", timeout_seconds=900)
artifact = Path(store.artifacts_dir) / outcome["artifact"]["path"]
body = json.loads(artifact.read_text(encoding="utf-8"))
print(json.dumps({
    "result": outcome["execution"]["result"],
    "exit_code": outcome["execution"]["exit_code"],
    "missing": outcome["execution"]["missing_dependencies"],
    "hash_ok": hashlib.sha256(artifact.read_bytes()).hexdigest() == outcome["artifact"]["sha256"],
    "lines": len([l for l in body.get("stdout", "").splitlines() if l.strip()]),
    "kind": outcome["proof"]["kind"],
}))
"""
        completed = self._docker("python3", "-c", script, timeout=1200)
        self.assertEqual(completed.returncode, 0, completed.stderr[-800:])
        report = json.loads(completed.stdout.strip().splitlines()[-1])

        self.assertEqual(report["missing"], [])
        self.assertEqual(report["exit_code"], 0)
        self.assertTrue(report["hash_ok"])
        self.assertEqual(report["kind"], "WINEHASH")
        # Il a réellement produit une liste, pas un squelette : le corpus est parcouru.
        self.assertGreater(report["lines"], 100)
        # Et il refuse de transformer sa mesure en verdict.
        self.assertEqual(report["result"], "UNKNOWN")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

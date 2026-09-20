"""Le bridge desktop parle-t-il UTF-8, quelle que soit la locale de la machine ?

Le protocole est du JSON lu côté Rust par `BufReader::read_line`, qui **exige** de l'UTF-8
valide. Python, lui, encode sa sortie selon la locale : `utf-8` sur Linux et macOS, mais la page
de code de la console sur Windows — `cp1252` sur une installation occidentale.

**Mesuré sur le runner Windows de la CI** (run #71) : `bridge_session_scans_a_native_root_over_stdio`
échouait sur « scan response: "Lecture bridge impossible." », c'est-à-dire une erreur d'E/S de
`read_line` — pas une fin de flux, qui aurait donné « Bridge local arrêté sans réponse. » Le
bridge avait parfaitement répondu ; ses octets n'étaient simplement pas lisibles.

Reproduit sur Linux en forçant `PYTHONIOENCODING=cp1252` : la réponse à `project.scan` fait
1411 octets dont le 244e est une continuation invalide, contre 1420 octets valides sans elle.
L'écart vient des accents — les messages de VERA sont en français, donc **toute** réponse un peu
substantielle en contient.

**C'était un défaut de production, pas de test.** L'application desktop Windows aurait échoué sur
sa première opération renvoyant du texte accentué, avec un message désignant un bridge muet plutôt
que l'encodage.

Deux diagnostics ont précédé le bon, et les deux étaient faux : le dialogue natif absent, puis
l'interpréteur `python3` introuvable. Le second avait sa propre part de vérité — il est corrigé et
son test passe sur Windows — mais il ne causait pas cette panne. *Une panne peut survivre à la
correction d'un vrai défaut voisin.*
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

#: Nonce minimal accepté par le bridge (24 caractères au moins).
NONCE = "n" * 32

#: Encodages sous lesquels la sortie doit rester de l'UTF-8 valide. `cp1252` est la page de code
#: d'une console Windows occidentale ; `ascii` est le cas le plus hostile qui soit.
ENCODAGES = (None, "utf-8", "cp1252", "latin-1", "ascii")


class DesktopBridgeEncodingTests(unittest.TestCase):
    """Le tube doit rester lisible par un lecteur qui n'accepte que l'UTF-8."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.racine = tempfile.TemporaryDirectory()
        root = Path(cls.racine.name)
        # Un marqueur suffit à déclencher un scan dont les libellés portent des accents.
        (root / "pyproject.toml").write_text("[project]\nname = 'sonde'\n", encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.racine.cleanup()

    def _interroger(self, encodage: str | None) -> bytes:
        """Interroge le bridge en octets bruts, sans décodage intermédiaire.

        Lire en mode texte masquerait précisément ce que ce test mesure : Python décoderait
        lui-même, et l'octet fautif ne serait jamais observé.
        """
        environnement = dict(os.environ)
        if encodage is None:
            environnement.pop("PYTHONIOENCODING", None)
        else:
            environnement["PYTHONIOENCODING"] = encodage
        requete = json.dumps(
            {
                "format": "vera-desktop-bridge/v1",
                "id": "sonde",
                "nonce": NONCE,
                "operation": "project.scan",
                "input": {},
            }
        )
        processus = subprocess.Popen(
            [sys.executable, "-m", "vera_mmu.desktop_bridge", "--project-root", self.racine.name, "--nonce", NONCE],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=environnement,
        )
        try:
            sortie, _ = processus.communicate(requete.encode("utf-8") + b"\n", timeout=60)
        finally:
            if processus.poll() is None:  # pragma: no cover - filet de sécurité
                processus.kill()
        return sortie.splitlines()[0] if sortie.splitlines() else b""

    def test_the_bridge_answers_in_utf8_whatever_the_locale_says(self) -> None:
        """Le cœur : sous chaque encodage, la ligne doit se décoder en UTF-8 **et** être du JSON."""
        for encodage in ENCODAGES:
            with self.subTest(encodage=encodage or "(defaut)"):
                ligne = self._interroger(encodage)
                self.assertTrue(ligne, "le bridge n’a rien répondu")
                try:
                    texte = ligne.decode("utf-8")
                except UnicodeDecodeError as exc:  # pragma: no cover - c’est le défaut mesuré
                    self.fail(f"sortie non-UTF-8 sous {encodage} : {exc.reason} à l’octet {exc.start}")
                charge = json.loads(texte)
                self.assertIs(charge.get("ok"), True, charge)

    def test_the_answer_really_contains_the_accents_that_broke_it(self) -> None:
        """Sans accent dans la réponse, le test précédent passerait pour de mauvaises raisons.

        C'est la différence entre mesurer une propriété et la constater par accident : un scan qui
        ne rendrait que de l'ASCII validerait tous les encodages sans rien prouver.
        """
        ligne = self._interroger(None)
        texte = ligne.decode("utf-8")
        self.assertTrue(
            any(caractere in texte for caractere in "éèêàçôûï«»’"),
            "la réponse ne contient aucun caractère non-ASCII : le test ne mesure plus rien",
        )
        # Et ces caractères tiennent sur plus d’un octet, ce qui est la condition du défaut.
        self.assertGreater(len(ligne), len(texte), "la réponse devrait être multi-octets en UTF-8")

    def test_the_request_side_is_utf8_too_not_only_the_answer(self) -> None:
        """L'entrée compte autant que la sortie, et une mutation l'a montré.

        La première version de ce fichier n'envoyait que de l'ASCII : neutraliser la
        reconfiguration de `sys.stdin` ne faisait donc rien tomber. Or côté Windows, Rust écrit de
        l'UTF-8 et Python aurait décodé en `cp1252` — un nom de projet accentué, saisi dans la
        fenêtre, serait arrivé déformé ou aurait fait échouer la requête.

        L'identifiant est renvoyé tel quel par le bridge : il sert donc de miroir exact de ce qui
        a été décodé à l'entrée.
        """
        identifiant = "sonde-é\u00e8-«ü»"
        requete = json.dumps(
            {
                "format": "vera-desktop-bridge/v1",
                "id": identifiant,
                "nonce": NONCE,
                "operation": "project.scan",
                "input": {},
            },
            ensure_ascii=False,
        )
        for encodage in ("cp1252", "latin-1", "ascii"):
            with self.subTest(encodage=encodage):
                environnement = dict(os.environ, PYTHONIOENCODING=encodage)
                processus = subprocess.Popen(
                    [
                        sys.executable, "-m", "vera_mmu.desktop_bridge",
                        "--project-root", self.racine.name, "--nonce", NONCE,
                    ],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                    env=environnement,
                )
                try:
                    sortie, _ = processus.communicate(requete.encode("utf-8") + b"\n", timeout=60)
                finally:
                    if processus.poll() is None:  # pragma: no cover
                        processus.kill()
                lignes = sortie.splitlines()
                self.assertTrue(lignes, "le bridge n’a rien répondu")
                charge = json.loads(lignes[0].decode("utf-8"))
                self.assertEqual(
                    charge.get("id"), identifiant,
                    "l’identifiant accentué n’a pas survécu à l’aller-retour",
                )

    def test_the_bridge_forces_the_encoding_itself_rather_than_trusting_its_caller(self) -> None:
        """L'encodage appartient au protocole, donc au bridge — pas à celui qui le lance.

        Le poser côté appelant ne couvrirait que le mode développement : le sidecar figé par
        PyInstaller est lancé autrement et aurait gardé le défaut.
        """
        from vera_mmu import desktop_bridge

        self.assertTrue(hasattr(desktop_bridge, "_force_utf8_stdio"))
        source = Path(desktop_bridge.__file__).read_text(encoding="utf-8")
        principal = source[source.index("def desktop_bridge_main")]  # existence
        self.assertTrue(principal)
        corps = source[source.index("def desktop_bridge_main") :]
        self.assertIn("_force_utf8_stdio()", corps.split("parser =")[0])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

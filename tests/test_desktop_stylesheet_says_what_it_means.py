"""Les deux règles de style que la vérification à l'écran a rendues nécessaires.

Vérifiées ici et non côté interface : vitest ne traite pas les feuilles de style, si bien qu'un
import `?raw` d'un `.css` y rend une chaîne vide. L'assertion aurait alors passé quoi qu'il
advienne de la règle — un test vert pour une raison qui n'a rien à voir avec ce qu'il annonce,
c'est-à-dire précisément la classe de défaut que ce dépôt traque. Le dépôt lit déjà ses workflows
depuis Python ; il lit sa feuille de style de la même façon.

**Ce que l'écran a montré.**

Le bandeau de message était le dernier élément avant le pied de page. En cliquant « Compiler le
preview » au milieu d'une page haute de plusieurs écrans, le motif du refus s'affichait hors de
vue et le bouton semblait inerte. J'ai d'abord rapporté que la fenêtre « avalait les refus » :
c'était faux, et ce mauvais diagnostic aurait conduit à réparer une chaîne qui fonctionnait.

Et `.journey-step` déclare trois colonnes — `34px` pour l'index, `1fr` pour le libellé, `auto`
pour l'état — alors que les listes de hachages de §34 et d'alertes n'ont pas d'index. Le
placement automatique tassait donc le libellé dans les 34 pixels réservés au numéro, et la valeur
venait se superposer au texte qui débordait : « profile_hash » illisible sous son propre hachage.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest

FEUILLE = Path(__file__).resolve().parents[1] / "apps" / "desktop" / "ui" / "src" / "styles.css"


class StylesheetTests(unittest.TestCase):
    """Deux règles, chacune née d'une capture d'écran."""

    def setUp(self) -> None:
        self.styles = FEUILLE.read_text(encoding="utf-8")

    def _regle(self, selecteur: str) -> str:
        """Rend le corps de la règle dont le sélecteur est **exactement** celui demandé.

        La première version cherchait le sélecteur n'importe où : pour `.notice`, elle tombait
        sur `.hero, .panel, .notice { … }`, une règle partagée qui ne porte pas l'épinglage — et
        elle échouait donc en désignant la mauvaise. Exiger une frontière avant le sélecteur
        évite de lire une règle pour une autre, ce qui est la même faute que juger une
        installation sur le marqueur d'un autre adapter.

        La dernière occurrence est retenue : en CSS, c'est elle qui l'emporte à spécificité
        égale, donc c'est elle qui décrit ce que la fenêtre fait vraiment.
        """
        motif = re.compile(r"(?:^|[}\n;])\s*" + re.escape(selecteur) + r"\s*\{([^}]*)\}")
        correspondances = list(motif.finditer(self.styles))
        self.assertTrue(correspondances, f"Règle absente : {selecteur}")
        return correspondances[-1].group(1)

    def test_the_message_band_stays_where_the_action_happens(self) -> None:
        corps = self._regle(".notice")
        self.assertIn("position: sticky", corps)
        self.assertIn("bottom:", corps)
        # Et au-dessus du contenu qu'il recouvre, sinon il resterait illisible.
        self.assertIn("z-index:", corps)

    def test_every_journey_row_child_names_its_column(self) -> None:
        """Nommer la colonne de chaque rôle rend la règle vraie quels que soient les enfants."""
        for selecteur, colonne in (
            (".journey-step > .journey-index", "1"),
            (".journey-step > .journey-label", "2"),
            (".journey-step > .journey-state", "3"),
        ):
            with self.subTest(selecteur=selecteur):
                self.assertIn(f"grid-column: {colonne}", self._regle(selecteur))

    def test_a_long_label_wraps_instead_of_overflowing_its_cell(self) -> None:
        self.assertIn("overflow-wrap: anywhere", self._regle(".journey-step > .journey-label"))

    def test_the_three_columns_the_rows_rely_on_are_still_declared(self) -> None:
        """Sans les trois colonnes, les placements ci-dessus ne désigneraient plus rien.

        Une règle qui nomme `grid-column: 3` dans une grille à deux colonnes crée une colonne
        implicite et passerait sans rien garantir : c'est la moitié du contrat qu'il faut tenir
        des deux côtés.
        """
        corps = self._regle(".journey-step")
        self.assertIn("grid-template-columns: 34px 1fr auto", corps)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

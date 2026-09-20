#!/usr/bin/env python3
"""Dérive le nom de tag qu'une release doit porter, et refuse tout autre.

**Pourquoi ce script existe plutôt qu'une ligne de YAML.** Un tag est une affirmation publique :
il dit que ce commit *est* cette version. Rien ne garantissait la cohérence entre le nom demandé
à la main et ce que les quatre manifestes déclarent — on pouvait poser `v0.1.0-rc.5` sur un arbre
disant `0.1.0rc4`, et le mensonge aurait survécu à toutes les vérifications suivantes puisque
plus personne ne relit un tag.

La règle est donc dérivée, jamais saisie : `pyproject.toml` porte la forme PEP 440, et le tag en
est la traduction SemVer préfixée. `0.1.0rc5` donne `v0.1.0-rc.5` ; une version finale `0.1.0`
donne `v0.1.0`.

Et parce qu'une règle que rien n'exerce ne garde rien, la dérivation vit ici, dans un module que
`tests/test_release_tag.py` met à l'épreuve — plutôt que dans une expression de workflow que seule
une release ferait tourner, c'est-à-dire trop tard.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]

#: `0.1.0`, `0.1.0rc5`, `1.2.3rc10` — les seules formes que le produit publie.
_PEP440 = re.compile(r"^(?P<base>\d+\.\d+\.\d+)(?:rc(?P<rc>\d+))?$")


class ReleaseTagError(RuntimeError):
    """Le nom de tag demandé ne correspond pas à ce que le dépôt déclare."""


def declared_version(root: Path = ROOT) -> str:
    """Lit la version PEP 440 du produit depuis `pyproject.toml`."""
    with (root / "pyproject.toml").open("rb") as flux:
        version = tomllib.load(flux).get("project", {}).get("version")
    if not isinstance(version, str) or not version:
        raise ReleaseTagError("Version absente ou invalide dans pyproject.toml.")
    return version


def expected_tag(version: str) -> str:
    """Traduit une version PEP 440 en nom de tag SemVer préfixé.

    Le refus nomme ce qu'il a reçu : une version hors forme fermée est plus probablement une
    faute de frappe qu'un choix, et le dire économise un aller-retour dans le code.
    """
    correspondance = _PEP440.fullmatch(version)
    if correspondance is None:
        raise ReleaseTagError(
            f"Version hors forme publiable : {version!r}. Attendu `X.Y.Z` ou `X.Y.ZrcN`."
        )
    base = correspondance.group("base")
    rc = correspondance.group("rc")
    return f"v{base}-rc.{rc}" if rc else f"v{base}"


def check(tag: str, root: Path = ROOT) -> str:
    """Vérifie qu'un tag demandé est bien celui que le dépôt déclare, et le rend."""
    attendu = expected_tag(declared_version(root))
    if tag != attendu:
        raise ReleaseTagError(
            f"Tag refusé : {tag!r} ne correspond pas à la version déclarée. Attendu {attendu!r}. "
            "Monter les quatre manifestes avant de publier, ou corriger le nom demandé."
        )
    return attendu


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dérive ou vérifie le nom de tag de release VERA.")
    parser.add_argument("--check", metavar="TAG", help="Refuse si ce tag ne correspond pas à la version déclarée.")
    arguments = parser.parse_args(argv)
    try:
        if arguments.check:
            print(check(arguments.check))
        else:
            print(expected_tag(declared_version()))
    except ReleaseTagError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

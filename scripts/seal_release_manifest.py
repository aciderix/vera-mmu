#!/usr/bin/env python3
"""Rattache **tous** les fichiers publiés au commit qui les a produits.

**Le défaut mesuré.** Sur la release `v0.1.0-rc.5`, la chaîne de provenance se fermait pour la
CLI et pour elle seule :

    asset GitHub → SHA256SUMS → release-manifest.json → binaire vmmu → source_revision → tag

Les quatre bundles de bureau — AppImage, `.deb`, `.msi`, `.exe` — n'y figuraient nulle part. Ils
n'étaient attestés que par le digest que GitHub calcule sur ce qu'on lui envoie, ce qui dit
seulement « le fichier n'a pas changé depuis le téléversement », jamais « ce fichier vient de ce
commit ». C'est précisément la question à laquelle ce produit existe pour répondre.

La cause est un ordre : `build_cli_bundle.py` écrit son manifeste **avant** que `tauri build`
n'ait produit quoi que ce soit. Ce script referme l'écart après coup, et refuse de sceller une
release dont un fichier publiable ne serait pas attesté — un artefact sans provenance publié à
côté d'artefacts qui en ont une est pire qu'inutile : il se fait croire couvert.

Le manifeste interne de l'archive CLI reste celui que l'archive contenait ; le manifeste publié
le **contient** et l'élargit. `tests/test_release_manifest_covers_every_asset.py` épingle cette
relation, pour que les deux ne puissent jamais se contredire.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_cli_bundle import ReleaseBundleError, canonical_json, file_sha256  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

#: Ce que chaque plateforme doit publier, en plus de l'archive CLI. La liste est fermée : un
#: bundle attendu et absent fait échouer la release plutôt que de la publier amputée.
EXPECTED_BUNDLES: dict[str, tuple[str, ...]] = {
    "x86_64-unknown-linux-gnu": (".AppImage", ".deb"),
    "x86_64-pc-windows-msvc": (".msi", "-setup.exe"),
}


def find_bundles(bundle_dir: Path, target: str) -> list[Path]:
    """Rend un fichier par suffixe attendu, et refuse toute ambiguïté.

    Deux fichiers pour un même suffixe rendraient le scellement dépendant de l'ordre du système
    de fichiers ; aucun signifie qu'un livrable manque. Les deux sont des refus.
    """
    attendus = EXPECTED_BUNDLES.get(target)
    if attendus is None:
        raise ReleaseBundleError(f"Target sans liste de bundles déclarée : {target}")
    trouves: list[Path] = []
    for suffixe in attendus:
        candidats = sorted(
            chemin
            for chemin in bundle_dir.rglob("*")
            if chemin.is_file() and not chemin.is_symlink() and chemin.name.endswith(suffixe)
        )
        if not candidats:
            raise ReleaseBundleError(f"Bundle `{suffixe}` attendu et absent sous {bundle_dir}.")
        if len(candidats) > 1:
            noms = ", ".join(chemin.name for chemin in candidats)
            raise ReleaseBundleError(f"Bundle `{suffixe}` ambigu : {noms}.")
        trouves.append(candidats[0])
    return trouves


def seal(cli_dir: Path, bundle_dir: Path, target: str, output_dir: Path) -> dict[str, Path]:
    """Écrit le manifeste complet et les sommes qui couvrent chaque fichier publié."""
    interne = json.loads((cli_dir / "release-manifest.json").read_text(encoding="utf-8"))
    archives = sorted(
        chemin for chemin in cli_dir.glob("vera-mmu-cli_*") if chemin.is_file() and not chemin.is_symlink()
    )
    if len(archives) != 1:
        raise ReleaseBundleError(f"{len(archives)} archive(s) CLI trouvée(s), une attendue.")
    archive = archives[0]

    publies = [archive, *find_bundles(bundle_dir, target)]
    complet = dict(interne)
    # Le binaire que l'archive contient reste attesté tel quel : c'est la seule entrée dont le
    # chemin est interne à une archive, et la retirer romprait la vérification faite au
    # déballage.
    complet["artifacts"] = [
        *interne["artifacts"],
        *({"path": chemin.name, "sha256": file_sha256(chemin)} for chemin in publies),
    ]
    output_dir.mkdir(parents=True, exist_ok=True)
    manifeste = output_dir / f"release-manifest-{target}.json"
    manifeste.write_bytes(canonical_json(complet))

    sommes = output_dir / f"SHA256SUMS-{target}"
    lignes = [f"{file_sha256(chemin)}  {chemin.name}" for chemin in publies]
    lignes.append(f"{file_sha256(manifeste)}  {manifeste.name}")
    sommes.write_text("\n".join(lignes) + "\n", encoding="utf-8")

    for chemin in publies:
        print(f"attesté {chemin.name}")
    print(f"Manifeste {manifeste}")
    print(f"Sommes {sommes}")
    return {"manifest": manifeste, "checksums": sommes}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scelle la provenance de tous les livrables d'une release VERA.")
    parser.add_argument("target")
    parser.add_argument("--bundle-dir", default="apps/desktop/src-tauri/target/release/bundle")
    parser.add_argument("--output-dir", default="livrables")
    arguments = parser.parse_args(argv)
    try:
        seal(
            ROOT / ".build" / "cli-release" / arguments.target,
            ROOT / arguments.bundle_dir,
            arguments.target,
            ROOT / arguments.output_dir,
        )
    except (ReleaseBundleError, KeyError, OSError, ValueError) as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

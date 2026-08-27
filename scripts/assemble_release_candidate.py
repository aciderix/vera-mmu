#!/usr/bin/env python3
"""Assemble les sorties natives en candidat de préversion hashé, sans publication."""

from __future__ import annotations

import argparse
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
FORMAT = "vera-release-candidate/v1"


class ReleaseCandidateError(RuntimeError):
    """Refus fail-closed d’assemblage de candidat de release."""


def _load_cli_builder():
    spec = importlib.util.spec_from_file_location("vera_release_cli_builder", ROOT / "scripts" / "build_cli_bundle.py")
    if spec is None or spec.loader is None:
        raise ReleaseCandidateError("Builder CLI introuvable.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise ReleaseCandidateError(f"Artefact absent ou ambigu : {path}")
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _revision() -> str:
    return subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def _verify_checksum_file(directory: Path, checksum_file: Path, required_names: set[str]) -> None:
    """Valide un SHA256SUMS source fermé avant de réutiliser ses artefacts."""

    if not checksum_file.is_file() or checksum_file.is_symlink():
        raise ReleaseCandidateError("SHA256SUMS CLI absent ou ambigu.")
    seen: set[str] = set()
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        parts = line.split("  ", 1)
        if len(parts) != 2 or len(parts[0]) != 64 or any(char not in "0123456789abcdef" for char in parts[0]):
            raise ReleaseCandidateError("Format SHA256SUMS CLI invalide.")
        digest, name = parts
        if name in seen or name not in required_names:
            raise ReleaseCandidateError("SHA256SUMS CLI contient une entrée ambiguë ou hors scope.")
        if _sha256(directory / name) != digest:
            raise ReleaseCandidateError(f"SHA256SUMS CLI invalide pour {name}.")
        seen.add(name)
    if seen != required_names:
        raise ReleaseCandidateError("SHA256SUMS CLI incomplet.")


def _checksum_lines(paths: tuple[Path, ...]) -> str:
    """Produit les lignes de checksum sans jamais inclure le checksum lui-même."""

    if any(path.name == "SHA256SUMS" for path in paths):
        raise ReleaseCandidateError("SHA256SUMS ne peut pas se hacher lui-même.")
    return "".join(f"{_sha256(path)}  {path.name}\n" for path in paths)


def _desktop_outputs(target: str) -> tuple[Path, ...]:
    bundle = ROOT / "apps" / "desktop" / "src-tauri" / "target" / "release" / "bundle"
    patterns = {
        "x86_64-unknown-linux-gnu": ("appimage/*.AppImage", "deb/*.deb"),
        "x86_64-pc-windows-msvc": ("nsis/*.exe", "msi/*.msi"),
    }
    try:
        files = tuple(path for pattern in patterns[target] for path in sorted(bundle.glob(pattern)))
    except KeyError as exc:
        raise ReleaseCandidateError(f"Target de release non pris en charge : {target}") from exc
    if len(files) != 2 or any(not path.is_file() or path.is_symlink() for path in files):
        raise ReleaseCandidateError("Les deux bundles desktop attendus sont requis pour le candidat.")
    return files


def assemble(target: str) -> Path:
    """Copie uniquement les artefacts produits pour un target et publie leur manifest local."""

    cli_builder = _load_cli_builder()
    spec = cli_builder.target_spec(target)
    version = cli_builder.product_version()
    cli_source = ROOT / ".build" / "cli-release" / target
    cli_archives = tuple(sorted(cli_source.glob(f"vera-mmu-cli_{version}_*.{spec.archive_suffix}")))
    cli_manifest = cli_source / "release-manifest.json"
    cli_sums = cli_source / "SHA256SUMS"
    if len(cli_archives) != 1 or not cli_manifest.is_file() or not cli_sums.is_file():
        raise ReleaseCandidateError("Candidat CLI incomplet : archive, manifest et SHA256SUMS requis.")
    _verify_checksum_file(cli_source, cli_sums, {cli_archives[0].name, cli_manifest.name})

    output = ROOT / ".build" / "release-candidate" / target
    shutil.rmtree(output, ignore_errors=True)
    output.mkdir(parents=True, exist_ok=True)
    candidates = (*cli_archives, cli_manifest, *_desktop_outputs(target))
    copied: list[Path] = []
    for source in candidates:
        if not source.is_file() or source.is_symlink():
            raise ReleaseCandidateError(f"Artefact source absent ou ambigu : {source}")
        destination = output / source.name
        if destination.exists():
            raise ReleaseCandidateError(f"Nom d’artefact ambigu : {source.name}")
        shutil.copyfile(source, destination)
        copied.append(destination)

    records = [{"path": path.name, "sha256": _sha256(path), "size_bytes": path.stat().st_size} for path in sorted(copied)]
    manifest = output / "release-manifest.json"
    manifest.write_text(
        json.dumps(
            {"artifacts": records, "format": FORMAT, "source_revision": _revision(), "target": target, "version": version},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    sums = output / "SHA256SUMS"
    sums.write_text(_checksum_lines((*copied, manifest)), encoding="utf-8")
    print(f"Assembled {output}")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Assemble un candidat VERA non signé depuis les builds natifs.")
    parser.add_argument("target")
    args = parser.parse_args(argv)
    try:
        assemble(args.target)
    except (ReleaseCandidateError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Construit une archive CLI VERA native et son manifest d’intégrité CI.

Ce script est un outil de build, pas une surface VERA destinée aux clients. Il
accepte seulement les deux triples publiables et construit exclusivement sous
``.build/cli-release``. Il ne crée ni tag, ni release, ni signature.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tomllib
import zipfile


ROOT = Path(__file__).resolve().parents[1]
FORMAT = "vera-release-manifest/v1"


@dataclass(frozen=True)
class TargetSpec:
    """Une cible CLI explicitement distribuable et son emballage canonique."""

    triple: str
    platform_name: str
    archive_suffix: str
    binary_name: str


TARGETS: dict[str, TargetSpec] = {
    "x86_64-unknown-linux-gnu": TargetSpec(
        triple="x86_64-unknown-linux-gnu",
        platform_name="linux-x64",
        archive_suffix="tar.gz",
        binary_name="vmmu",
    ),
    "x86_64-pc-windows-msvc": TargetSpec(
        triple="x86_64-pc-windows-msvc",
        platform_name="windows-x64",
        archive_suffix="zip",
        binary_name="vmmu.exe",
    ),
}


class ReleaseBundleError(RuntimeError):
    """Erreur de préparation d’un candidat d’archive CLI, toujours fail-closed."""


def host_tuple() -> str:
    """Retourne le seul triple de build permis par l’hôte Python courant."""

    system = platform.system().lower()
    machine = platform.machine().lower()
    if machine not in {"x86_64", "amd64"}:
        raise ReleaseBundleError(f"Architecture hôte non publiée : {machine}")
    if system == "linux":
        return "x86_64-unknown-linux-gnu"
    if system == "windows":
        return "x86_64-pc-windows-msvc"
    raise ReleaseBundleError(f"Système hôte non publié : {system}")


def target_spec(target: str) -> TargetSpec:
    """Résout exclusivement une cible de la liste de publication."""

    if target not in TARGETS:
        raise ReleaseBundleError(f"Target CLI non pris en charge : {target}")
    if target != host_tuple():
        raise ReleaseBundleError(f"La CLI doit être construite nativement : target={target}, host={host_tuple()}")
    return TARGETS[target]


def _version_from_cargo(path: Path) -> str:
    match = re.search(r'^version\s*=\s*"([0-9A-Za-z.+-]+)"\s*$', path.read_text(encoding="utf-8"), flags=re.MULTILINE)
    if match is None:
        raise ReleaseBundleError(f"Version Cargo absente : {path}")
    return match.group(1)


def product_version() -> str:
    """Exige l’alignement de la version de release, avec normalisation PEP 440."""

    with (ROOT / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)
    package = json.loads((ROOT / "apps" / "desktop" / "package.json").read_text(encoding="utf-8"))
    tauri = json.loads((ROOT / "apps" / "desktop" / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))
    python_version = pyproject.get("project", {}).get("version")
    if isinstance(python_version, str):
        python_version = re.sub(r"^([0-9]+\.[0-9]+\.[0-9]+)rc([0-9]+)$", r"\1-rc.\2", python_version)
    versions = {
        "pyproject": python_version,
        "package.json": package.get("version"),
        "Cargo.toml": _version_from_cargo(ROOT / "apps" / "desktop" / "src-tauri" / "Cargo.toml"),
        "tauri.conf.json": tauri.get("version"),
    }
    if not all(isinstance(value, str) and value for value in versions.values()):
        raise ReleaseBundleError("Un manifeste de version VERA est absent ou invalide.")
    unique = set(versions.values())
    if len(unique) != 1:
        raise ReleaseBundleError(f"Versions VERA divergentes : {versions}")
    return next(iter(unique))


def source_revision() -> str:
    """Retourne le SHA du checkout, en refusant un arbre sale de release."""

    status = subprocess.run(
        ["git", "status", "--porcelain=v1"], cwd=ROOT, check=True, capture_output=True, text=True
    )
    if status.stdout.strip():
        raise ReleaseBundleError("Le candidat CLI exige un checkout Git propre.")
    revision = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ReleaseBundleError("Révision Git de release invalide.")
    return revision


def file_sha256(path: Path) -> str:
    """Hache un fichier régulier sans suivre un lien symbolique."""

    if not path.is_file() or path.is_symlink():
        raise ReleaseBundleError(f"Fichier de release absent ou ambigu : {path}")
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: object) -> bytes:
    """Sérialise le manifest de release de manière stable et diffable."""

    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def build_binary(spec: TargetSpec, staging: Path) -> Path:
    """Construit le seul exécutable CLI autorisé dans une zone temporaire fixe."""

    dist_dir = staging / "binary"
    work_dir = ROOT / ".build" / "cli-release-work" / spec.triple
    shutil.rmtree(work_dir, ignore_errors=True)
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        "vmmu",
        "--paths",
        str(ROOT / "src"),
        "--collect-submodules",
        "vera_mmu",
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(work_dir / "work"),
        "--specpath",
        str(work_dir / "spec"),
        str(ROOT / "scripts" / "cli_entry.py"),
    ]
    subprocess.run(command, check=True, cwd=ROOT)
    binary = dist_dir / spec.binary_name
    if not binary.is_file() or binary.is_symlink():
        raise ReleaseBundleError(f"CLI native attendue absente ou ambiguë : {binary}")
    return binary


def _write_archive(spec: TargetSpec, archive: Path, binary: Path, manifest: Path) -> None:
    if spec.archive_suffix == "zip":
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
            bundle.write(binary, arcname=spec.binary_name)
            bundle.write(manifest, arcname="release-manifest.json")
        return
    with tarfile.open(archive, "w:gz", format=tarfile.PAX_FORMAT) as bundle:
        bundle.add(binary, arcname=spec.binary_name, recursive=False)
        bundle.add(manifest, arcname="release-manifest.json", recursive=False)


def build_bundle(target: str) -> dict[str, Path]:
    """Construit archive, manifest et SHA256SUMS de candidat sans publication."""

    spec = target_spec(target)
    version = product_version()
    revision = source_revision()
    output_dir = ROOT / ".build" / "cli-release" / spec.triple
    staging = ROOT / ".build" / "cli-release-stage" / spec.triple
    shutil.rmtree(output_dir, ignore_errors=True)
    shutil.rmtree(staging, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    staging.mkdir(parents=True, exist_ok=True)
    binary = build_binary(spec, staging)
    manifest = output_dir / "release-manifest.json"
    manifest.write_bytes(
        canonical_json(
            {
                "artifacts": [{"path": spec.binary_name, "sha256": file_sha256(binary)}],
                "format": FORMAT,
                "platform": spec.platform_name,
                "source_revision": revision,
                "target": spec.triple,
                "version": version,
            }
        )
    )
    archive = output_dir / f"vera-mmu-cli_{version}_{spec.platform_name}.{spec.archive_suffix}"
    _write_archive(spec, archive, binary, manifest)
    sums = output_dir / "SHA256SUMS"
    sums.write_text(
        f"{file_sha256(archive)}  {archive.name}\n{file_sha256(manifest)}  {manifest.name}\n",
        encoding="utf-8",
    )
    print(f"Built {archive}")
    print(f"Manifest {manifest}")
    print(f"Checksums {sums}")
    return {"archive": archive, "manifest": manifest, "checksums": sums}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Construit un candidat CLI VERA natif et non signé.")
    parser.add_argument("target", nargs="?", default=host_tuple())
    args = parser.parse_args(argv)
    try:
        build_bundle(args.target)
    except (ReleaseBundleError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

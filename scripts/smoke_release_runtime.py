#!/usr/bin/env python3
"""Smoke tests bornés d'un candidat Linux VERA, sans interaction utilisateur."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile


ROOT = Path(__file__).resolve().parents[1]
FORMAT = "vera-release-candidate/v1"
LINUX_TARGET = "x86_64-unknown-linux-gnu"


class SmokeError(RuntimeError):
    """Le candidat n'est pas exécutable selon le contrat de smoke test."""


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_member_path(root: Path, name: str) -> Path:
    candidate = root / name
    if not name or Path(name).is_absolute() or candidate.resolve().parent != root.resolve() and root.resolve() not in candidate.resolve().parents:
        raise SmokeError(f"Archive ambiguë : {name!r}")
    return candidate


def _verify_candidate(candidate: Path, target: str) -> dict[str, object]:
    manifest_path = candidate / "release-manifest.json"
    sums_path = candidate / "SHA256SUMS"
    if not manifest_path.is_file() or manifest_path.is_symlink() or not sums_path.is_file() or sums_path.is_symlink():
        raise SmokeError("Manifest ou SHA256SUMS final absent ou ambigu.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("format") != FORMAT or manifest.get("target") != target:
        raise SmokeError("Manifest de candidat inattendu.")
    records = manifest.get("artifacts")
    if not isinstance(records, list) or not records:
        raise SmokeError("Manifest de candidat incomplet.")
    expected: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise SmokeError("Entrée de manifest invalide.")
        name, digest, size = record.get("path"), record.get("sha256"), record.get("size_bytes")
        if not isinstance(name, str) or Path(name).name != name or name in expected:
            raise SmokeError("Nom de manifest ambigu.")
        artifact = candidate / name
        if not artifact.is_file() or artifact.is_symlink() or artifact.stat().st_size != size or _sha256(artifact) != digest:
            raise SmokeError(f"Manifest invalide pour {name!r}.")
        expected.add(name)
    expected.add("release-manifest.json")
    actual: set[str] = set()
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        digest, separator, name = line.partition("  ")
        if separator != "  " or len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise SmokeError("SHA256SUMS final invalide.")
        if name in actual or name not in expected or name == "SHA256SUMS" or _sha256(candidate / name) != digest:
            raise SmokeError("SHA256SUMS final invalide ou hors périmètre.")
        actual.add(name)
    if actual != expected:
        raise SmokeError("SHA256SUMS final incomplet.")
    return manifest


def _extract_cli(archive: Path, destination: Path) -> Path:
    if archive.suffixes[-2:] != [".tar", ".gz"]:
        raise SmokeError("Archive CLI Linux attendue au format tar.gz.")
    with tarfile.open(archive, "r:gz") as bundle:
        for member in bundle.getmembers():
            if member.issym() or member.islnk() or not member.isfile():
                raise SmokeError("Archive CLI contient une entrée non régulière.")
            target = _safe_member_path(destination, member.name)
            with bundle.extractfile(member) as source, target.open("wb") as output:
                if source is None:
                    raise SmokeError("Entrée CLI illisible.")
                shutil.copyfileobj(source, output)
            target.chmod(target.stat().st_mode | 0o100)
    binary = destination / "vmmu"
    if not binary.is_file() or binary.is_symlink():
        raise SmokeError("Binaire CLI vmmu absent de l’archive.")
    return binary


def _run(command: list[str], *, timeout: int = 20) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise SmokeError(f"Commande expirée : {' '.join(command)}") from exc


def _require_success(command: list[str], *, contains: str | None = None) -> str:
    result = _run(command)
    output = f"{result.stdout}\n{result.stderr}"
    if result.returncode != 0 or (contains is not None and contains not in output):
        raise SmokeError(f"Commande CLI refusée ({result.returncode}) : {output[-1200:]}")
    return result.stdout


def _smoke_cli(binary: Path) -> None:
    _require_success([str(binary), "--help"], contains="usage: vmmu")
    with tempfile.TemporaryDirectory(prefix="vera-cli-smoke-") as raw_project:
        project = Path(raw_project)
        (project / "README.md").write_text("runtime smoke only\n", encoding="utf-8")
        payload = json.loads(_require_success([str(binary), "scan", str(project)]))
        if payload.get("ok") is not True or payload.get("scan", {}).get("status") != "OBSERVED":
            raise SmokeError("Le scan CLI ne retourne pas OBSERVED.")
        if (project / ".vera-mmu").exists():
            raise SmokeError("Le scan CLI a écrit dans le projet de smoke test.")


def _launch_desktop(command: list[str], label: str) -> None:
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if process.poll() is not None:
                stdout, stderr = process.communicate(timeout=2)
                raise SmokeError(f"{label} s’est arrêté prématurément ({process.returncode}) : {(stdout + stderr)[-1200:]}")
            time.sleep(0.5)
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.communicate(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate(timeout=8)


def _desktop_artifact(candidate: Path, suffix: str) -> Path:
    matches = tuple(sorted(candidate.glob(f"*{suffix}")))
    if len(matches) != 1 or not matches[0].is_file() or matches[0].is_symlink():
        raise SmokeError(f"Bundle desktop {suffix} absent ou ambigu.")
    return matches[0]


def _smoke_linux_desktop(candidate: Path) -> None:
    xvfb = shutil.which("xvfb-run")
    dpkg_deb = shutil.which("dpkg-deb")
    if not xvfb or not dpkg_deb:
        raise SmokeError("xvfb-run ou dpkg-deb indisponible pour le smoke Linux.")
    appimage = _desktop_artifact(candidate, ".AppImage")
    appimage.chmod(appimage.stat().st_mode | 0o100)
    _launch_desktop([xvfb, "-a", str(appimage), "--appimage-extract-and-run"], "AppImage")
    deb = _desktop_artifact(candidate, ".deb")
    with tempfile.TemporaryDirectory(prefix="vera-deb-smoke-") as raw_root:
        root = Path(raw_root)
        extracted = _run([dpkg_deb, "-x", str(deb), str(root)])
        if extracted.returncode != 0:
            raise SmokeError(f"Extraction Debian refusée : {extracted.stderr[-1200:]}")
        candidates = tuple(path for path in root.rglob("VERA-MMU") if path.is_file() and not path.is_symlink())
        if len(candidates) != 1:
            raise SmokeError("Exécutable VERA-MMU absent ou ambigu dans le paquet Debian.")
        candidates[0].chmod(candidates[0].stat().st_mode | 0o100)
        _launch_desktop([xvfb, "-a", str(candidates[0])], "payload Debian")


def smoke(target: str) -> None:
    if target != LINUX_TARGET or not sys.platform.startswith("linux"):
        raise SmokeError("Ce smoke Python est réservé au candidat Linux x64 natif.")
    candidate = ROOT / ".build" / "release-candidate" / target
    _verify_candidate(candidate, target)
    archives = tuple(candidate.glob("vera-mmu-cli_*.tar.gz"))
    if len(archives) != 1:
        raise SmokeError("Archive CLI Linux absente ou ambiguë.")
    with tempfile.TemporaryDirectory(prefix="vera-cli-extract-") as raw:
        _smoke_cli(_extract_cli(archives[0], Path(raw)))
    _smoke_linux_desktop(candidate)
    print(json.dumps({"ok": True, "target": target, "checks": ["integrity", "cli-help", "cli-observed-scan", "appimage-start", "deb-payload-start"]}, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke test d’exécution Linux d’un candidat VERA non signé.")
    parser.add_argument("target", choices=[LINUX_TARGET])
    args = parser.parse_args(argv)
    try:
        smoke(args.target)
    except (SmokeError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

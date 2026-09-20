#!/usr/bin/env python3
"""Build the VERA desktop bridge as a native, Tauri-compatible sidecar."""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace


sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_cli_bundle as cli_bundle  # noqa: E402
from pyinstaller_resources import add_data_arguments  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_TARGETS = {"x86_64-unknown-linux-gnu", "x86_64-pc-windows-msvc"}


def host_tuple() -> str:
    completed = subprocess.run(
        ["rustc", "--print", "host-tuple"],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def pyinstaller_command(binary_name: str, binary_dir: Path, work_dir: Path) -> list[str]:
    """Compose la commande du sidecar, séparée de son exécution pour rester mesurable.

    Le sidecar est un second emballage, construit indépendamment de la CLI : c'est pourquoi le
    même oubli de ressources y a été livré aussi. `add_data_arguments` est la définition
    partagée, et `tests/test_cli_bundle_resources.py` compare les deux commandes côte à côte.
    """
    return [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        binary_name,
        "--paths",
        str(ROOT / "src"),
        "--collect-submodules",
        "vera_mmu",
        *add_data_arguments(),
        "--distpath",
        str(binary_dir),
        "--workpath",
        str(work_dir / "work"),
        "--specpath",
        str(work_dir / "spec"),
        str(ROOT / "scripts" / "desktop_bridge_entry.py"),
    ]


def cli_command(binary_name: str, binary_dir: Path, work_dir: Path) -> list[str]:
    """Compose la commande de la CLI embarquée dans le paquet de bureau.

    **Pourquoi le bureau transporte la CLI.** Mesuré sur la release `v0.1.0-rc.5` : le paquet
    n'embarquait que `vera-mmu-desktop` et son sidecar. Or c'est la CLI qui porte les
    sous-commandes `claude-code-local-mcp` et `-hook` que la configuration générée doit nommer.
    Faute de l'avoir, l'installation lancée depuis la fenêtre inscrivait le chemin du **sidecar**,
    qui ne connaît pas ces sous-commandes : aucun serveur MCP ne pouvait démarrer.

    La commande dérive de `build_cli_bundle.pyinstaller_command`, jamais d'une copie : deux
    recettes pour un même binaire, c'est la garantie qu'elles divergeront un jour, et l'oubli de
    ressources livré simultanément dans les deux emballages a déjà montré ce que cela coûte.
    """
    spec = SimpleNamespace(binary_name=binary_name)
    commande = cli_bundle.pyinstaller_command(spec, binary_dir, work_dir)
    # Le nom de sortie est la seule différence : Tauri attend `<nom>-<triplet>` et retire le
    # suffixe à l'installation, si bien que le binaire installé s'appelle bien `vmmu`.
    index = commande.index("--name")
    commande[index + 1] = binary_name
    return commande


def main() -> int:
    parser = argparse.ArgumentParser(description="Construit le sidecar desktop VERA pour le triplet natif demandé.")
    parser.add_argument("target", nargs="?", default=host_tuple())
    args = parser.parse_args()
    target = args.target
    if target not in SUPPORTED_TARGETS:
        parser.error(f"Target desktop non pris en charge : {target}")
    actual_host = host_tuple()
    if target != actual_host:
        parser.error(f"Le sidecar doit être construit nativement : target={target}, host={actual_host}")

    binary_dir = ROOT / "apps" / "desktop" / "src-tauri" / "binaries"
    work_dir = ROOT / ".build" / "desktop-sidecar" / target
    suffixe = ".exe" if target.endswith("windows-msvc") else ""
    binary_name = f"vmmu-desktop-bridge-{target}"
    expected = binary_dir / f"{binary_name}{suffixe}"
    shutil.rmtree(work_dir, ignore_errors=True)
    binary_dir.mkdir(parents=True, exist_ok=True)

    subprocess.run(pyinstaller_command(binary_name, binary_dir, work_dir), check=True, cwd=ROOT)
    if not expected.is_file() or expected.is_symlink():
        raise RuntimeError(f"Sidecar attendu absent ou ambigu : {expected}")
    print(f"Built {expected}")

    cli_name = f"vmmu-{target}"
    cli_attendue = binary_dir / f"{cli_name}{suffixe}"
    subprocess.run(cli_command(cli_name, binary_dir, work_dir / "cli"), check=True, cwd=ROOT)
    if not cli_attendue.is_file() or cli_attendue.is_symlink():
        raise RuntimeError(f"CLI embarquée attendue absente ou ambiguë : {cli_attendue}")
    print(f"Built {cli_attendue}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

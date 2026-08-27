#!/usr/bin/env python3
"""Build the VERA desktop bridge as a native, Tauri-compatible sidecar."""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys


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
    binary_name = f"vmmu-desktop-bridge-{target}"
    expected = binary_dir / f"{binary_name}{'.exe' if target.endswith('windows-msvc') else ''}"
    shutil.rmtree(work_dir, ignore_errors=True)
    binary_dir.mkdir(parents=True, exist_ok=True)

    command = [
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
        "--distpath",
        str(binary_dir),
        "--workpath",
        str(work_dir / "work"),
        "--specpath",
        str(work_dir / "spec"),
        str(ROOT / "scripts" / "desktop_bridge_entry.py"),
    ]
    subprocess.run(command, check=True, cwd=ROOT)
    if not expected.is_file() or expected.is_symlink():
        raise RuntimeError(f"Sidecar attendu absent ou ambigu : {expected}")
    print(f"Built {expected}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

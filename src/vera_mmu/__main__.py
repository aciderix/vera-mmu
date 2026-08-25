"""Command-line entry point for the VERA-MMU foundation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .identity import ProfileError, load_profile, profile_identity


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vmmu",
        description="VERA-MMU foundation CLI: deterministic project profile identity.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    identity = subparsers.add_parser("identity", help="Validate a Project Profile and print its canonical identity.")
    identity.add_argument("profile", type=Path, help="Path to a project.yaml file.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "identity":
        try:
            identity = profile_identity(load_profile(args.profile))
        except ProfileError as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
            return 2
        print(json.dumps({"ok": True, "identity": identity.as_dict()}, ensure_ascii=False, sort_keys=True))
        return 0
    raise AssertionError(f"Commande non gérée : {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())

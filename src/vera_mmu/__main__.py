"""Command-line entry point for the VERA-MMU Core."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .identity import ProfileError, load_profile, profile_identity, project_identity
from .runtime import RuntimeLocator
from .workspace import WorkspaceError, resolve_workspace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vmmu",
        description="VERA-MMU Core CLI: deterministic profile and workspace validation.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    identity = subparsers.add_parser("identity", help="Validate a Project Profile and print its canonical identity.")
    identity.add_argument("profile", type=Path, help="Path to a project.yaml file.")

    inspect = subparsers.add_parser("inspect", help="Validate a Project Profile, workspace roots, and runtime confinement.")
    inspect.add_argument("profile", type=Path, help="Path to a project.yaml file.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        profile = load_profile(args.profile)
        if args.command == "identity":
            payload: dict[str, object] = {"ok": True, "identity": profile_identity(profile).as_dict()}
        elif args.command == "inspect":
            workspace = resolve_workspace(profile, args.profile)
            payload = {
                "ok": True,
                "profile_identity": profile_identity(profile).as_dict(),
                "project_identity": project_identity(profile, workspace).as_dict(),
                "workspace": workspace.as_dict(),
                "runtime": RuntimeLocator.from_workspace(profile, workspace).as_dict(),
            }
        else:
            raise AssertionError(f"Commande non gérée : {args.command}")
    except (ProfileError, WorkspaceError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

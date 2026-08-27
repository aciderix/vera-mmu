from __future__ import annotations

import argparse
from pathlib import Path

from vera_mmu.identity import load_profile
from vera_mmu.mcp_server import create_server
from vera_mmu.store import MemoryStore


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=Path, required=True)
    args = parser.parse_args()
    with MemoryStore.open(load_profile(args.profile), args.profile) as store:
        create_server(store).run("stdio")


if __name__ == "__main__":
    main()

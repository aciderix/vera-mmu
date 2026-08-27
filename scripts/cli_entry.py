#!/usr/bin/env python3
"""Entrée PyInstaller minimale pour la CLI VERA distribuée."""

from vera_mmu.__main__ import main


if __name__ == "__main__":
    raise SystemExit(main())

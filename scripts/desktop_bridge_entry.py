"""Entrée de packaging du sidecar desktop VERA, conservée hors de la logique métier."""
from vera_mmu.desktop_bridge import desktop_bridge_main


if __name__ == "__main__":
    raise SystemExit(desktop_bridge_main())

#!/usr/bin/env bash
# Compatibilité POSIX : délègue au builder Python portable Windows/Linux.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$root/scripts/build_desktop_sidecar.py" "$@"

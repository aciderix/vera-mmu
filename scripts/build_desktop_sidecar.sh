#!/usr/bin/env bash
# Build reproducible du sidecar desktop VERA : un seul bridge stdio, sans service réseau.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
target="${1:-$(rustc --print host-tuple)}"
binary_dir="$root/apps/desktop/src-tauri/binaries"
work_dir="$root/.build/desktop-sidecar/$target"
binary_name="vmmu-desktop-bridge-$target"

case "$target" in
  *linux*|*windows*) ;;
  *)
    printf 'Unsupported desktop sidecar target: %s\n' "$target" >&2
    exit 2
    ;;
esac

rm -rf "$work_dir"
mkdir -p "$work_dir" "$binary_dir"

PYTHONPATH="$root/src" pyinstaller \
  --noconfirm \
  --clean \
  --onefile \
  --name "$binary_name" \
  --paths "$root/src" \
  --collect-submodules vera_mmu \
  --distpath "$binary_dir" \
  --workpath "$work_dir/work" \
  --specpath "$work_dir/spec" \
  "$root/scripts/desktop_bridge_entry.py"

test -f "$binary_dir/$binary_name"
printf 'Built %s\n' "$binary_dir/$binary_name"

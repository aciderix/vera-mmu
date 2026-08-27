from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("vera_release_smoke", ROOT / "scripts" / "smoke_release_runtime.py")
assert SPEC is not None and SPEC.loader is not None
SMOKE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SMOKE
SPEC.loader.exec_module(SMOKE)


def test_safe_member_path_refuses_absolute_and_escape(tmp_path: Path) -> None:
    assert SMOKE._safe_member_path(tmp_path, "vmmu") == tmp_path / "vmmu"
    with pytest.raises(SMOKE.SmokeError):
        SMOKE._safe_member_path(tmp_path, "../vmmu")
    with pytest.raises(SMOKE.SmokeError):
        SMOKE._safe_member_path(tmp_path, "/tmp/vmmu")


def test_smoke_is_limited_to_linux_native_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(SMOKE.sys, "platform", "win32")
    with pytest.raises(SMOKE.SmokeError, match="Linux x64 natif"):
        SMOKE.smoke(SMOKE.LINUX_TARGET)
    monkeypatch.setattr(SMOKE.sys, "platform", "linux")
    with pytest.raises(SMOKE.SmokeError, match="Linux x64 natif"):
        SMOKE.smoke("x86_64-pc-windows-msvc")

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest

from vera_mmu.mcp_server import _decollapse_mapping
from vera_mmu.session_lifecycle import (
    barrier_disabled,
    mcp_channel_alive,
    wait_for_mcp_ready,
    tool_allowed_during_guard,
    touch_mcp_ready,
)


class ReliabilityHardeningTests(unittest.TestCase):
    def test_mcp_liveness_marker_is_atomic_and_bounded(self) -> None:
        with TemporaryDirectory() as directory:
            runtime = Path(directory)
            touch_mcp_ready(runtime)
            self.assertTrue(mcp_channel_alive(runtime))
            self.assertFalse(mcp_channel_alive(runtime, now=runtime.joinpath("mcp_ready").stat().st_mtime + 91.0))
            self.assertFalse((runtime / "mcp_ready.tmp").exists())

    def test_mcp_startup_readiness_waits_for_marker_but_timeout_is_bounded(self) -> None:
        with TemporaryDirectory() as directory:
            runtime = Path(directory)
            self.assertFalse(wait_for_mcp_ready(runtime, timeout_s=0))
            touch_mcp_ready(runtime)
            self.assertTrue(wait_for_mcp_ready(runtime, timeout_s=0))

    def test_runtime_kill_switch_is_available_during_session(self) -> None:
        with TemporaryDirectory() as directory:
            runtime = Path(directory)
            self.assertFalse(barrier_disabled(runtime))
            (runtime / "BARRIER_OFF").write_text("operator\n", encoding="utf-8")
            self.assertTrue(barrier_disabled(runtime))
            (runtime / "BARRIER_OFF").unlink()
            previous = os.environ.get("VERA_MMU_BARRIER_OFF")
            previous_aret = os.environ.get("ARET_MMU_BARRIER_OFF")
            try:
                os.environ["VERA_MMU_BARRIER_OFF"] = "1"
                self.assertTrue(barrier_disabled(runtime))
                os.environ.pop("VERA_MMU_BARRIER_OFF", None)
                os.environ["ARET_MMU_BARRIER_OFF"] = "1"
                self.assertTrue(barrier_disabled(runtime))
            finally:
                if previous is None:
                    os.environ.pop("VERA_MMU_BARRIER_OFF", None)
                else:
                    os.environ["VERA_MMU_BARRIER_OFF"] = previous
                if previous_aret is None:
                    os.environ.pop("ARET_MMU_BARRIER_OFF", None)
                else:
                    os.environ["ARET_MMU_BARRIER_OFF"] = previous_aret

    def test_diagnostic_allowlist_and_arbitrary_action_boundary(self) -> None:
        self.assertTrue(tool_allowed_during_guard("ToolSearch"))
        self.assertTrue(tool_allowed_during_guard("Read"))
        self.assertTrue(tool_allowed_during_guard("mcp__vera__mmu_acknowledge_resume"))
        self.assertFalse(tool_allowed_during_guard("Bash"))
        self.assertFalse(tool_allowed_during_guard("mmu_run_capability"))

    def test_parameter_collapse_is_reconstructed_before_validation(self) -> None:
        collapsed = {
            "working-rules": "r" * 80 + '</parameter><parameter name="current-state">' + "s" * 60,
        }
        repaired = _decollapse_mapping(collapsed)
        self.assertEqual(repaired["working-rules"], "r" * 80)
        self.assertEqual(repaired["current-state"], "s" * 60)


if __name__ == "__main__":
    unittest.main()

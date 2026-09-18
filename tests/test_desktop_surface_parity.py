"""Pin that the four layers of the desktop surface actually reach one another.

The Core, the stdio bridge, the Rust parent and the React console are four separate layers, and
until this suite existed nothing checked that a rung was not missing. It was: five bridge
operations — `taxonomy.preview`, `taxonomy.apply`, `work.graph.read`, `work.graph.preview` and
`work.graph.apply` — were declared, tested and reachable by nothing, because B4 and B5 shipped the
Core and the bridge and never wired the native parent. Steps 5 to 8 of the eighteen-step journey
were therefore displayed by the console, executable by the Core, and impossible from the Dashboard.

Nothing about that was visible: every layer's own tests passed. It took reading the four files side
by side to see it, which is exactly the kind of check that should not depend on someone thinking to
look. Each rule below closes one direction of the chain, so the next missing rung fails a test
instead of waiting to be noticed.

The parsers are deliberately strict about what they accept, and each is checked against a known
member and a plausible size: a regex that quietly matched nothing would make every rule below pass
for the wrong reason, which is the failure mode these rules exist to prevent.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "src" / "vera_mmu" / "desktop_bridge.py"
PARENT = ROOT / "apps" / "desktop" / "src-tauri" / "src" / "main.rs"
CONSOLE_API = ROOT / "apps" / "desktop" / "ui" / "src" / "desktop-api.ts"

#: Commands the parent serves itself, with no bridge operation behind them.
NATIVE_ONLY = frozenset({"select_project"})


def _bridge_operations() -> set[str]:
    """The operations the Python bridge declares in its handler table."""
    return set(re.findall(r'^\s+"([a-z][a-z.\-]*)": self\._\w+,$', BRIDGE.read_text(encoding="utf-8"), re.M))


def _parent_calls() -> set[str]:
    """The bridge operations the Rust parent actually calls, one-line or wrapped."""
    return set(re.findall(r'bridge\.call\(\s*"([a-z][a-z.\-]*)"', PARENT.read_text(encoding="utf-8")))


def _parent_commands() -> set[str]:
    """The functions the Rust parent exposes with `#[tauri::command]`.

    Further attributes may sit between the marker and the signature — `capability_preview` carries
    an `#[allow]` for its fifteen contract fields — so they are skipped rather than assumed absent.
    """
    return set(
        re.findall(
            r'#\[tauri::command\]\s*\n(?:\s*#\[[^\]]*\]\s*\n)*(?:pub )?(?:async )?fn\s+(\w+)',
            PARENT.read_text(encoding="utf-8"),
        )
    )


def _parent_registered() -> set[str]:
    """The commands the parent actually registers in its invoke handler."""
    block = re.search(r'generate_handler!\[([^\]]+)\]', PARENT.read_text(encoding="utf-8"))
    assert block is not None, "invoke_handler introuvable dans main.rs"
    return {name.strip() for name in block.group(1).replace("\n", " ").split(",") if name.strip()}


def _console_invocations() -> set[str]:
    """The Rust commands `desktopApi` invokes."""
    return set(re.findall(r'invoke<[^>]*>\(\s*"(\w+)"', CONSOLE_API.read_text(encoding="utf-8")))


class DesktopSurfaceParityTests(unittest.TestCase):
    def test_the_parsers_read_what_they_claim_to_read(self) -> None:
        """A regex matching nothing would make every rule below pass for the wrong reason."""
        for label, names, known in (
            ("opérations du bridge", _bridge_operations(), "wizard.state"),
            ("appels du parent", _parent_calls(), "wizard.state"),
            ("commandes Rust", _parent_commands(), "wizard_state"),
            ("commandes enregistrées", _parent_registered(), "wizard_state"),
            ("invocations de la console", _console_invocations(), "wizard_state"),
        ):
            self.assertIn(known, names, label)
            self.assertGreater(len(names), 30, label)

    def test_every_bridge_operation_is_reachable_from_the_native_parent(self) -> None:
        """The rung that was missing: a Core capability the Dashboard could not ask for."""
        unreachable = sorted(_bridge_operations() - _parent_calls())
        self.assertEqual(unreachable, [], f"Opérations du bridge qu’aucune commande Rust n’appelle : {unreachable}")

    def test_every_parent_call_names_a_declared_bridge_operation(self) -> None:
        unknown = sorted(_parent_calls() - _bridge_operations())
        self.assertEqual(unknown, [], f"Appels Rust vers une opération que le bridge ne déclare pas : {unknown}")

    def test_every_declared_command_is_registered_and_every_registration_is_declared(self) -> None:
        self.assertEqual(sorted(_parent_commands() - _parent_registered()), [])
        self.assertEqual(sorted(_parent_registered() - _parent_commands()), [])

    def test_every_registered_command_is_exposed_to_the_console_and_no_other(self) -> None:
        """`desktop-api.ts` is the console's only door; an unlisted command is a dead command."""
        self.assertEqual(sorted(_parent_registered() - _console_invocations() - NATIVE_ONLY), [])
        self.assertEqual(sorted(_console_invocations() - _parent_registered()), [])

    def test_the_journey_s_editing_steps_all_have_a_command(self) -> None:
        """Steps 5 to 13 each need a way in, or the journey displays work nobody can do."""
        registered = _parent_registered()
        for step, command in (
            ("edit-taxonomy / define-entities / define-relations", "taxonomy_preview"),
            ("configure-work-graph", "work_graph_preview"),
            ("declare-capabilities", "capability_preview"),
            ("build-gates", "gate_structure_preview"),
            ("define-policies", "policy_preview"),
            ("configure-resume / choose-integrations", "resume_preview"),
        ):
            self.assertIn(command, registered, step)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from vera_mmu.__main__ import main


PROFILE = """\
mmu:
  version: "2.0"
project:
  id: "cli-project"
  name: "CLI Project"
  domain: "generic"
workspace:
  root: "."
storage:
  memory_dir: ".vera-mmu"
  sqlite_file: "memory.sqlite"
  artifacts_dir: "artifacts"
"""


class CliTests(unittest.TestCase):
    """I001/I011/I014: the public initialization command only opens a profile-bound store."""

    def test_init_creates_and_reopens_the_profile_bound_store(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory) / ".vera-mmu"
            runtime.mkdir()
            profile_path = runtime / "project.yaml"
            profile_path.write_text(PROFILE, encoding="utf-8")
            output = StringIO()
            with redirect_stdout(output):
                first_status = main(["init", str(profile_path)])
            first = json.loads(output.getvalue())
            self.assertEqual(first_status, 0)
            self.assertTrue(first["ok"])
            self.assertEqual(first["metadata"]["store_format"], {"schema_version": 24})

            output = StringIO()
            with redirect_stdout(output):
                second_status = main(["init", str(profile_path)])
            second = json.loads(output.getvalue())
            self.assertEqual(second_status, 0)
            self.assertEqual(second["metadata"], first["metadata"])


if __name__ == "__main__":
    unittest.main()

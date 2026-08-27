from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.entities import EntityCreateInput, EntityService
from vera_mmu.identity import load_profile
from vera_mmu.relations import RelationService
from vera_mmu.store import MemoryStore


PROFILE = '''
mmu:
  version: "2.0"
project:
  id: "m11k-graph"
  name: "M11-K Graph"
  domain: "research"
workspace:
  root: "."
storage:
  memory_dir: ".vera-mmu"
  sqlite_file: "memory.sqlite"
  artifacts_dir: "artifacts"
identity:
  include_vcs_revision: false
  include_profile_hash: true
'''


class RelatedTraversalTests(unittest.TestCase):
    def _store(self, root: Path) -> MemoryStore:
        runtime = root / ".vera-mmu"; runtime.mkdir()
        profile = runtime / "project.yaml"; profile.write_text(PROFILE, encoding="utf-8")
        return MemoryStore.open(load_profile(profile), profile)

    def test_i001_i002_i009_i011_bounded_bfs_is_deterministic_cycle_safe_and_non_mutating(self) -> None:
        from vera_mmu.read_api import ReadApiError, ReadService

        with TemporaryDirectory() as directory:
            with self._store(Path(directory)) as store:
                entities = EntityService(store)
                entities.register_type_and_create_batch("node", "Node", [
                    EntityCreateInput("a", "A"), EntityCreateInput("b", "B"), EntityCreateInput("c", "C"), EntityCreateInput("d", "D"),
                ])
                relations = RelationService(store)
                relations.register_type("links", "Links", from_types=["node"], to_types=["node"])
                relations.create("ab", "links", "a", "b")
                relations.create("bc", "links", "b", "c")
                relations.create("ca", "links", "c", "a")
                relations.create("bd", "links", "b", "d")
                audits = store.audit_events()
                graph = ReadService(store).related("vera://m11k-graph/entity/a", direction="OUTBOUND", max_depth=2, max_nodes=3)
                self.assertEqual(graph["root_address"], "vera://m11k-graph/entity/a")
                self.assertEqual([item["address"] for item in graph["nodes"]], ["vera://m11k-graph/entity/b", "vera://m11k-graph/entity/c", "vera://m11k-graph/entity/d"])
                self.assertEqual([edge["id"] for edge in graph["relations"]], ["ab", "bc", "bd"])
                bounded = ReadService(store).related("vera://m11k-graph/entity/a", direction="OUTBOUND", max_depth=2, max_nodes=1)
                self.assertEqual([item["id"] for item in bounded["nodes"]], ["b"])
                self.assertEqual([edge["id"] for edge in bounded["relations"]], ["ab"])
                returned_ids = {"a", *(item["id"] for item in bounded["nodes"])}
                self.assertTrue(all(
                    edge["from_address"].rsplit("/", 1)[-1] in returned_ids
                    and edge["to_address"].rsplit("/", 1)[-1] in returned_ids
                    for edge in bounded["relations"]
                ))
                self.assertEqual(store.audit_events(), audits)
                with self.assertRaises(ReadApiError): ReadService(store).related("vera://m11k-graph/entity/a", direction="OUTBOUND", max_depth=4, max_nodes=3)
                with self.assertRaises(ReadApiError): ReadService(store).related("vera://other/entity/a", direction="OUTBOUND", max_depth=1, max_nodes=3)
                with self.assertRaises(ReadApiError): ReadService(store).related("vera://m11k-graph/knowledge/a", direction="OUTBOUND", max_depth=1, max_nodes=3)


if __name__ == "__main__": unittest.main()

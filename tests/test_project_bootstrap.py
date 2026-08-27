from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from vera_mmu.__main__ import main


def invoke(argv:list[str])->tuple[int,dict[str,object]]:
    output=StringIO()
    with redirect_stdout(output):code=main(argv)
    return code,json.loads(output.getvalue())

class ProjectBootstrapTests(unittest.TestCase):
    def test_i007_i011_builtin_agent_profiles_are_declarative_and_bounded(self)->None:
        from vera_mmu.agent_profiles import AgentProfileError,builtin_agent_profiles,validate_agent_profile
        profiles=builtin_agent_profiles();self.assertIn("claude-code-cloud",profiles);self.assertEqual(profiles["generic-mcp"].coverage,"MCP_ONLY")
        custom=validate_agent_profile({"id":"my-codex","label":"My Codex","adapter":"codex","mode":"local","coverage":"MCP_ONLY","events":[]})
        self.assertEqual(custom.id,"my-codex");self.assertEqual(custom.adapter,"codex")
        with self.assertRaises(AgentProfileError):validate_agent_profile({"id":"bad","label":"Bad","adapter":"codex","mode":"local","coverage":"TURN_GUARD_HARD","events":["SessionStart"]})
        with self.assertRaises(AgentProfileError):validate_agent_profile({"id":"evil","label":"Evil","adapter":"generic-mcp","mode":"local","coverage":"MCP_ONLY","events":[],"command":"anything"})
    def test_i007_i011_init_preview_is_deterministic_and_writes_nothing(self)->None:
        from vera_mmu.identity import load_profile
        from vera_mmu.project_bootstrap import preview_project_initialization
        with TemporaryDirectory() as directory:
            root=Path(directory);first=preview_project_initialization(root,template="software",project_id="my-app",project_name="My App");second=preview_project_initialization(root,template="software",project_id="my-app",project_name="My App")
            expected_paths=[".vera-mmu/agent-profiles.yaml",".vera-mmu/capabilities.yaml",".vera-mmu/gates.yaml",".vera-mmu/playbook.md",".vera-mmu/policies.yaml",".vera-mmu/project.yaml",".vera-mmu/sync-policy.json"]
            self.assertEqual(first,second);self.assertEqual(first.status,"PREVIEW");self.assertEqual([item.path for item in first.files],expected_paths);self.assertIn("domain: software",first.files[5].content);self.assertIn('"auto_push":true',first.files[6].content)
            self.assertFalse((root/".vera-mmu").exists())
            code,payload=invoke(["init-project",str(root),"--template","software","--project-id","my-app","--project-name","My App"]);self.assertEqual(code,0);self.assertEqual(payload["initialization"]["status"],"PREVIEW");self.assertFalse((root/".vera-mmu").exists())
            applied_root=Path(directory)/"applied";applied_root.mkdir();preview=preview_project_initialization(applied_root,template="software",project_id="my-app",project_name="My App")
            from vera_mmu.project_bootstrap import apply_project_initialization
            apply_project_initialization(applied_root,preview,confirm=True);profile=load_profile(applied_root/".vera-mmu"/"project.yaml")
            self.assertEqual(profile["capabilities"]["catalog"],".vera-mmu/capabilities.yaml");self.assertEqual(profile["gates"]["catalog"],".vera-mmu/gates.yaml");self.assertEqual(profile["policies"]["file"],".vera-mmu/policies.yaml")
            self.assertEqual(profile["resume"]["template"],"engineering");self.assertIn("RULE",profile["knowledge"]["types"])
    def test_i007_i011_profile_catalog_paths_and_taxonomy_are_project_bound(self)->None:
        from vera_mmu.identity import ProfileError,validate_profile
        profile={"mmu":{"version":"2.0"},"project":{"id":"my-app","name":"My App","domain":"software"},"workspace":{"root":"."},"storage":{"memory_dir":".vera-mmu","sqlite_file":"memory.sqlite","artifacts_dir":"artifacts"},"capabilities":{"catalog":".vera-mmu/capabilities.yaml"},"gates":{"catalog":".vera-mmu/gates.yaml"},"policies":{"file":".vera-mmu/policies.yaml"},"knowledge":{"types":["RULE","DECISION"]},"entities":{"types":["COMPONENT"]},"relations":{"types":["IMPLEMENTS"]},"resume":{"template":"engineering","sections":["rules","current_state"]},"work":{"enabled":True},"integrations":{"agent_profiles":".vera-mmu/agent-profiles.yaml"}}
        normalized=validate_profile(profile);self.assertEqual(normalized["knowledge"]["types"],["RULE","DECISION"]);self.assertEqual(normalized["integrations"]["agent_profiles"],".vera-mmu/agent-profiles.yaml")
        profile["capabilities"]={"catalog":"../capabilities.yaml"}
        with self.assertRaises(ProfileError):validate_profile(profile)
        profile["capabilities"]={"catalog":".vera-mmu/capabilities.yaml"};profile["knowledge"]={"types":["RULE","RULE"]}
        with self.assertRaises(ProfileError):validate_profile(profile)
    def test_i007_i011_init_apply_is_confirmed_non_destructive_and_refuses_symlink(self)->None:
        from vera_mmu.project_bootstrap import ProjectBootstrapError,apply_project_initialization,preview_project_initialization
        with TemporaryDirectory() as directory:
            root=Path(directory);preview=preview_project_initialization(root,template="research",project_id="study-1",project_name="Study 1")
            with self.assertRaises(ProjectBootstrapError):apply_project_initialization(root,preview,confirm=False)
            applied=apply_project_initialization(root,preview,confirm=True);self.assertEqual(applied.status,"INITIALIZED");self.assertTrue((root/".vera-mmu"/"project.yaml").is_file())
            self.assertEqual(apply_project_initialization(root,preview,confirm=True).status,"UNCHANGED")
            altered=(root/".vera-mmu"/"playbook.md");altered.write_text("other",encoding="utf-8")
            with self.assertRaises(ProjectBootstrapError):apply_project_initialization(root,preview,confirm=True)
        with TemporaryDirectory() as directory:
            target=Path(directory)/"target";target.mkdir();root=Path(directory)/"root";root.symlink_to(target,target_is_directory=True)
            with self.assertRaises(ProjectBootstrapError):preview_project_initialization(root,template="data",project_id="data-1",project_name="Data 1")

if __name__=="__main__":unittest.main()

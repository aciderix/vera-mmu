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
            self.assertEqual(profile["capabilities"]["catalog"],".vera-mmu/capabilities.yaml");self.assertEqual(profile["gates"]["catalog"],".vera-mmu/gates.yaml");self.assertEqual(profile["policies"]["file"],".vera-mmu/policies.yaml");self.assertEqual(profile["integrations"]["enabled"],[])
            self.assertEqual(profile["resume"]["template"],"engineering");self.assertIn("RULE",profile["knowledge"]["types"]);self.assertIn("active_goal",profile["front"]["fields"]);self.assertTrue(profile["project"]["description"])
    def test_i007_i011_profile_catalog_paths_and_taxonomy_are_project_bound(self)->None:
        from vera_mmu.identity import ProfileError,validate_profile
        profile={"mmu":{"version":"2.0"},"project":{"id":"my-app","name":"My App","domain":"software"},"workspace":{"root":"."},"storage":{"memory_dir":".vera-mmu","sqlite_file":"memory.sqlite","artifacts_dir":"artifacts"},"capabilities":{"catalog":".vera-mmu/capabilities.yaml"},"gates":{"catalog":".vera-mmu/gates.yaml"},"policies":{"file":".vera-mmu/policies.yaml"},"knowledge":{"types":["RULE","DECISION"]},"entities":{"types":["COMPONENT"]},"relations":{"types":["IMPLEMENTS"]},"resume":{"template":"engineering","sections":["rules","current_state"]},"work":{"enabled":True},"integrations":{"agent_profiles":".vera-mmu/agent-profiles.yaml"}}
        profile["integrations"]["enabled"]=["generic-mcp"]
        normalized=validate_profile(profile);self.assertEqual(normalized["knowledge"]["types"],["RULE","DECISION"]);self.assertEqual(normalized["integrations"]["agent_profiles"],".vera-mmu/agent-profiles.yaml");self.assertEqual(normalized["integrations"]["enabled"],["generic-mcp"]);self.assertIn("active_goal",normalized["front"]["fields"])
        profile["capabilities"]={"catalog":"../capabilities.yaml"}
        with self.assertRaises(ProfileError):validate_profile(profile)
        profile["capabilities"]={"catalog":".vera-mmu/capabilities.yaml"};profile["knowledge"]={"types":["RULE","RULE"]}
        with self.assertRaises(ProfileError):validate_profile(profile)
        profile["knowledge"]={"types":["RULE"]};profile["front"]={"fields":["active_goal","active_goal"]}
        with self.assertRaises(ProfileError):validate_profile(profile)
        profile["front"]={"fields":["active_goal"]};profile["integrations"]={"agent_profiles":".vera-mmu/agent-profiles.yaml","enabled":["generic-mcp","generic-mcp"]}
        with self.assertRaises(ProfileError):validate_profile(profile)
    def test_i007_i011_project_catalogs_are_hashed_validated_and_confined(self)->None:
        from vera_mmu.project_bootstrap import apply_project_initialization,preview_project_initialization
        from vera_mmu.project_catalogs import ProjectCatalogError,load_project_catalogs
        with TemporaryDirectory() as directory:
            root=Path(directory);preview=preview_project_initialization(root,template="data",project_id="data-app",project_name="Data App");apply_project_initialization(root,preview,confirm=True)
            catalogs=load_project_catalogs(root/".vera-mmu"/"project.yaml")
            self.assertEqual(catalogs.capabilities["format"],"vera-capability-catalog/v1");self.assertEqual(catalogs.gates["format"],"vera-gate-catalog/v1");self.assertEqual(catalogs.policies["format"],"vera-policy-catalog/v1")
            self.assertTrue(catalogs.capability_catalog_hash);self.assertTrue(catalogs.gate_catalog_hash);self.assertTrue(catalogs.policy_hash)
            (root/".vera-mmu"/"capabilities.yaml").write_text("format: invalid\ncapabilities: []\n",encoding="utf-8")
            with self.assertRaises(ProjectCatalogError):load_project_catalogs(root/".vera-mmu"/"project.yaml")
            (root/".vera-mmu"/"capabilities.yaml").write_text("format: vera-capability-catalog/v1\ncapabilities: []\ncapabilities: []\n",encoding="utf-8")
            with self.assertRaises(ProjectCatalogError):load_project_catalogs(root/".vera-mmu"/"project.yaml")
            (root/".vera-mmu"/"capabilities.yaml").unlink();(root/".vera-mmu"/"capabilities.yaml").symlink_to(root/".vera-mmu"/"gates.yaml")
            with self.assertRaises(ProjectCatalogError):load_project_catalogs(root/".vera-mmu"/"project.yaml")
    def test_i007_i008_project_catalog_declarations_are_closed_and_linked(self)->None:
        from vera_mmu.project_bootstrap import apply_project_initialization,preview_project_initialization
        from vera_mmu.project_catalogs import ProjectCatalogError,load_project_catalogs
        capability={"id":"unit-tests","name":"Unit tests","description":"Verify unit tests","kind":"CHECK","version":"1.0.0","runner":"OBSERVED_PROCESS","network_policy":"DENY_NETWORK","timeout_seconds":180,"parameter_schema":{"type":"object","additionalProperties":False},"yields_proof":True,"policy":"READ_ONLY","inputs":[],"outputs":[],"validator":"EVIDENCE_HASH","artifacts":[],"confirmation_required":False}
        gate={"id":"UNIT_TESTS_OK","name":"Unit tests pass","capability_id":"unit-tests","required":True,"expected":{"verdict":"PASS"}}
        with TemporaryDirectory() as directory:
            root=Path(directory);preview=preview_project_initialization(root,template="software",project_id="catalog-app",project_name="Catalog App");apply_project_initialization(root,preview,confirm=True)
            (root/".vera-mmu"/"capabilities.yaml").write_text(json.dumps({"format":"vera-capability-catalog/v1","capabilities":[capability]})+"\n",encoding="utf-8")
            (root/".vera-mmu"/"gates.yaml").write_text(json.dumps({"format":"vera-gate-catalog/v1","gates":[gate]})+"\n",encoding="utf-8")
            catalogs=load_project_catalogs(root/".vera-mmu"/"project.yaml");self.assertEqual(catalogs.gates["gates"][0]["capability_id"],"unit-tests")
            capability["command"]=["sh","-c","whoami"]
            (root/".vera-mmu"/"capabilities.yaml").write_text(json.dumps({"format":"vera-capability-catalog/v1","capabilities":[capability]})+"\n",encoding="utf-8")
            with self.assertRaises(ProjectCatalogError):load_project_catalogs(root/".vera-mmu"/"project.yaml")
    def test_i004_domain_templates_emit_distinct_declarative_entity_taxonomies(self)->None:
        from vera_mmu.identity import load_profile
        from vera_mmu.project_bootstrap import apply_project_initialization,preview_project_initialization
        expected={"software":{"COMPONENT","MODULE","SYMBOL","TEST","BUILD","DEPLOY"},"game":{"ASSET","SCENE","SERVER","EVENT","PLAYER_STATE","SYSTEM_STATE"},"research":{"EXPERIMENT","HYPOTHESIS","DATASET","RESULT","METRIC"},"data":{"DATASET","FEATURE","MODEL","EVALUATION","METRIC","PIPELINE"},"hardware":{"BOARD","COMPONENT","FIRMWARE","MEASUREMENT","DEVICE"},"documentation":{"SOURCE","DOCUMENT","CLAIM","CITATION","REVISION"}}
        with TemporaryDirectory() as directory:
            root=Path(directory)
            for index,(template,entity_types) in enumerate(expected.items()):
                project=root/template;project.mkdir();preview=preview_project_initialization(project,template=template,project_id=f"domain-{index}",project_name=template.title());apply_project_initialization(project,preview,confirm=True)
                self.assertEqual(set(load_profile(project/".vera-mmu"/"project.yaml")["entities"]["types"]),entity_types)
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

"""Verify the materialized checkout contract without contacts or model calls."""
import importlib.util
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("local_runtime",ROOT/"scripts/local_runtime.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class LocalRuntime(unittest.TestCase):
    def test_materialization_preserves_host_and_points_at_actual_local_files(self):
        data=mod.runtime_data()
        self.assertNotIn("providers",data);self.assertNotIn("session",data)
        skills=next(x for x in data["tools"] if x["module"]=="tool-skills")["config"]["skills"]
        self.assertEqual(skills,[str(ROOT/"skills")])
        entries=list((Path(skills[0])).glob("*/SKILL.md"))
        self.assertEqual(len(entries),1)
        self.assertEqual(entries[0].parent.name,'good-teammate')
        for path in data["context"]["include"]:self.assertTrue(Path(path).is_file())
        for tool in data["tools"]:
            if tool["module"]!="tool-skills":self.assertTrue(Path(tool["source"]).is_dir())
    def test_refuses_output_in_public_tree(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/"runtime.json"
            result=subprocess.run([sys.executable,str(ROOT/"scripts/local_runtime.py"),"--output",str(output)],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0);self.assertFalse(output.exists())
if __name__=="__main__":unittest.main()

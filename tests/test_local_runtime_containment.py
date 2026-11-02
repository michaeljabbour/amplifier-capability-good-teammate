"""Machine-local generated behavior must remain in the checkout's ignored tree."""
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("runtime_containment", ROOT / "scripts/local_runtime.py")
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


class RuntimeContainmentTests(unittest.TestCase):
    def invoke(self, root, output, *extra):
        with patch.object(runtime, "ROOT", root), patch.object(runtime, "runtime_data", return_value={"bundle": {"name": "fictional-local"}}), patch.object(sys, "argv", ["local_runtime.py", "--output", str(output), *extra]), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            runtime.main()

    def test_symlinked_ignored_root_cannot_redirect_machine_paths_outside(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "checkout"
            outside = Path(directory) / "outside"
            root.mkdir(); outside.mkdir()
            (root / ".capability-check").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(SystemExit) as stopped:
                self.invoke(root, root / ".capability-check/behavior.yaml")
            self.assertEqual(stopped.exception.code, 2)
            self.assertEqual(list(outside.iterdir()), [])

    def test_nested_symlink_cannot_escape_the_ignored_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "checkout"
            local = root / ".capability-check"
            outside = Path(directory) / "outside"
            local.mkdir(parents=True); outside.mkdir()
            (local / "link").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(SystemExit):
                self.invoke(root, local / "link/behavior.yaml")
            self.assertEqual(list(outside.iterdir()), [])

    def test_fresh_regular_ignored_directory_is_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "checkout"
            root.mkdir()
            output = root / ".capability-check/behavior.yaml"
            self.invoke(root, output)
            self.assertIn("fictional-local", output.read_text())

    def test_existing_different_output_needs_explicit_replace(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "checkout"
            output = root / ".capability-check/behavior.yaml"
            output.parent.mkdir(parents=True)
            output.write_text("preserve fictional previous behavior")
            with self.assertRaises(SystemExit):
                self.invoke(root, output)
            self.assertEqual(output.read_text(), "preserve fictional previous behavior")


if __name__ == "__main__":
    unittest.main()

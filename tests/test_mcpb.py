"""Verify Desktop bundle boundaries, metadata consistency, and read-only checks."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from zipfile import ZipFile


SOURCE = Path(__file__).resolve().parents[1]


class McpbTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for name in ("scripts", "plugin-source", "mcpb"):
            shutil.copytree(SOURCE / name, self.root / name)
        shutil.copyfile(SOURCE / "LICENSE", self.root / "LICENSE")

    def build(self, *args):
        return subprocess.run(
            [sys.executable, str(self.root / "scripts/build_mcpb.py"), *args],
            capture_output=True, text=True,
        )

    def test_bundle_excludes_local_files_and_preserves_license_and_server_pin(self):
        (self.root / "mcpb/.env").write_text("DUMMY=true\n")
        (self.root / "mcpb/.venv").mkdir()
        (self.root / "mcpb/.venv/local.py").write_text("# Local fixture\n")
        metadata = json.loads((self.root / "plugin-source/metadata.json").read_text())
        metadata["desktop"]["version"] = "0.2.0"
        metadata["mcp"]["version"] = "0.4.4"
        (self.root / "plugin-source/metadata.json").write_text(json.dumps(metadata))
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        with ZipFile(self.root / "dist/lumoz.mcpb") as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(set(archive.namelist()), {
                "manifest.json", "pyproject.toml", "server.py", "LICENSE",
            })
            self.assertEqual(archive.read("LICENSE"), (SOURCE / "LICENSE").read_bytes())
            manifest = json.loads(archive.read("manifest.json"))
            project = tomllib.loads(archive.read("pyproject.toml").decode())
            self.assertEqual(manifest["version"], "0.2.0")
            self.assertEqual(project["project"]["version"], "0.2.0")
            self.assertEqual(project["project"]["dependencies"], ["lumoz-mcp==0.4.4"])
            self.assertIn(manifest["server"]["entry_point"], archive.namelist())

    def test_plugin_release_does_not_change_desktop_metadata(self):
        before = {name: (self.root / "mcpb" / name).read_bytes() for name in ("manifest.json", "pyproject.toml")}
        path = self.root / "plugin-source/metadata.json"
        metadata = json.loads(path.read_text())
        metadata["plugins"]["skills"]["version"] = "0.2.0"
        metadata["plugins"]["mcp"]["version"] = "0.3.0"
        path.write_text(json.dumps(metadata))
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        for name, data in before.items():
            self.assertEqual((self.root / "mcpb" / name).read_bytes(), data)

    def test_check_detects_stale_metadata_without_writing(self):
        manifest = self.root / "mcpb/manifest.json"
        manifest.write_text("{}\n")
        result = self.build("--check")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Outdated MCPB metadata", result.stderr)
        self.assertEqual(manifest.read_text(), "{}\n")
        self.assertFalse((self.root / "dist").exists())

    def test_license_is_required(self):
        (self.root / "LICENSE").unlink()
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Required package input missing: LICENSE", result.stderr)
        self.assertFalse((self.root / "dist").exists())

    @unittest.skipIf(sys.platform == "win32", "Symlinks require extra privileges on Windows")
    def test_symlink_launcher_is_rejected(self):
        launcher = self.root / "mcpb/server.py"
        launcher.unlink()
        launcher.symlink_to(SOURCE / "mcpb/server.py")
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symlink", result.stderr)
        self.assertFalse((self.root / "dist").exists())


if __name__ == "__main__":
    unittest.main()

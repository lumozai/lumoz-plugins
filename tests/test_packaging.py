"""Check that public bundles reject accidental local credentials and symlinks."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile


SOURCE = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "plugin"
        self.root.mkdir()
        for name in ("scripts", "plugin-source", "plugins"):
            shutil.copytree(SOURCE / name, self.root / name)
        shutil.copyfile(SOURCE / "LICENSE", self.root / "LICENSE")
        self.skills = self.root / "plugins/lumoz-skills"
        self.mcp = self.root / "plugins/lumoz-mcp"

    def build(self, *args):
        return subprocess.run(
            [sys.executable, str(self.root / "scripts/build_claude.py"), *args],
            capture_output=True, text=True,
        )

    def test_bundle_contains_only_runtime_files_and_license(self):
        (self.root / "LICENSE").write_text("Test license fixture\n")
        result = self.build("--zip")
        self.assertEqual(result.returncode, 0, result.stderr)
        with ZipFile(self.root / "dist/lumoz-skills-0.1.0.zip") as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(set(archive.namelist()), {
                ".claude-plugin/plugin.json",
                "README.md",
                "skills/lumoz-evals/SKILL.md",
                "LICENSE",
            })
            manifest = json.loads(archive.read(".claude-plugin/plugin.json"))
            self.assertNotIn("mcpServers", manifest)
            self.assertNotIn("userConfig", manifest)
            self.assertNotIn("dependencies", manifest)
            self.assertEqual(archive.read("LICENSE"), b"Test license fixture\n")
        with ZipFile(self.root / "dist/lumoz-mcp-0.1.0.zip") as archive:
            self.assertEqual(set(archive.namelist()), {
                ".claude-plugin/plugin.json", ".mcp.json", "README.md", "LICENSE",
            })
            manifest = json.loads(archive.read(".claude-plugin/plugin.json"))
            self.assertTrue(manifest["userConfig"]["api_key"]["sensitive"])
            self.assertEqual(archive.read("LICENSE"), b"Test license fixture\n")

    def test_credential_file_is_rejected(self):
        (self.skills / "skills/lumoz-evals/.env.production").write_text("DUMMY=true\n")
        result = self.build("--zip")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("credential file cannot be packaged", result.stderr)
        self.assertFalse((self.root / "dist").exists())

    @unittest.skipIf(sys.platform == "win32", "Symlinks require extra privileges on Windows")
    def test_symlink_outside_plugin_is_rejected(self):
        outside = Path(self.temporary.name) / "outside.md"
        outside.write_text("Private local fixture\n")
        (self.skills / "skills/lumoz-evals/external.md").symlink_to(outside)
        result = self.build("--zip")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symlink", result.stderr)
        self.assertFalse((self.root / "dist").exists())

    def test_check_cannot_build_or_write(self):
        result = self.build("--check", "--zip")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "dist").exists())
        self.assertFalse((self.root / ".mcp.json").exists())

    def test_server_update_does_not_change_skills_plugin(self):
        self.assertEqual(self.build().returncode, 0)
        before = {p.relative_to(self.skills): p.read_bytes() for p in self.skills.rglob("*") if p.is_file()}
        path = self.root / "plugin-source/metadata.json"
        metadata = json.loads(path.read_text())
        metadata["mcp"]["version"] = "0.4.4"
        metadata["plugins"]["mcp"]["version"] = "0.1.1"
        path.write_text(json.dumps(metadata))
        result = self.build("--zip")
        self.assertEqual(result.returncode, 0, result.stderr)
        after = {p.relative_to(self.skills): p.read_bytes() for p in self.skills.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertTrue((self.root / "dist/lumoz-mcp-0.1.1.zip").is_file())
        config = json.loads((self.mcp / ".mcp.json").read_text())
        self.assertIn("lumoz-mcp==0.4.4", config["mcpServers"]["lumoz"]["args"])

    def test_skills_cannot_accidentally_gain_an_mcp_entry(self):
        (self.skills / ".mcp.json").write_text('{}\n')
        result = self.build("--zip")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unexpected combined-plugin component", result.stderr)
        self.assertFalse((self.root / "dist").exists())

    def test_check_detects_stale_license_without_writing(self):
        self.assertEqual(self.build().returncode, 0)
        (self.skills / "LICENSE").write_text("Stale license\n")
        result = self.build("--check")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.skills / "LICENSE").read_text(), "Stale license\n")


if __name__ == "__main__":
    unittest.main()

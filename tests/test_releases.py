"""Check that component tags cannot publish a different package or version."""

import importlib.util
import json
from pathlib import Path
import unittest


SOURCE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prepare_release", SOURCE / "scripts/prepare_release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.metadata = json.loads((SOURCE / "plugin-source/metadata.json").read_text())
        self.metadata["plugins"]["skills"]["version"] = "1.2.3"
        self.metadata["plugins"]["mcp"]["version"] = "2.3.4"
        self.metadata["desktop"]["version"] = "3.4.5"

    def test_each_tag_selects_its_own_artifact(self):
        cases = {
            "lumoz-skills-v1.2.3": "dist/lumoz-skills-1.2.3.zip",
            "lumoz-mcp-v2.3.4": "dist/lumoz-mcp-2.3.4.zip",
            "lumoz-desktop-v3.4.5": "dist/lumoz.mcpb",
        }
        for tag, asset in cases.items():
            with self.subTest(tag=tag):
                details = release.release_details(self.metadata, tag)
                self.assertEqual(details["asset"], asset)
                self.assertEqual(details["latest"], "true" if "desktop" in tag else "false")

    def test_wrong_component_version_cannot_be_published(self):
        with self.assertRaisesRegex(ValueError, "does not match"):
            release.release_details(self.metadata, "lumoz-mcp-v1.2.3")

    def test_unrelated_or_malformed_tag_cannot_publish(self):
        for tag in ("v1.2.3", "lumoz-other-v1.2.3", "lumoz-skills-v1.2.3/extra"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                release.release_details(self.metadata, tag)


if __name__ == "__main__":
    unittest.main()

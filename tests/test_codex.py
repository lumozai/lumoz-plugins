"""Check skills installation and private MCP configuration with real Codex."""

import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest


SOURCE = Path(__file__).resolve().parents[1]
CODEX = shutil.which("codex")


@unittest.skipUnless(CODEX, "Codex CLI is required for the plugin integration check")
class CodexTests(unittest.TestCase):
    def test_install_discovers_skill_and_preserves_manual_mcp_configuration(self):
        self.check_install()

    def test_existing_claude_format_installs_and_discovers_skill(self):
        self.check_install(legacy=True)

    def check_install(self, legacy=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marketplace = root / "marketplace"
            marketplace.mkdir()
            for name in ("scripts", "plugin-source", "plugins"):
                shutil.copytree(SOURCE / name, marketplace / name)
            shutil.copyfile(SOURCE / "LICENSE", marketplace / "LICENSE")
            generated = subprocess.run(
                [sys.executable, str(marketplace / "scripts/build_claude.py")],
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(generated.returncode, 0, generated.stderr)
            catalog = json.loads((marketplace / '.agents/plugins/marketplace.json').read_text())
            self.assertEqual([plugin['name'] for plugin in catalog['plugins']], ['lumoz-skills'])
            if legacy:
                (marketplace / '.agents/plugins/marketplace.json').unlink()
                (marketplace / 'plugins/lumoz-skills/plugin.json').unlink()
            home = root / "codex-home"
            home.mkdir()
            (home / "config.toml").write_text(
                '[features]\nplugins = true\nremote_plugin = false\n'
            )
            env = {**os.environ, "CODEX_HOME": str(home)}

            def codex(*args):
                result = subprocess.run(
                    [CODEX, *args, "--json"], env=env, cwd=root,
                    capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)

            added = codex("plugin", "marketplace", "add", str(marketplace))
            self.assertEqual(added["marketplaceName"], "lumoz")
            skills = codex("plugin", "add", "lumoz-skills@lumoz")
            skill_root = Path(skills["installedPath"])
            self.assertEqual(
                (skill_root / "skills/lumoz-evals/SKILL.md").read_bytes(),
                (SOURCE / "plugins/lumoz-skills/skills/lumoz-evals/SKILL.md").read_bytes(),
            )
            self.assertFalse((skill_root / "mcp.json").exists())
            self.assertEqual(codex("mcp", "list"), [])
            self.check_skill_discovery(root, env)

            config = home / "config.toml"
            with config.open("a") as stream:
                stream.write(
                    '\n[mcp_servers.lumoz]\ncommand = "uvx"\nargs = ["lumoz-mcp"]\n'
                    '[mcp_servers.lumoz.env]\nLUMOZ_API_KEY = "test-client:test-secret"\n'
                )
            before = config.read_bytes()
            codex("plugin", "add", "lumoz-skills@lumoz")
            self.assertEqual(config.read_bytes(), before)
            servers = codex("mcp", "list")
            self.assertEqual(len(servers), 1)
            server = servers[0]
            self.assertEqual(server["name"], "lumoz")
            self.assertTrue(server["enabled"])
            transport = server["transport"]
            self.assertEqual(transport["command"], "uvx")
            self.assertEqual(transport["args"], ["lumoz-mcp"])
            self.assertEqual(transport["env"]["LUMOZ_API_KEY"], "test-client:test-secret")
            codex("plugin", "remove", "lumoz-skills@lumoz")
            self.assertEqual(codex("mcp", "list"), servers)

    def check_skill_discovery(self, root, env):
        with tempfile.TemporaryFile(mode="w+") as stderr:
            process = subprocess.Popen(
                [CODEX, "app-server", "--listen", "stdio://"], env=env, cwd=root,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr,
                text=True,
            )
            messages = queue.Queue()

            def read_messages():
                for line in process.stdout:
                    messages.put(json.loads(line))

            reader = threading.Thread(target=read_messages, daemon=True)
            reader.start()

            def request(identifier, method, params):
                process.stdin.write(json.dumps({
                    "id": identifier, "method": method, "params": params,
                }) + "\n")
                process.stdin.flush()
                while True:
                    message = messages.get(timeout=20)
                    if message.get("id") == identifier:
                        self.assertNotIn("error", message, message)
                        return message["result"]

            try:
                request(1, "initialize", {
                    "clientInfo": {"name": "lumoz-packaging-test", "version": "1"},
                    "capabilities": {"experimentalApi": True},
                })
                process.stdin.write('{"method":"initialized"}\n')
                process.stdin.flush()
                result = request(2, "skills/list", {"cwds": [str(root)], "forceReload": True})
                skills = [skill for entry in result["data"] for skill in entry["skills"]
                          if skill.get("pluginId") == "lumoz-skills@lumoz"]
                self.assertEqual([skill["name"] for skill in skills], ["lumoz-skills:lumoz-evals"])
                self.assertTrue(skills[0]["enabled"])
                for entry in result["data"]:
                    self.assertEqual(entry["errors"], [])
            except (queue.Empty, AssertionError):
                stderr.seek(0)
                self.fail(f"Codex skill discovery failed. stderr: {stderr.read()}")
            finally:
                process.kill()
                process.wait(timeout=10)
                process.stdin.close()
                reader.join(timeout=5)
                process.stdout.close()


if __name__ == "__main__":
    unittest.main()

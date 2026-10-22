"""Installer failure handling and integration with isolated client profiles."""

from contextlib import redirect_stderr, redirect_stdout
import getpass
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "installer/src"))
from lumoz_setup import cli

KEY = "example-client:example-secret"


class Invocation:
    def invoke(self, target, action="install", key=KEY):
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output), patch.object(
            cli.getpass, "getpass", return_value=key,
        ):
            result = cli.main([target, action])
        if ":" in key and not any(c.isspace() for c in key):
            self.assertNotIn(key, output.getvalue())
        return result, output.getvalue()


class InstallerTests(Invocation, unittest.TestCase):
    def test_invalid_and_cancelled_keys_never_change_state(self):
        for key in ("", "client", ":secret", "client:", "client:two words"):
            with self.subTest(key=key), patch.object(cli.shutil, "which", return_value="example"), patch.object(
                cli.Client, "run",
            ) as run:
                self.assertEqual(self.invoke("codex", key=key)[0], 1)
                run.assert_called_once_with("plugin", "add", "--help")
        for error in (EOFError, KeyboardInterrupt, getpass.GetPassWarning):
            with self.subTest(error=error), patch.object(cli.shutil, "which", return_value="example"), patch.object(
                cli.Client, "run",
            ) as run, patch.object(cli.getpass, "getpass", side_effect=error), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(cli.main(["codex"]), 1)
                run.assert_called_once_with("plugin", "add", "--help")

    def test_missing_runtime_and_client_never_prompt(self):
        for executable in (None, "codex"):
            with patch.object(cli.shutil, "which", side_effect=[executable, None]), patch.object(
                cli.getpass, "getpass",
            ) as prompt, redirect_stderr(io.StringIO()):
                self.assertEqual(cli.main(["codex"]), 1)
                prompt.assert_not_called()

    def test_errors_and_timeouts_do_not_print_credentials(self):
        for failure in (
            subprocess.CompletedProcess([], 1, "", f"bad --env LUMOZ_API_KEY={KEY}"),
            subprocess.TimeoutExpired(["codex", KEY], 180),
        ):
            with patch.object(cli.shutil, "which", return_value="example"):
                client = cli.Client("codex")
            client.secret = KEY
            with patch.object(cli.subprocess, "run", side_effect=[failure] if isinstance(failure, Exception) else None, return_value=failure), redirect_stdout(io.StringIO()):
                with self.assertRaises(cli.SetupError) as caught:
                    client.run("mcp", "add", "lumoz", "--env", f"LUMOZ_API_KEY={KEY}")
                self.assertNotIn(KEY, str(caught.exception))

    def test_claude_key_is_passed_on_stdin_only(self):
        with patch.object(cli.shutil, "which", return_value="example"):
            client = cli.Client("claude-code")
        client.secret = KEY
        result = subprocess.CompletedProcess([], 0, 'Progress\n{"saved":["api_key"]}\n', '')
        with patch.object(cli.subprocess, "run", return_value=result) as run, redirect_stdout(io.StringIO()):
            self.assertEqual(client.run("plugin", "configure", "lumoz-mcp@lumoz", values={"api_key": KEY}, as_json=True), {"saved": ["api_key"]})
        self.assertNotIn(KEY, str(run.call_args.args))
        self.assertEqual(json.loads(run.call_args.kwargs["input"]), {"api_key": KEY})

    def test_marketplace_is_kept_for_other_plugins(self):
        with patch.object(cli.shutil, "which", return_value="example"):
            client = cli.Client("codex")
        with patch.object(client, "plugins", return_value=[{"pluginId": "other@lumoz"}]), patch.object(client, "run") as run, redirect_stdout(io.StringIO()):
            cli.uninstall(client)
        run.assert_called_once_with("mcp", "remove", "lumoz")

    def test_claude_project_installation_is_preserved(self):
        with patch.object(cli.shutil, "which", return_value="example"):
            client = cli.Client("claude-code")
        project = {"id": "lumoz-mcp@lumoz", "scope": "project"}
        with patch.object(client, "plugins", return_value=[project]), patch.object(client, "run") as run, redirect_stdout(io.StringIO()):
            cli.uninstall(client)
        run.assert_not_called()

    def test_old_claude_fails_before_key_prompt(self):
        result = subprocess.CompletedProcess([], 0, "Usage: claude plugin", "")
        with patch.object(cli.shutil, "which", return_value="example"), patch.object(cli.subprocess, "run", return_value=result), patch.object(cli.getpass, "getpass") as prompt, redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(["claude-code"]), 1)
        prompt.assert_not_called()

    def test_packaged_defaults_match_release_metadata(self):
        defaults = json.loads((ROOT / "installer/src/lumoz_setup/defaults.json").read_text())
        metadata = json.loads((ROOT / "plugin-source/metadata.json").read_text())
        self.assertEqual(defaults["server"], f"{metadata['mcp']['package']}=={metadata['mcp']['version']}")
        self.assertEqual((ROOT / "installer/LICENSE").read_text(), (ROOT / "LICENSE").read_text().rstrip("\n") + "\n")


class ClientIntegrationTests(Invocation, unittest.TestCase):
    def check_client(self, target):
        executable = shutil.which("codex" if target == "codex" else "claude")
        if not executable:
            self.skipTest(f"{target} CLI is required")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            uvx = str(root / "path with spaces" / "uvx")
            home = root / "profile"
            home.mkdir()
            if target == "codex":
                (home / "config.toml").write_text(
                    '[features]\nplugins=true\nremote_plugin=false\n'
                    '[mcp_servers.other]\ncommand="example-server"\n'
                    '[mcp_servers.other.env]\nOTHER_KEY="example-other-key"\n'
                )
            variable = "CODEX_HOME" if target == "codex" else "CLAUDE_CONFIG_DIR"
            original_run = cli.subprocess.run

            def run(command, **kwargs):
                # Use the real CLI and a local marketplace; no network/account needed.
                if command[1:4] == ["plugin", "marketplace", "add"]:
                    command = [*command[:4], str(ROOT), *command[5:]]
                return original_run(command, cwd=directory, **kwargs)

            def which(name):
                return executable if name in ("codex", "claude") else uvx

            with patch.dict(os.environ, {variable: str(home)}), patch.object(cli.shutil, "which", side_effect=which), patch.object(cli.subprocess, "run", side_effect=run):
                if target == "codex":
                    # A failure after skills installation must be recoverable by rerunning setup.
                    def interrupted(command, **kwargs):
                        if command[1:3] == ["mcp", "add"]:
                            return subprocess.CompletedProcess(command, 1, "", "Simulated write failure")
                        return run(command, **kwargs)
                    with patch.object(cli.subprocess, "run", side_effect=interrupted):
                        self.assertEqual(self.invoke(target)[0], 1)
                self.assertEqual(self.invoke(target)[0], 0)
                if target == "codex":
                    config = home / "config.toml"
                    config.write_text(config.read_text().replace("enabled = true", "enabled = false"))
                else:
                    original_run([executable, "plugin", "disable", "lumoz-skills@lumoz", "--scope", "user"], capture_output=True, text=True, cwd=directory, check=True)
                self.assertEqual(self.invoke(target, key="new-client:new-secret")[0], 0)
                listing = original_run([executable, "plugin", "list", "--json"], capture_output=True, text=True, cwd=directory, check=True)
                installed = json.loads(listing.stdout)
                self.assertTrue(all(p["enabled"] for p in (installed["installed"] if target == "codex" else installed)))
                if target == "codex":
                    settings = tomllib.loads((home / "config.toml").read_text())
                    self.assertEqual(settings["mcp_servers"]["lumoz"]["env"], {"LUMOZ_API_KEY": "new-client:new-secret"})
                    self.assertEqual(settings["mcp_servers"]["lumoz"]["command"], str(Path(uvx).resolve()))
                else:
                    result = original_run([executable, "plugin", "configure", "lumoz-mcp@lumoz", "--json"], capture_output=True, text=True, cwd=directory, check=True)
                    configuration = json.loads(result.stdout)
                    self.assertIn("api_key", configuration["configured"])
                    self.assertNotIn("new-client:new-secret", result.stdout)
                with patch.object(cli.getpass, "getpass") as prompt, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    self.assertEqual(cli.main([target, "uninstall"]), 0)
                    self.assertEqual(cli.main([target, "uninstall"]), 0)
                prompt.assert_not_called()
                listing = original_run([executable, "plugin", "list", "--json"], capture_output=True, text=True, cwd=directory, check=True)
                installed = json.loads(listing.stdout)
                self.assertEqual(installed["installed"] if target == "codex" else installed, [])
                if target == "codex":
                    settings = tomllib.loads((home / "config.toml").read_text())
                    self.assertNotIn("lumoz", settings["mcp_servers"])
                    self.assertEqual(settings["mcp_servers"]["other"]["env"], {"OTHER_KEY": "example-other-key"})
                else:
                    # Claude stores secrets separately from install records; uninstall must clear them.
                    for path in home.rglob("*"):
                        if path.is_file() and path.suffix == ".json":
                            self.assertNotIn("new-client:new-secret", path.read_text())

    def test_codex_install_repeat_and_uninstall(self):
        self.check_client("codex")

    def test_claude_install_repeat_and_uninstall(self):
        self.check_client("claude-code")


if __name__ == "__main__":
    unittest.main()

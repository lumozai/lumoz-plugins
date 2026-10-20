"""Exercise credential setup, failure handling, and removal with real Codex."""

from contextlib import redirect_stderr, redirect_stdout
import getpass
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from scripts import setup_codex


KEY = "example-client:example-secret"
CODEX = shutil.which("codex")


class SetupTests(unittest.TestCase):
    def invoke(self, arguments=(), key=KEY):
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output), patch.object(
            setup_codex.getpass, "getpass", return_value=key,
        ):
            result = setup_codex.main(arguments)
        self.assertNotIn(key, output.getvalue())
        return result, output.getvalue()

    def test_missing_runtime_does_not_prompt_or_write(self):
        with patch.object(setup_codex.shutil, "which", side_effect=["codex", None]), patch.object(
            setup_codex.getpass, "getpass",
        ) as prompt, patch.object(setup_codex.subprocess, "run") as run, redirect_stderr(io.StringIO()):
            self.assertEqual(setup_codex.main([]), 1)
        prompt.assert_not_called()
        run.assert_not_called()

    def test_invalid_key_does_not_write(self):
        with patch.object(setup_codex.shutil, "which", return_value="example"), patch.object(
            setup_codex.subprocess, "run",
        ) as run:
            for key in ("missing-separator", ":secret", "client:", "client:two words"):
                with self.subTest(key=key):
                    result, output = self.invoke(key=key)
                    self.assertEqual(result, 1)
                    self.assertIn("client_id:client_secret", output)
        run.assert_not_called()

    def test_codex_failure_redacts_key(self):
        failure = subprocess.CompletedProcess([], 1, "", f"failed --env LUMOZ_API_KEY={KEY}")
        with patch.object(setup_codex.shutil, "which", return_value="example"), patch.object(
            setup_codex.subprocess, "run", return_value=failure,
        ):
            result, output = self.invoke()
        self.assertEqual(result, 1)
        self.assertIn("[redacted]", output)

    def test_timeout_does_not_print_command_with_key(self):
        with patch.object(setup_codex.shutil, "which", return_value="example"), patch.object(
            setup_codex.subprocess, "run",
            side_effect=subprocess.TimeoutExpired(["codex", KEY], 30),
        ):
            result, output = self.invoke()
        self.assertEqual(result, 1)
        self.assertIn("30 seconds", output)

    def test_no_hidden_input_does_not_write(self):
        with patch.object(setup_codex.shutil, "which", return_value="example"), patch.object(
            setup_codex.getpass, "getpass", side_effect=getpass.GetPassWarning("No terminal"),
        ), patch.object(setup_codex.subprocess, "run") as run, redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
            self.assertEqual(setup_codex.main([]), 1)
        run.assert_not_called()

    @unittest.skipUnless(CODEX, "Codex CLI is required for the setup integration check")
    def test_install_replace_and_uninstall_preserve_unrelated_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.toml"
            unrelated = (
                '[mcp_servers.other]\ncommand = "example-server"\n'
                '[mcp_servers.other.env]\nOTHER_API_KEY = "example-other-key"\n'
            )
            config.write_text(
                unrelated + '\n[mcp_servers.lumoz]\ncommand = "old-server"\n'
                'args = ["--old-option"]\nenv_vars = ["OLD_LUMOZ_KEY"]\n'
                'startup_timeout_sec = 90\n'
                '[mcp_servers.lumoz.env]\nLUMOZ_API_KEY = "old-client:old-secret"\n'
            )
            metadata = json.loads((setup_codex.ROOT / "plugin-source/metadata.json").read_text())

            def executable(name):
                return CODEX if name == "codex" else "/example/path with spaces/uvx"

            with patch.dict(os.environ, {"CODEX_HOME": directory}), patch.object(
                setup_codex.shutil, "which", side_effect=executable,
            ):
                self.assertEqual(self.invoke()[0], 0)
                first = config.read_text()
                self.assertIn(KEY, first)
                self.assertNotIn("env_vars", first)
                self.assertNotIn("old-client:old-secret", first)
                self.assertNotIn("startup_timeout_sec", first)
                settings = subprocess.run(
                    [CODEX, "mcp", "get", "lumoz", "--json"],
                    capture_output=True, text=True, check=True, timeout=30,
                )
                transport = json.loads(settings.stdout)["transport"]
                self.assertEqual(transport["command"], "/example/path with spaces/uvx")
                self.assertEqual(transport["args"], [
                    "--from", f"{metadata['mcp']['package']}=={metadata['mcp']['version']}", "lumoz-mcp",
                ])
                self.assertEqual(transport["env"], {"LUMOZ_API_KEY": KEY})
                replacement = "replacement-client:replacement-secret"
                self.assertEqual(self.invoke(["install"], key=replacement)[0], 0)
                updated = config.read_text()
                self.assertNotIn(KEY, updated)
                self.assertIn(replacement, updated)
                self.assertEqual(updated.count("[mcp_servers.lumoz]"), 1)

                # Removal needs neither uvx, a key prompt, nor release metadata.
                with patch.object(setup_codex.getpass, "getpass") as prompt, patch.object(
                    setup_codex.shutil, "which", return_value=CODEX,
                ) as which, redirect_stdout(io.StringIO()):
                    self.assertEqual(setup_codex.main(["uninstall"]), 0)
                prompt.assert_not_called()
                which.assert_called_once_with("codex")
                after = config.read_text()
                self.assertNotIn("lumoz", after)
                self.assertNotIn(replacement, after)
                self.assertEqual(tomllib.loads(after), tomllib.loads(unrelated))


if __name__ == "__main__":
    unittest.main()

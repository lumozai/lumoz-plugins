"""Install or uninstall Lumoz skills and MCP tools using the client's CLI."""

import argparse
import getpass
from importlib.resources import files
import json
from pathlib import Path
import shutil
import subprocess
import sys
import warnings


class SetupError(Exception):
    pass


class Client:
    def __init__(self, target):
        self.codex = target == "codex"
        self.name = "codex" if self.codex else "claude"
        self.command = shutil.which(self.name)
        if not self.command:
            raise SetupError(f"{self.name} was not found. Install the client and add it to PATH first.")
        self.secret = None

    def run(self, *arguments, values=None, as_json=False):
        command = [self.command, *arguments]
        if as_json:
            command.append("--json")
        print(f"Running {self.name} {' '.join(arguments[:3])}…", flush=True)
        try:
            result = subprocess.run(
                command, input=json.dumps(values) if values is not None else None,
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180,
            )
        except subprocess.TimeoutExpired:
            raise SetupError("The client timed out. Check its state, then rerun setup to finish.") from None
        if result.returncode:
            detail = (result.stderr or result.stdout).strip()
            if self.secret:
                detail = detail.replace(self.secret, "[redacted]")
                detail = detail.replace(json.dumps(self.secret)[1:-1], "[redacted]")
            raise SetupError(f"{self.name} {' '.join(arguments[:2])} failed: {detail}")
        if not as_json:
            return None
        try:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                # Claude may print progress before its final JSON result.
                return json.loads(result.stdout.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            raise SetupError("The client returned unexpected output. Update it and try again.") from None

    def marketplaces(self):
        result = self.run("plugin", "marketplace", "list", as_json=True)
        return result["marketplaces"] if self.codex else result

    def plugins(self):
        result = self.run("plugin", "list", as_json=True)
        return result["installed"] if self.codex else result

    def plugin_id(self, plugin):
        return plugin["pluginId"] if self.codex else plugin["id"]

    def user_plugin(self, plugin):
        return self.codex or plugin.get("scope") == "user"


def read_key():
    with warnings.catch_warnings():
        warnings.simplefilter("error", getpass.GetPassWarning)
        key = getpass.getpass("Lumoz API key (client_id:client_secret): ").strip()
    client, separator, secret = key.partition(":")
    if not separator or not client or not secret or any(c.isspace() for c in key):
        raise SetupError("Enter the full API key in client_id:client_secret format.")
    return key


def install(client, defaults):
    uvx = shutil.which("uvx")
    if not uvx:
        raise SetupError("uvx was not found. Install uv: https://docs.astral.sh/uv/getting-started/installation/")
    uvx = str(Path(uvx).resolve())
    if client.codex:
        client.run("plugin", "add", "--help")
        print("Setup saves the key as plaintext in your private Codex config.toml.")
        print("It replaces the existing 'lumoz' MCP entry, including custom settings.")
    else:
        supported = subprocess.run(
            [client.command, "plugin", "configure", "--help"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
        )
        if supported.returncode or "--values-stdin" not in supported.stdout:
            raise SetupError("Update Claude Code: plugin configure --values-stdin is required.")
        print("Setup saves the key using Claude Code's plugin credential configuration.")
    client.secret = read_key()
    marketplaces = client.marketplaces()
    if not any(m["name"] == "lumoz" for m in marketplaces):
        client.run("plugin", "marketplace", "add", defaults["marketplace"])
    else:
        print("Lumoz marketplace is already registered; keeping its configured source.")

    wanted = ["lumoz-skills@lumoz"]
    if not client.codex:
        wanted.append("lumoz-mcp@lumoz")
    plugins = client.plugins()
    for identifier in wanted:
        existing = next((p for p in plugins if client.plugin_id(p) == identifier and client.user_plugin(p)), None)
        if existing is None or (client.codex and not existing.get("enabled", True)):
            arguments = ["plugin", "add" if client.codex else "install", identifier]
            if not client.codex:
                arguments += ["--scope", "user"]
            client.run(*arguments)
        elif not existing.get("enabled", True):
            client.run("plugin", "enable", identifier, "--scope", "user")
        else:
            print(f"{identifier} is already installed.")

    if client.codex:
        client.run(
            "mcp", "add", "lumoz", "--env", f"LUMOZ_API_KEY={client.secret}",
            "--", uvx, "--from", defaults["server"], "lumoz-mcp",
        )
        print(f"Saved the MCP connection for {defaults['server']} and its API key.")
    else:
        result = client.run(
            "plugin", "configure", "lumoz-mcp@lumoz", "--values-stdin",
            values={"api_key": client.secret, "uvx_path": uvx}, as_json=True,
        )
        if result.get("unconfigured"):
            raise SetupError("Claude Code still reports missing plugin settings. Rerun setup to configure them.")
        print("Saved the MCP plugin's API key and uvx path.")
    print("Setup complete. Restart the client, open /mcp, then ask:")
    print("  Use Lumoz to list the apps and environments I can access. Do not modify anything.")
    print("Ask for lumoz-evals to use the skill. A successful tool call verifies API access.")
    print("The first MCP connection downloads the server through uvx if needed.")


def uninstall(client):
    if client.codex:
        client.run("mcp", "remove", "lumoz")
        print("Removed the Lumoz MCP entry and any API key stored in that entry.")
    wanted = {"lumoz-skills@lumoz"}
    if not client.codex:
        wanted.add("lumoz-mcp@lumoz")
    for plugin in client.plugins():
        identifier = client.plugin_id(plugin)
        if identifier in wanted and client.user_plugin(plugin):
            arguments = ["plugin", "remove" if client.codex else "uninstall", identifier]
            if not client.codex:
                arguments += ["--scope", "user"]
            result = client.run(*arguments, as_json=True)
            if not client.codex and result.get("savedKept"):
                raise SetupError("Claude removed the plugin but kept saved settings. Check claude plugin list and its uninstall output.")
    remaining = client.plugins()
    if any(client.plugin_id(p).endswith("@lumoz") for p in remaining):
        print("Kept the Lumoz marketplace: other plugins or installation scopes still use it.")
    elif any(m["name"] == "lumoz" for m in client.marketplaces()):
        arguments = ["plugin", "marketplace", "remove", "lumoz"]
        if not client.codex:
            arguments += ["--scope", "user"]
        client.run(*arguments)
    if not client.codex:
        print("Claude manages saved-key deletion; settings remain if another scope still uses the plugin.")
    print("Uninstall complete. Restart active sessions to disconnect their running server.")
    print("API keys remain valid in Lumoz. Package caches and copies saved elsewhere remain.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("client", choices=("codex", "claude-code"))
    parser.add_argument("action", nargs="?", default="install", choices=("install", "uninstall"))
    args = parser.parse_args(argv)
    try:
        client = Client(args.client)
        if args.action == "uninstall":
            uninstall(client)
        else:
            defaults = json.loads(files("lumoz_setup").joinpath("defaults.json").read_text())
            install(client, defaults)
    except (EOFError, KeyboardInterrupt):
        print("\nSetup cancelled. Any completed steps are kept; rerun setup to finish.", file=sys.stderr)
        return 1
    except getpass.GetPassWarning:
        print("Run setup directly in a terminal with hidden input.", file=sys.stderr)
        return 1
    except subprocess.TimeoutExpired:
        print("The client timed out. Check its state before retrying.", file=sys.stderr)
        return 1
    except (KeyError, TypeError, json.JSONDecodeError):
        print("Unexpected client configuration. Update the client and rerun setup.", file=sys.stderr)
        return 1
    except (SetupError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0

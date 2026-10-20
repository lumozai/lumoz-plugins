#!/usr/bin/env python3
"""Install or uninstall the Lumoz stdio MCP connection for Codex."""

import argparse
import getpass
import json
from pathlib import Path
import shutil
import subprocess
import sys
import warnings


ROOT = Path(__file__).resolve().parents[1]


def run_codex(codex, arguments, secret=None):
    # Capture output: a failed CLI invocation must not echo its secret argument.
    result = subprocess.run(
        [codex, "mcp", *arguments], capture_output=True, text=True, timeout=30,
    )
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        if secret:
            detail = detail.replace(secret, "[redacted]")
        raise ValueError(f"Codex could not {arguments[0]} Lumoz. {detail}")


def install(codex):
    uvx = shutil.which("uvx")
    if not uvx:
        raise ValueError("uvx was not found. Install uv: https://docs.astral.sh/uv/getting-started/installation/")
    metadata = json.loads((ROOT / "plugin-source/metadata.json").read_text())
    package = f"{metadata['mcp']['package']}=={metadata['mcp']['version']}"
    print("This saves your API key as plaintext in your private Codex config.toml.")
    print("Running setup again replaces the existing 'lumoz' MCP registration and key.")
    # Refuse getpass's fallback to visible input when no terminal is available.
    with warnings.catch_warnings():
        warnings.simplefilter("error", getpass.GetPassWarning)
        key = getpass.getpass("Lumoz API key (client_id:client_secret): ").strip()
    client, separator, secret = key.partition(":")
    if not separator or not client or not secret or any(character.isspace() for character in key):
        raise ValueError("Enter the full API key in client_id:client_secret format.")
    run_codex(codex, [
        "add", "lumoz", "--env", f"LUMOZ_API_KEY={key}",
        "--", uvx, "--from", package, "lumoz-mcp",
    ], secret=key)
    print(f"Registered Lumoz ({package}) and saved the API key. No export is needed.")
    print("Restart Codex, open /mcp, then ask:")
    print("  Use Lumoz to list all apps and environments I can access. Do not modify anything.")
    print("Registration is complete; a successful tool call verifies API access.")
    print("The first connection downloads the server through uvx if needed.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", default="install", choices=("install", "uninstall"))
    args = parser.parse_args(argv)
    codex = shutil.which("codex")
    if not codex:
        print("Codex CLI was not found. Install Codex and add it to PATH first.", file=sys.stderr)
        return 1
    try:
        if args.action == "uninstall":
            run_codex(codex, ["remove", "lumoz"])
            print("Removed the Lumoz MCP registration and any API key stored in that entry.")
            print("Restart active Codex sessions to disconnect the running server.")
            print("The key remains valid in Lumoz; cached packages remain in uv's cache.")
        else:
            install(codex)
    except (EOFError, KeyboardInterrupt):
        print("\nSetup cancelled.", file=sys.stderr)
        return 1
    except getpass.GetPassWarning:
        print("A terminal with hidden input is required. Run setup directly in your terminal.", file=sys.stderr)
        return 1
    except subprocess.TimeoutExpired:
        print("Codex did not finish within 30 seconds. Check its configuration before retrying.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

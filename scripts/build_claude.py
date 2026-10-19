#!/usr/bin/env python3
"""Generate independent Claude plugins and optionally build their trial ZIPs."""

import argparse
import json
from pathlib import Path
import sys
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]


def manifests(metadata):
    author = {"name": "Lumoz AI", "email": "support@lumoz.ai", "url": "https://lumoz.ai"}
    common = {
        "author": author,
        "homepage": "https://github.com/lumozai/lumoz-plugins#readme",
        "repository": "https://github.com/lumozai/lumoz-plugins",
        "license": "Apache-2.0",
    }
    skills = {
        **common, **metadata["plugins"]["skills"],
        "displayName": "Lumoz Skills",
        "description": "Create regression evals from Lumoz eval suggestions using your project's test framework.",
        "keywords": ["lumoz", "skills", "evals", "observability"],
    }
    mcp = {
        **common, **metadata["plugins"]["mcp"],
        "displayName": "Lumoz MCP (Claude Code)",
        "description": "Connect Claude Code to Lumoz traces, signals, problems, RCAs, and eval suggestions.",
        "keywords": ["lumoz", "mcp", "observability", "rca"],
        "userConfig": {
            "api_key": {
                "type": "string", "title": "Lumoz API key",
                "description": "API key from Lumoz Console, in client_id:client_secret format.",
                "required": True, "sensitive": True,
            },
            "uvx_path": {
                "type": "string", "title": "uvx executable",
                "description": "Use uvx from PATH, or enter its full executable path.",
                "default": "uvx",
            },
        },
    }
    return {
        ".claude-plugin/marketplace.json": {
            "name": metadata["name"], "owner": author,
            "description": "Lumoz skills for Claude and a separate MCP integration for Claude Code.",
            "plugins": [
                {"name": plugin["name"], "source": f"./plugins/{plugin['name']}",
                 "description": plugin["description"]}
                for plugin in (skills, mcp)
            ],
        },
        f"plugins/{skills['name']}/.claude-plugin/plugin.json": skills,
        f"plugins/{mcp['name']}/.claude-plugin/plugin.json": mcp,
        f"plugins/{mcp['name']}/.mcp.json": {
            "mcpServers": {
                "lumoz": {
                    "command": "${user_config.uvx_path}",
                    "args": ["--from", f"{metadata['mcp']['package']}=={metadata['mcp']['version']}", "lumoz-mcp"],
                    "env": {"LUMOZ_API_KEY": "${user_config.api_key}"},
                },
            },
        },
    }


def safe_input(path):
    relative = path.relative_to(ROOT)
    if any(parent.is_symlink() for parent in (path, *path.parents) if parent != ROOT):
        raise ValueError(f"Package input contains a symlink: {relative}")
    local_config = any(
        part.startswith(".env") or part in {".aws", ".codex", ".git", ".claude", ".venv", "venv"}
        for part in relative.parts
    )
    if local_config or path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
        raise ValueError(f"Local configuration or credential file cannot be packaged: {relative}")


def package_files(name, skills=False):
    root = ROOT / "plugins" / name
    files = [root / ".claude-plugin/plugin.json", root / "README.md", root / "LICENSE"]
    if (root / "NOTICE").is_file():
        files.append(root / "NOTICE")
    if skills:
        files += sorted(path for path in (root / "skills").rglob("*") if path.is_file())
    else:
        files.append(root / ".mcp.json")
    files = [path for path in files if "__pycache__" not in path.parts and path.suffix != ".pyc"]
    for path in files:
        safe_input(path)
        if not path.is_file():
            raise ValueError(f"Required package input missing: {path.relative_to(ROOT)}")
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Check generated manifests/licenses without writing files.")
    mode.add_argument("--zip", action="store_true", help="Also build one minimal trial ZIP per plugin.")
    args = parser.parse_args()
    metadata = json.loads((ROOT / "plugin-source/metadata.json").read_text())
    plugins = metadata["plugins"]
    # Retired root files or crossed components would defeat independent installs.
    forbidden = (
        ".claude-plugin/plugin.json", ".mcp.json", "skills",
        f"plugins/{plugins['skills']['name']}/.mcp.json",
        f"plugins/{plugins['mcp']['name']}/skills",
    )
    for name in forbidden:
        if (ROOT / name).exists():
            print(f"Unexpected combined-plugin component: {name}", file=sys.stderr)
            return 1
    contents = {
        relative: (json.dumps(value, indent=2) + "\n").encode()
        for relative, value in manifests(metadata).items()
    }
    try:
        for license_name in ("LICENSE", "NOTICE"):
            source = ROOT / license_name
            if license_name == "NOTICE" and not source.exists():
                continue
            safe_input(source)
            data = source.read_bytes()
            for plugin in plugins.values():
                contents[f"plugins/{plugin['name']}/{license_name}"] = data
        stale = []
        for relative, content in contents.items():
            path = ROOT / relative
            safe_input(path)
            if args.check:
                if not path.is_file() or path.read_bytes() != content:
                    stale.append(relative)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
        if stale:
            print("Outdated plugin files: " + ", ".join(stale), file=sys.stderr)
            print("Run python3 scripts/build_claude.py", file=sys.stderr)
            return 1
        skill_root = ROOT / "plugins" / plugins["skills"]["name"] / "skills"
        if not list(skill_root.glob("*/SKILL.md")):
            raise ValueError("No skills found to include in the skills plugin.")
        packages = {
            kind: package_files(plugin["name"], skills=kind == "skills")
            for kind, plugin in plugins.items()
        }
        if args.zip:
            for kind, files in packages.items():
                plugin = plugins[kind]
                output = ROOT / "dist" / f"{plugin['name']}-{plugin['version']}.zip"
                output.parent.mkdir(parents=True, exist_ok=True)
                with ZipFile(output, "w", ZIP_DEFLATED) as archive:
                    for path in files:
                        archive.write(path, path.relative_to(ROOT / "plugins" / plugin["name"]).as_posix())
                print(f"Built {output.relative_to(ROOT)} ({len(files)} files)")
        else:
            print(f"Two Claude plugins {'checked' if args.check else 'generated'}.")
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

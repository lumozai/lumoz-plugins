#!/usr/bin/env python3
"""Generate Desktop extension metadata and build dist/lumoz.mcpb."""

import argparse
import json
from pathlib import Path
import sys
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]


def generated_files(metadata):
    manifest = {
        "manifest_version": "0.4",
        "name": metadata["desktop"]["name"],
        "display_name": "Lumoz",
        "version": metadata["desktop"]["version"],
        "description": "Investigate Lumoz traces, signals, problems, and root cause analyses.",
        "author": {"name": "Lumoz AI", "email": "support@lumoz.ai", "url": "https://lumoz.ai"},
        "homepage": "https://lumoz.ai",
        "repository": {"type": "git", "url": "https://github.com/lumozai/lumoz-plugins"},
        "support": "https://github.com/lumozai/lumoz-plugins/issues",
        "license": "Apache-2.0",
        "server": {
            "type": "uv",
            "entry_point": "server.py",
            "mcp_config": {
                "command": "uv",
                "args": ["run", "--directory", "${__dirname}", "--no-dev", "server.py"],
                "env": {"LUMOZ_API_KEY": "${user_config.api_key}"},
            },
        },
        "compatibility": {
            "platforms": ["darwin", "win32"],
            "runtimes": {"python": ">=3.11"},
        },
        "user_config": {
            "api_key": {
                "type": "string",
                "title": "Lumoz API key",
                "description": "API key from Lumoz Console, in client_id:client_secret format.",
                "required": True,
                "sensitive": True,
            },
        },
        "keywords": ["lumoz", "observability", "rca", "evals"],
    }
    # JSON strings are valid TOML strings for these metadata values.
    dependency = f"{metadata['mcp']['package']}=={metadata['mcp']['version']}"
    project = (
        '[project]\nname = "lumoz-desktop"\n'
        f'version = {json.dumps(metadata["desktop"]["version"])}\n'
        'requires-python = ">=3.11"\n'
        f'dependencies = [{json.dumps(dependency)}]\n'
    )
    return {
        "manifest.json": json.dumps(manifest, indent=2) + "\n",
        "pyproject.toml": project,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check generated files without writing or building.")
    args = parser.parse_args()
    metadata = json.loads((ROOT / "plugin-source/metadata.json").read_text())
    extension = ROOT / "mcpb"
    generated = generated_files(metadata)
    inputs = [(extension / name, name) for name in (*generated, "server.py")]
    inputs.append((ROOT / "LICENSE", "LICENSE"))
    if (ROOT / "NOTICE").exists():
        inputs.append((ROOT / "NOTICE", "NOTICE"))
    # Only allow explicit runtime files; never archive the whole checkout or a venv.
    for path, _ in inputs:
        if any(parent.is_symlink() for parent in (path, *path.parents) if parent != ROOT):
            print(f"Package input contains a symlink: {path.relative_to(ROOT)}", file=sys.stderr)
            return 1
        if path.name not in generated and not path.is_file():
            print(f"Required package input missing: {path.relative_to(ROOT)}", file=sys.stderr)
            return 1
    stale = []
    for name, content in generated.items():
        path = extension / name
        if args.check:
            if not path.is_file() or path.read_text() != content:
                stale.append(name)
        else:
            path.write_text(content)
    if stale:
        print("Outdated MCPB metadata: " + ", ".join(stale), file=sys.stderr)
        print("Run python3 scripts/build_mcpb.py", file=sys.stderr)
        return 1
    if args.check:
        print("MCPB metadata checked.")
        return 0
    output = ROOT / "dist" / f"{metadata['desktop']['name']}.mcpb"
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for path, name in inputs:
            archive.write(path, name)
    print(f"Built {output.relative_to(ROOT)} ({len(inputs)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

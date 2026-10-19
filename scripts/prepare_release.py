#!/usr/bin/env python3
"""Check a component release tag and select its built artifact without publishing."""

import argparse
import json
from pathlib import Path
import re
import sys
import urllib.request


ROOT = Path(__file__).resolve().parents[1]


def release_details(metadata, tag):
    match = re.fullmatch(r"lumoz-(skills|mcp|desktop)-v(\d+\.\d+\.\d+)", tag)
    if not match:
        raise ValueError("Expected lumoz-{skills|mcp|desktop}-vMAJOR.MINOR.PATCH")
    component, version = match.groups()
    package = metadata["desktop"] if component == "desktop" else metadata["plugins"][component]
    if version != package["version"]:
        raise ValueError(f"Tag version {version} does not match {component} metadata {package['version']}")
    asset = f"{package['name']}.mcpb" if component == "desktop" else f"{package['name']}-{version}.zip"
    return {
        "component": component, "version": version, "asset": f"dist/{asset}",
        "title": f"{'Lumoz Desktop' if component == 'desktop' else package['name']} {version}",
        "latest": "true" if component == "desktop" else "false",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag")
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--verify-pypi", action="store_true", help="Check the pinned server exists before MCP publication.")
    args = parser.parse_args()
    metadata = json.loads((ROOT / "plugin-source/metadata.json").read_text())
    try:
        details = release_details(metadata, args.tag)
        if not (ROOT / details["asset"]).is_file():
            raise ValueError(f"Build the artifact first: {details['asset']}")
        if args.verify_pypi and details["component"] != "skills":
            server = metadata["mcp"]
            with urllib.request.urlopen(
                f"https://pypi.org/pypi/{server['package']}/{server['version']}/json", timeout=30,
            ) as response:
                published = json.load(response)
            if published["info"]["version"] != server["version"] or not published.get("urls"):
                raise ValueError("Pinned PyPI server release has no available artifacts")
        lines = [
            f"{details['title']}\n", f"Component: `{details['component']}`.\n",
            "Installation: https://github.com/lumozai/lumoz-plugins#readme\n",
        ]
        if details["component"] != "skills":
            lines.append(f"Server dependency: `{metadata['mcp']['package']}=={metadata['mcp']['version']}`.\n")
        (ROOT / "dist/release-notes.md").write_text("\n".join(lines))
        if args.github_output:
            with args.github_output.open("a") as output:
                for key, value in details.items():
                    output.write(f"{key}={value}\n")
        print(json.dumps(details, indent=2))
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

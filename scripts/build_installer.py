#!/usr/bin/env python3
"""Generate the installer package's runtime defaults and license."""

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    metadata = json.loads((ROOT / "plugin-source/metadata.json").read_text())
    contents = {
        "installer/src/lumoz_setup/defaults.json": (json.dumps({
            "marketplace": "lumozai/lumoz-plugins",
            "server": f"{metadata['mcp']['package']}=={metadata['mcp']['version']}",
        }, indent=2) + "\n").encode(),
        "installer/LICENSE": (ROOT / "LICENSE").read_bytes().rstrip(b"\n") + b"\n",
    }
    for relative, content in contents.items():
        path = ROOT / relative
        if args.check:
            if not path.is_file() or path.read_bytes() != content:
                print(f"Outdated {relative}; run python3 scripts/build_installer.py", file=sys.stderr)
                return 1
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    print("Installer metadata checked." if args.check else "Installer metadata generated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

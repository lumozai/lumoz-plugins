#!/usr/bin/env python3
"""Compatibility entry point; customer setup now lives in installer/."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "installer/src"))
from lumoz_setup.cli import main


if __name__ == "__main__":
    print("Use lumoz-setup codex instead. This entry point now manages skills and MCP together.")
    sys.exit(main(["codex", *sys.argv[1:]]))

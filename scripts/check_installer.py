#!/usr/bin/env python3
"""Check the built installer wheel and run it outside the source checkout."""

from configparser import ConfigParser
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]


def main():
    project = tomllib.loads((ROOT / "installer/pyproject.toml").read_text())["project"]
    wheel = ROOT / "dist/installer" / f"lumoz_setup-{project['version']}-py3-none-any.whl"
    metadata = json.loads((ROOT / "plugin-source/metadata.json").read_text())
    with ZipFile(wheel) as archive:
        names = set(archive.namelist())
        package_files = {name for name in names if name.startswith("lumoz_setup/")}
        expected = {"lumoz_setup/__init__.py", "lumoz_setup/cli.py", "lumoz_setup/defaults.json"}
        if package_files != expected or any(
            not name.startswith(("lumoz_setup/", f"lumoz_setup-{project['version']}.dist-info/"))
            for name in names
        ):
            raise ValueError("Unexpected installer wheel contents")
        defaults = json.loads(archive.read("lumoz_setup/defaults.json"))
        if defaults["server"] != f"{metadata['mcp']['package']}=={metadata['mcp']['version']}":
            raise ValueError("The wheel's server pin does not match release metadata")
        entry_points = ConfigParser()
        entry_points.read_string(archive.read(f"lumoz_setup-{project['version']}.dist-info/entry_points.txt").decode())
        if entry_points["console_scripts"]["lumoz-setup"] != "lumoz_setup.cli:main":
            raise ValueError("Missing lumoz-setup console entry point")
    # Import from the wheel under isolated Python, with no checkout or site packages.
    with tempfile.TemporaryDirectory() as directory:
        result = subprocess.run([
            sys.executable, "-I", "-c",
            "import sys; sys.path.insert(0, sys.argv[1]); "
            "from lumoz_setup.cli import main; "
            "from importlib.resources import files; "
            "assert files('lumoz_setup').joinpath('defaults.json').is_file(); "
            "main(['--help'])",
            str(wheel),
        ], cwd=directory, capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise ValueError(result.stderr)
    print(f"Validated {wheel.name}: scoped files, pinned server, entry point, and isolated execution.")


if __name__ == "__main__":
    main()

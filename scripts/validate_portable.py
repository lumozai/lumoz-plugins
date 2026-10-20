#!/usr/bin/env python3
"""Validate generated portable manifests against the published v1 schemas."""

import json
import urllib.request

from jsonschema import Draft202012Validator

from build_claude import PLUGIN_SCHEMA, ROOT


def main():
    metadata = json.loads((ROOT / "plugin-source/metadata.json").read_text())
    with urllib.request.urlopen(PLUGIN_SCHEMA, timeout=30) as response:
        schema = json.load(response)
    Draft202012Validator.check_schema(schema)
    path = ROOT / "plugins" / metadata["plugins"]["skills"]["name"] / "plugin.json"
    Draft202012Validator(schema).validate(json.loads(path.read_text()))
    print(f"Validated {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

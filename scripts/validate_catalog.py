#!/usr/bin/env python3
"""Validate data/guidelines.yml against data/guidelines.schema.json.

Checks:
1. Valid YAML syntax and top-level list structure.
2. JSON Schema validation against data/guidelines.schema.json.
3. Uniqueness of `id` across all catalog entries.
4. Presence of either `source_url` or `landing_url` for every entry.

Usage:
    python scripts/validate_catalog.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "data" / "guidelines.yml"
SCHEMA_PATH = ROOT / "data" / "guidelines.schema.json"


def validate_catalog(catalog_path: Path = CATALOG_PATH, schema_path: Path = SCHEMA_PATH) -> list[str]:
    errors: list[str] = []
    if not catalog_path.exists():
        return [f"Catalog file not found: {catalog_path}"]
    if not schema_path.exists():
        return [f"Schema file not found: {schema_path}"]

    catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    if not isinstance(catalog, list):
        return ["Catalog root must be a YAML list of guideline entries."]

    validator = jsonschema.Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(catalog), key=lambda e: list(e.path)):
        idx = err.path[0] if err.path else "?"
        entry_id = catalog[idx].get("id", f"index {idx}") if isinstance(idx, int) and idx < len(catalog) else str(idx)
        field_path = ".".join(str(p) for p in list(err.path)[1:]) or "<root>"
        errors.append(f"[{entry_id}] {field_path}: {err.message}")

    seen_ids: set[str] = set()
    for idx, entry in enumerate(catalog):
        if not isinstance(entry, dict):
            continue
        gid = entry.get("id")
        if gid in seen_ids:
            errors.append(f"[{gid}] Duplicate id at index {idx}")
        if gid:
            seen_ids.add(gid)
        if not entry.get("source_url") and not entry.get("landing_url"):
            errors.append(f"[{gid}] Neither source_url nor landing_url is provided")

    return errors


def main() -> int:
    errors = validate_catalog()
    if errors:
        print(f"Validation FAILED with {len(errors)} error(s):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    catalog = yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8"))
    jurisdictions = {g["jurisdiction"] for g in catalog}
    levels = {}
    for g in catalog:
        lvl = g["jurisdiction_level"]
        levels[lvl] = levels.get(lvl, 0) + 1
    print(
        f"Catalog validation PASSED: {len(catalog)} guidelines across "
        f"{len(jurisdictions)} jurisdictions ({levels})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

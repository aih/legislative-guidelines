#!/usr/bin/env python3
"""Validate the catalog files (data/guidelines.yml, data/subnational.yml) against data/guidelines.schema.json.

Checks:
1. Valid YAML syntax and top-level list structure in each file.
2. JSON Schema validation against data/guidelines.schema.json.
3. Uniqueness of `id` across all catalog files.
4. Presence of either `source_url` or `landing_url` for every entry.
5. For subnational entries, `subdivision_code` starts with the parent `country_code`.

Usage:
    python scripts/validate_catalog.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import CATALOG_FILES, load_file  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "data" / "guidelines.schema.json"


def validate_catalog(catalog_paths: list[Path] | None = None, schema_path: Path = SCHEMA_PATH) -> list[str]:
    errors: list[str] = []
    paths = catalog_paths or CATALOG_FILES
    if not paths[0].exists():
        return [f"Catalog file not found: {paths[0]}"]
    if not schema_path.exists():
        return [f"Schema file not found: {schema_path}"]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)

    seen_ids: dict[str, str] = {}
    for path in paths:
        if not path.exists():
            continue
        name = path.name
        catalog = load_file(path)
        if not isinstance(catalog, list):
            errors.append(f"{name}: root must be a YAML list of guideline entries.")
            continue

        for err in sorted(validator.iter_errors(catalog), key=lambda e: list(e.path)):
            idx = err.path[0] if err.path else "?"
            entry_id = catalog[idx].get("id", f"index {idx}") if isinstance(idx, int) and idx < len(catalog) else str(idx)
            field_path = ".".join(str(p) for p in list(err.path)[1:]) or "<root>"
            errors.append(f"{name} [{entry_id}] {field_path}: {err.message}")

        for idx, entry in enumerate(catalog):
            if not isinstance(entry, dict):
                continue
            gid = entry.get("id")
            if gid in seen_ids:
                errors.append(f"{name} [{gid}] Duplicate id (also in {seen_ids[gid]})")
            if gid:
                seen_ids[gid] = name
            if not entry.get("source_url") and not entry.get("landing_url"):
                errors.append(f"{name} [{gid}] Neither source_url nor landing_url is provided")
            sub = entry.get("subdivision_code")
            if sub and not sub.startswith(f"{entry.get('country_code')}-"):
                errors.append(f"{name} [{gid}] subdivision_code {sub} does not belong to country_code {entry.get('country_code')}")
            if sub and entry.get("jurisdiction_level") != "subnational":
                errors.append(f"{name} [{gid}] subdivision_code is set but jurisdiction_level is not subnational")

    return errors


def main() -> int:
    errors = validate_catalog()
    if errors:
        print(f"Validation FAILED with {len(errors)} error(s):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    catalog = [g for path in CATALOG_FILES for g in load_file(path)]
    jurisdictions = {g["jurisdiction"] for g in catalog}
    levels: dict[str, int] = {}
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

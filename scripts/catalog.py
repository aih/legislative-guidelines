"""Load the guideline catalog.

The catalog is split across files that share one entry format (data/SCHEMA.md):

    data/guidelines.yml     national, supranational and international guidelines
    data/subnational.yml    state, province, territory and devolved-government guidelines

`load_catalog()` returns the entries of every file that exists, in that order.
"""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CATALOG_FILES = [ROOT / "data" / "guidelines.yml", ROOT / "data" / "subnational.yml"]


def load_file(path: Path) -> list:
    entries = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else []
    return entries or []


def load_catalog(paths: list[Path] | None = None) -> list[dict]:
    catalog: list[dict] = []
    for path in paths or CATALOG_FILES:
        catalog.extend(load_file(path))
    return catalog

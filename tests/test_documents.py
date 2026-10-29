"""Checks on converted documents committed under documents/<id>/."""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
CONVERTED = sorted(ROOT.glob("documents/*/content.html"))
CATALOG_IDS = {g["id"] for g in yaml.safe_load((ROOT / "data" / "guidelines.yml").read_text(encoding="utf-8"))}

# Shortest genuine guideline in the collection is a few thousand words; block and login pages are under a few hundred.
MIN_WORDS = 1000
BLOCK_PAGE = re.compile(
    r"requisição foi bloqueada|access denied|request (?:was )?blocked|enable javascript|captcha|log ?in to (?:the )?site",
    re.I,
)


@pytest.mark.parametrize("path", CONVERTED, ids=lambda p: p.parent.name)
def test_converted_document_has_substantial_text(path: Path):
    text = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml").get_text(" ")
    words = len(text.split())
    assert words >= MIN_WORDS, f"{path.parent.name}: only {words} words; the download was probably not the document"
    head = text[:3000]
    assert not BLOCK_PAGE.search(head), f"{path.parent.name}: text looks like a block or login page"


@pytest.mark.parametrize("path", CONVERTED, ids=lambda p: p.parent.name)
def test_converted_document_is_catalogued(path: Path):
    assert path.parent.name in CATALOG_IDS

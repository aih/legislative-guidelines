#!/usr/bin/env python3
"""Build the static site into dist/.

Reads data/guidelines.yml, data/retrieval.json and the converted documents in
documents/<id>/ and writes:

    dist/index.html                    catalog with filters
    dist/guidelines/<id>/index.html    one page per guideline: metadata, contents, full text
    dist/guidelines/<id>/original.*    stored copy of the original document
    dist/search.html                   full-text search (Pagefind index built afterwards)
    dist/contribute.html               submission form for missing guidelines
    dist/about.html                    method and field definitions
    dist/catalog.json, catalog.csv     machine-readable catalog
    dist/opensearch.xml                OpenSearch description, so browsers can add the site as a search engine

Run `npx pagefind --site dist` afterwards to build the search index.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import shutil
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "site_src"
DIST = ROOT / "dist"
DOCS = ROOT / "documents"

SITE = {
    "title": "Legislative Drafting Guidelines",
    "subtitle": "National and supranational drafting manuals, collected and converted to HTML",
    "repo": os.environ.get("SITE_REPO", "aih/legislative-guidelines"),
    "url": os.environ.get("SITE_URL", "https://aih.github.io/legislative-guidelines/"),
    # Optional: a Formspree-compatible endpoint. When empty, the contribute form
    # opens a prefilled GitHub issue instead.
    "form_endpoint": os.environ.get("FORM_ENDPOINT", ""),
}

STATUS_LABELS = {
    "current": "Current",
    "in-force": "In force",
    "dated": "Dated",
    "superseded": "Superseded",
    "unverified": "Unverified",
}

LANGUAGE_NAMES = {
    "en": "English", "fr": "French", "de": "German", "it": "Italian", "es": "Spanish", "pt": "Portuguese",
    "nl": "Dutch", "da": "Danish", "sv": "Swedish", "fi": "Finnish", "pl": "Polish", "cs": "Czech",
    "multilingual": "Multilingual",
}


def load() -> list[dict]:
    catalog = yaml.safe_load((ROOT / "data" / "guidelines.yml").read_text(encoding="utf-8"))
    retrieval_path = ROOT / "data" / "retrieval.json"
    retrieval = json.loads(retrieval_path.read_text(encoding="utf-8")) if retrieval_path.exists() else {}
    for g in catalog:
        g["retrieval"] = retrieval.get(g["id"], {})
        doc_dir = DOCS / g["id"]
        content = doc_dir / "content.html"
        g["content"] = content.read_text(encoding="utf-8") if content.exists() else ""
        toc = doc_dir / "toc.json"
        g["toc"] = json.loads(toc.read_text(encoding="utf-8")) if toc.exists() else []
        originals = sorted(doc_dir.glob("original.*")) if doc_dir.exists() else []
        g["stored_original"] = originals[0] if originals else None
        g["status_label"] = STATUS_LABELS.get(g.get("currency", {}).get("status", "unverified"), "Unverified")
        g["language_names"] = [LANGUAGE_NAMES.get(code, code) for code in g.get("languages", [])]
    level_order = {"supranational": 0, "international": 1, "national": 2}
    catalog.sort(key=lambda g: (level_order.get(g["jurisdiction_level"], 9), g["jurisdiction"], g["title"]))
    return catalog


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def export_catalog(catalog: list[dict]) -> None:
    fields = [
        "id", "title", "title_en", "jurisdiction", "jurisdiction_level", "country_code", "region", "issuing_body",
        "languages", "document_type", "legal_status", "edition", "published", "last_updated", "currency_status",
        "currency_note", "checked_on", "original_format", "source_url", "landing_url", "license",
        "retrieved_at", "stored_format", "sha256",
    ]
    rows = []
    for g in catalog:
        cur = g.get("currency", {})
        ret = g["retrieval"]
        rows.append(
            {
                **{k: g.get(k) for k in fields if k in g},
                "languages": ", ".join(g.get("languages", [])),
                "currency_status": cur.get("status"),
                "currency_note": cur.get("note"),
                "checked_on": cur.get("checked_on"),
                "retrieved_at": ret.get("retrieved_at") if ret.get("sha256") else None,
                "stored_format": ret.get("format"),
                "sha256": ret.get("sha256"),
            }
        )
    write(DIST / "catalog.json", json.dumps(rows, indent=1, ensure_ascii=False))
    with (DIST / "catalog.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k) for k in fields})


def main() -> int:
    catalog = load()
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copytree(SRC / "assets", DIST / "assets")

    env = Environment(loader=FileSystemLoader(SRC / "templates"), autoescape=select_autoescape(["html", "xml"]))
    common = {
        "site": SITE,
        "built": dt.date.today().isoformat(),
        "catalog": catalog,
        "status_labels": STATUS_LABELS,
    }

    facets = {
        "regions": sorted({g["region"] for g in catalog}),
        "levels": sorted({g["jurisdiction_level"] for g in catalog}),
        "statuses": [s for s in STATUS_LABELS if any(g.get("currency", {}).get("status") == s for g in catalog)],
        "languages": sorted({name for g in catalog for name in g["language_names"]}),
    }
    stats = {
        "documents": len(catalog),
        "jurisdictions": len({g["jurisdiction"] for g in catalog}),
        "converted": sum(1 for g in catalog if g["content"]),
        "stored": sum(1 for g in catalog if g["stored_original"]),
    }
    for name in ["index.html", "search.html", "contribute.html", "about.html", "opensearch.xml"]:
        tpl = env.get_template(name)
        write(DIST / name, tpl.render(**common, base="", facets=facets, stats=stats, page=name))

    tpl = env.get_template("guideline.html")
    for g in catalog:
        out = DIST / "guidelines" / g["id"]
        out.mkdir(parents=True, exist_ok=True)
        stored = None
        if g["stored_original"]:
            stored = g["stored_original"].name
            shutil.copy2(g["stored_original"], out / stored)
        write(out / "index.html", tpl.render(**common, base="../../", g=g, stored=stored, page="guideline"))

    export_catalog(catalog)
    write(DIST / ".nojekyll", "")
    print(f"built {len(catalog)} guideline pages into {DIST.relative_to(ROOT)}/ "
          f"({stats['converted']} with converted text, {stats['stored']} with stored originals)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

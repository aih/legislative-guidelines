#!/usr/bin/env python3
"""Build the static site into dist/.

Reads data/guidelines.yml, data/retrieval.json, data/comparative_matrix.yml and
the converted documents in documents/<id>/ and writes:

    dist/index.html                    landing page: search box and A-Z filterable list
    dist/compare.html                  cross-jurisdictional comparative matrix
    dist/auditor.html                  interactive bill drafting compliance auditor (1-10 score)
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
import re
import os
import shutil
import sys
import unicodedata
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
    "nl": "Dutch", "da": "Danish", "sv": "Swedish", "no": "Norwegian", "nb": "Norwegian", "fi": "Finnish",
    "et": "Estonian", "lv": "Latvian", "lt": "Lithuanian", "pl": "Polish", "cs": "Czech", "sk": "Slovak",
    "sl": "Slovenian", "hr": "Croatian", "hu": "Hungarian", "ro": "Romanian", "bg": "Bulgarian", "el": "Greek",
    "ja": "Japanese", "ko": "Korean", "zh": "Chinese", "ms": "Malay", "cy": "Welsh", "ga": "Irish",
    "ar": "Arabic", "ru": "Russian", "sq": "Albanian", "sr": "Serbian", "ka": "Georgian", "rw": "Kinyarwanda",
    "multilingual": "Multilingual",
}

COMMON_LAW_CODES = {
    "GB", "GB-SCT", "GB-WLS", "GB-NIR", "JE", "US", "AU", "NZ", "IE", "PK", "KE", "UG", "NR",
    "IN", "SG", "HK", "MY", "PH", "NG", "GH", "ZA", "TZ", "RW", "LR", "COMSEC", "CARICOM",
}
BIJURAL_CODES = {"CA", "ZA", "PH", "RW", "GB-SCT", "JE"}


def infer_tradition(g: dict) -> str:
    if g.get("legal_tradition"):
        return g["legal_tradition"]
    level = g.get("jurisdiction_level", "national")
    code = g.get("country_code", "")
    if level == "supranational":
        return "supranational"
    if level == "international":
        return "international"
    if code == "CA":
        return "bijural"
    if code in COMMON_LAW_CODES:
        return "common_law"
    return "civil_law"


def recency_key(last_updated) -> str:
    """Sortable form of last_updated: "YYYY-MM-DD" (missing parts as 00),
    "9999" for online texts maintained without dated editions, "" when unknown."""
    if last_updated is None:
        return ""
    m = re.match(r"^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?$", str(last_updated).strip())
    if m:
        return f"{m.group(1)}-{m.group(2) or '00'}-{m.group(3) or '00'}"
    return "9999"


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
        g["legal_tradition"] = infer_tradition(g)
        g["recency"] = recency_key(g.get("last_updated"))
    level_order = {"supranational": 0, "international": 1, "national": 2, "subnational": 3}
    catalog.sort(key=lambda g: (level_order.get(g["jurisdiction_level"], 9), g["jurisdiction"], g["title"]))
    return catalog


def load_matrix() -> dict:
    matrix_path = ROOT / "data" / "comparative_matrix.yml"
    if matrix_path.exists():
        return yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
    return {"jurisdictions": [], "dimensions": []}


def sort_key(text: str) -> str:
    """Accent- and case-insensitive key for alphabetical ordering."""
    return "".join(c for c in unicodedata.normalize("NFD", text) if not unicodedata.combining(c)).casefold()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def export_catalog(catalog: list[dict]) -> None:
    fields = [
        "id", "title", "title_en", "jurisdiction", "jurisdiction_level", "legal_tradition", "country_code",
        "region", "issuing_body", "languages", "document_type", "legal_status", "edition", "published",
        "last_updated", "currency_status", "currency_note", "checked_on", "original_format", "source_url",
        "landing_url", "license", "retrieved_at", "stored_format", "sha256",
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
    matrix = load_matrix()
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copytree(SRC / "assets", DIST / "assets")

    env = Environment(loader=FileSystemLoader(SRC / "templates"), autoescape=select_autoescape(["html", "xml"]))
    common = {
        "site": SITE,
        "built": dt.date.today().isoformat(),
        "catalog": catalog,
        "matrix": matrix,
        "status_labels": STATUS_LABELS,
    }

    facets = {
        "regions": sorted({g["region"] for g in catalog}),
        "levels": sorted({g["jurisdiction_level"] for g in catalog}),
        "traditions": sorted({g["legal_tradition"] for g in catalog}),
        "statuses": [s for s in STATUS_LABELS if any(g.get("currency", {}).get("status") == s for g in catalog)],
        "languages": sorted({name for g in catalog for name in g["language_names"]}),
    }
    stats = {
        "documents": len(catalog),
        "jurisdictions": len({g["jurisdiction"] for g in catalog}),
        "converted": sum(1 for g in catalog if g["content"]),
        "stored": sum(1 for g in catalog if g["stored_original"]),
    }
    catalog_az = sorted(catalog, key=lambda g: (sort_key(g["jurisdiction"]), sort_key(g["title"])))
    for name in ["index.html", "compare.html", "auditor.html", "search.html", "contribute.html", "about.html", "opensearch.xml"]:
        tpl = env.get_template(name)
        write(DIST / name, tpl.render(**common, base="", facets=facets, stats=stats, catalog_az=catalog_az, page=name))

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

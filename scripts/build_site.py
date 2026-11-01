#!/usr/bin/env python3
"""Build the static site into dist/.

Reads data/guidelines.yml, data/retrieval.json, data/comparative_matrix.yml and
the converted documents in documents/<id>/ and writes:

    dist/index.html                    landing page: search box, guidelines by country (with sub-national
                                       navigation) and A-Z filterable list
    dist/compare.html                  cross-jurisdictional comparative matrix
    dist/auditor.html                  interactive bill drafting compliance auditor (1-10 score)
    dist/guidelines/<id>/index.html    one page per guideline: metadata, contents, full text
    dist/guidelines/<id>/original.*    stored copy of the original document
    dist/search.html                   full-text search (Pagefind index built afterwards)
    dist/contribute.html               submission form for missing guidelines
    dist/about.html                    method and field definitions
    dist/catalog.json, catalog.csv     machine-readable catalog
    dist/opensearch.xml                OpenSearch description, so browsers can add the site as a search engine
    dist/sitemap.xml, robots.txt       page list for search engines

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
from urllib.parse import urlparse
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog import load_catalog  # noqa: E402
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "site_src"
DIST = ROOT / "dist"
DOCS = ROOT / "documents"

SITE = {
    "title": "Legislative Drafting Guidelines",
    "subtitle": "National, sub-national and supranational drafting manuals, collected and converted to HTML",
    "repo": os.environ.get("SITE_REPO", "aih/legislative-guidelines"),
    "url": os.environ.get("SITE_URL", "https://legdraft.linkedlegislation.org/"),
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

# Country names for countries that have sub-national entries but no national entry
# (otherwise the name is taken from the national entry's `jurisdiction`).
COUNTRY_NAMES = {
    "US": "United States", "CA": "Canada", "AU": "Australia", "GB": "United Kingdom", "IN": "India",
    "DE": "Germany", "AT": "Austria", "CH": "Switzerland", "BE": "Belgium", "ES": "Spain", "IT": "Italy",
    "BR": "Brazil", "AR": "Argentina", "MX": "Mexico", "NG": "Nigeria", "ZA": "South Africa", "MY": "Malaysia",
    "PK": "Pakistan", "CN": "China", "RU": "Russia", "KE": "Kenya", "ET": "Ethiopia", "NZ": "New Zealand",
    "FR": "France", "PT": "Portugal", "FI": "Finland", "DK": "Denmark", "BA": "Bosnia and Herzegovina",
}

SECTION_ORDER = ["International & supranational", "Africa", "Americas", "Asia", "Europe", "Oceania"]

PLURALS = {"land": "Länder", "devolved nation": "devolved nations"}


def plural(noun: str) -> str:
    if noun in PLURALS:
        return PLURALS[noun]
    if noun.endswith("y") and not noun.endswith(("ay", "ey", "oy")):
        return noun[:-1] + "ies"
    return noun + "s"


def subdivision_label(types: list[str]) -> str:
    """Navigation label from the subdivision types present, e.g. "States & territories"."""
    names = []
    for t in types:
        if plural(t) not in names:
            names.append(plural(t))
    label = " & ".join(names[:2]) + (" & other" if len(names) > 2 else "")
    return label[:1].upper() + label[1:]


def infer_tradition(g: dict) -> str:
    if g.get("legal_tradition"):
        return g["legal_tradition"]
    level = g.get("jurisdiction_level", "national")
    code = g.get("subdivision_code") or g.get("country_code", "")
    if level == "supranational":
        return "supranational"
    if level == "international":
        return "international"
    if code == "CA":
        return "bijural"
    if code in COMMON_LAW_CODES or g.get("country_code") in COMMON_LAW_CODES:
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
    catalog = load_catalog()
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
    names = {g["country_code"]: g["jurisdiction"] for g in catalog if g["jurisdiction_level"] != "subnational"}
    for g in catalog:
        g["country_name"] = names.get(g["country_code"]) or COUNTRY_NAMES.get(g["country_code"], g["country_code"])
        g["display_jurisdiction"] = (f"{g['jurisdiction']} ({g['country_name']})"
                                     if g["jurisdiction_level"] == "subnational" else g["jurisdiction"])
        url = g.get("source_url") or g.get("landing_url") or ""
        host = urlparse(url).netloc.lower()
        g["host"] = host[4:] if host.startswith("www.") else host
    level_order = {"supranational": 0, "international": 1, "national": 2, "subnational": 3}
    catalog.sort(key=lambda g: (level_order.get(g["jurisdiction_level"], 9), g["jurisdiction"], g["title"]))
    return catalog


def build_groups(catalog: list[dict]) -> list[dict]:
    """One group per country or organisation (keyed by country_code), with its
    national entries and its sub-national entries grouped by subdivision."""
    groups: dict[str, dict] = {}
    for g in catalog:
        code = g["country_code"]
        grp = groups.setdefault(code, {"code": code, "name": g["country_name"], "kind": "country",
                                       "region": g["region"], "national": [], "subs": {}})
        if g["jurisdiction_level"] in ("supranational", "international"):
            grp["kind"] = "organisation"
        if g["jurisdiction_level"] == "subnational":
            sub = grp["subs"].setdefault(g["subdivision_code"], {
                "code": g["subdivision_code"], "name": g["jurisdiction"],
                "type": g.get("subdivision_type", "subdivision"), "entries": []})
            sub["entries"].append(g)
        else:
            grp["national"].append(g)
            grp["region"] = g["region"]
    out = []
    for grp in groups.values():
        grp["section"] = "International & supranational" if grp["kind"] == "organisation" else grp["region"]
        grp["national"].sort(key=lambda g: sort_key(g["title"]))
        subs = sorted(grp["subs"].values(), key=lambda s: sort_key(s["name"]))
        for s in subs:
            s["entries"].sort(key=lambda g: sort_key(g["title"]))
        grp["subs"] = subs
        grp["sub_count"] = sum(len(s["entries"]) for s in subs)
        type_counts: dict[str, int] = {}
        for s in subs:
            type_counts[s["type"]] = type_counts.get(s["type"], 0) + 1
        types = sorted(type_counts, key=lambda t: -type_counts[t])
        grp["sub_label"] = subdivision_label(types) if types else ""
        grp["total"] = len(grp["national"]) + grp["sub_count"]
        out.append(grp)
    out.sort(key=lambda grp: (SECTION_ORDER.index(grp["section"]) if grp["section"] in SECTION_ORDER else 99,
                              sort_key(grp["name"])))
    return out


def group_sections(groups: list[dict]) -> list[dict]:
    sections: list[dict] = []
    for grp in groups:
        if not sections or sections[-1]["name"] != grp["section"]:
            sections.append({"name": grp["section"], "groups": []})
        sections[-1]["groups"].append(grp)
    return sections


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
        "subdivision_code", "subdivision_type",
        "region", "issuing_body", "languages", "document_type", "legal_status", "edition", "published",
        "last_updated", "currency_status", "currency_note", "checked_on", "original_format", "source_url",
        "landing_url", "license", "credits", "retrieved_at", "stored_format", "sha256",
    ]
    rows = []
    for g in catalog:
        cur = g.get("currency", {})
        ret = g["retrieval"]
        rows.append(
            {
                **{k: g.get(k) for k in fields if k in g},
                "languages": ", ".join(g.get("languages", [])),
                "credits": "; ".join(c["name"] for c in g.get("credits", [])),
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
        "groups": len({g["country_code"] for g in catalog}),
        "subdivisions": len({g["subdivision_code"] for g in catalog if g.get("subdivision_code")}),
        "converted": sum(1 for g in catalog if g["content"]),
        "stored": sum(1 for g in catalog if g["stored_original"]),
    }
    catalog_az = sorted(catalog, key=lambda g: (sort_key(g["display_jurisdiction"]), sort_key(g["title"])))
    groups = build_groups(catalog)
    sections = group_sections(groups)
    for name in ["index.html", "compare.html", "auditor.html", "search.html", "contribute.html", "about.html", "opensearch.xml"]:
        tpl = env.get_template(name)
        write(DIST / name, tpl.render(**common, base="", facets=facets, stats=stats, catalog_az=catalog_az,
                                           groups=groups, sections=sections, page=name))

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
    pages = ["index.html", "search.html", "compare.html", "auditor.html", "about.html", "contribute.html"]
    pages += [f"guidelines/{g['id']}/index.html" for g in catalog]
    urls = "".join(f"  <url><loc>{SITE['url']}{path}</loc></url>\n" for path in pages)
    write(DIST / "sitemap.xml",
          f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
    write(DIST / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE['url']}sitemap.xml\n")
    print(f"built {len(catalog)} guideline pages into {DIST.relative_to(ROOT)}/ "
          f"({stats['converted']} with converted text, {stats['stored']} with stored originals)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Export the guidelines as OpenSearch documents, one per section.

Each converted document is split at its headings; every section becomes one
OpenSearch document carrying the guideline's metadata, the section title, the
heading path and the section text.

Usage:
    python scripts/export_opensearch.py                      # writes dist/opensearch-bulk.ndjson
    python scripts/export_opensearch.py --load URL           # also creates the index and bulk-loads it
    python scripts/export_opensearch.py --load URL --index legislative-guidelines
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests
import yaml
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "documents"
MAPPING = ROOT / "opensearch" / "index-mapping.json"
HEADINGS = {"h2", "h3", "h4", "h5"}


def sections(content_html: str):
    """Yield (section_id, title, path, text) for each heading-delimited section."""
    soup = BeautifulSoup(content_html, "lxml")
    root = soup.body or soup
    path: list[tuple[int, str]] = []
    current = {"id": "", "title": "", "path": "", "text": []}
    for el in root.find_all(True, recursive=True):
        if el.name in HEADINGS:
            if current["text"]:
                yield current["id"], current["title"], current["path"], "\n".join(current["text"])
            level = int(el.name[1])
            title = el.get_text(" ", strip=True)
            path = [p for p in path if p[0] < level] + [(level, title)]
            current = {"id": el.get("id", ""), "title": title, "path": " › ".join(t for _, t in path), "text": []}
        elif el.name in {"p", "li", "td", "th", "pre", "blockquote"} and not el.find(["p", "li"]):
            text = el.get_text(" ", strip=True)
            if text:
                current["text"].append(text)
    if current["text"]:
        yield current["id"], current["title"], current["path"], "\n".join(current["text"])


def documents(page_base: str):
    catalog = yaml.safe_load((ROOT / "data" / "guidelines.yml").read_text(encoding="utf-8"))
    for g in catalog:
        meta = {
            "guideline_id": g["id"],
            "title": g["title"],
            "title_en": g.get("title_en"),
            "jurisdiction": g["jurisdiction"],
            "jurisdiction_level": g["jurisdiction_level"],
            "country_code": g.get("country_code"),
            "region": g.get("region"),
            "issuing_body": g.get("issuing_body"),
            "languages": g.get("languages", []),
            "document_type": g.get("document_type"),
            "legal_status": g.get("legal_status"),
            "edition": g.get("edition"),
            "last_updated": str(g.get("last_updated") or ""),
            "currency_status": g.get("currency", {}).get("status"),
            "original_format": g.get("original_format"),
            "source_url": g.get("source_url"),
        }
        page = f"{page_base}guidelines/{g['id']}/index.html"
        content = DOCS / g["id"] / "content.html"
        if not content.exists():
            yield f"{g['id']}--meta", {**meta, "page_url": page, "body": g.get("currency", {}).get("note") or ""}
            continue
        for n, (sid, title, path, text) in enumerate(sections(content.read_text(encoding="utf-8"))):
            yield f"{g['id']}--{n:04d}", {
                **meta,
                "page_url": f"{page}#{sid}" if sid else page,
                "section_id": sid,
                "section_title": title,
                "section_path": path,
                "body": text,
            }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--index", default="legislative-guidelines")
    ap.add_argument("--load", metavar="URL", help="OpenSearch base URL to create the index in and load")
    ap.add_argument("--page-base", default="https://aih.github.io/legislative-guidelines/")
    ap.add_argument("--out", default=str(ROOT / "dist" / "opensearch-bulk.ndjson"))
    args = ap.parse_args()

    lines = []
    for doc_id, doc in documents(args.page_base):
        lines.append(json.dumps({"index": {"_index": args.index, "_id": doc_id}}))
        lines.append(json.dumps(doc, ensure_ascii=False))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {len(lines) // 2} documents to {out}")

    if args.load:
        base = args.load.rstrip("/")
        requests.delete(f"{base}/{args.index}", timeout=30)
        r = requests.put(f"{base}/{args.index}", json=json.loads(MAPPING.read_text()), timeout=30)
        r.raise_for_status()
        batch = 1000  # action+source pairs per request
        for i in range(0, len(lines), batch * 2):
            chunk = "\n".join(lines[i : i + batch * 2]) + "\n"
            r = requests.post(f"{base}/_bulk", data=chunk.encode("utf-8"),
                              headers={"Content-Type": "application/x-ndjson"}, timeout=120)
            r.raise_for_status()
            if r.json().get("errors"):
                print("bulk load reported errors", file=sys.stderr)
                return 1
        print(f"loaded into {base}/{args.index}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

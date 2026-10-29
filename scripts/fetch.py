#!/usr/bin/env python3
"""Download the original guideline documents listed in data/guidelines.yml.

Each document is saved under documents/<id>/original.<ext>. Retrieval details
(date, final URL, HTTP status, content type, size, SHA-256) are written to
data/retrieval.json so the hand-maintained catalog stays untouched.

Entries with a `crawl` block are multi-page HTML guides: pages linked from the
source URL whose URL starts with `crawl.prefix` are saved as
documents/<id>/pages/NNN.html, in link order.

Usage:
    python scripts/fetch.py               # fetch everything not yet retrieved
    python scripts/fetch.py --force       # re-download everything
    python scripts/fetch.py eu-joint-practical-guide fr-guide-de-legistique
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import mimetypes
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urldefrag

import requests
import yaml
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data" / "guidelines.yml"
RETRIEVAL = ROOT / "data" / "retrieval.json"
DOCS = ROOT / "documents"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36 legislative-guidelines-collector"
    ),
    "Accept-Language": "en,fr;q=0.8,de;q=0.7,*;q=0.5",
}

EXT_BY_TYPE = {
    "application/pdf": ".pdf",
    "text/html": ".html",
    "application/xhtml+xml": ".html",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.oasis.opendocument.text": ".odt",
    "application/rtf": ".rtf",
}


def load_catalog() -> list[dict]:
    return yaml.safe_load(CATALOG.read_text(encoding="utf-8"))


def load_retrieval() -> dict:
    if RETRIEVAL.exists():
        return json.loads(RETRIEVAL.read_text(encoding="utf-8"))
    return {}


def save_retrieval(data: dict) -> None:
    RETRIEVAL.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def guess_ext(resp: requests.Response, url: str) -> str:
    ctype = resp.headers.get("Content-Type", "").split(";")[0].strip().lower()
    if ctype in EXT_BY_TYPE:
        return EXT_BY_TYPE[ctype]
    if resp.content[:4] == b"%PDF":
        return ".pdf"
    if resp.content[:2] == b"PK":
        return ".docx"
    if resp.content[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        return ".doc"
    path_ext = Path(url.split("?")[0]).suffix.lower()
    if path_ext in {".pdf", ".html", ".htm", ".doc", ".docx", ".odt", ".rtf"}:
        return ".html" if path_ext == ".htm" else path_ext
    return mimetypes.guess_extension(ctype) or ".bin"


def get(session: requests.Session, url: str) -> requests.Response:
    last = None
    for attempt in range(3):
        try:
            resp = session.get(url, headers=HEADERS, timeout=90, allow_redirects=True)
            return resp
        except requests.RequestException as exc:  # network hiccup: back off and retry
            last = exc
            time.sleep(2 ** (attempt + 1))
    raise last  # type: ignore[misc]


def _norm(url: str) -> str:
    return url.replace("://www.", "://").replace("http://", "https://")


def crawl(session: requests.Session, entry: dict, index_html: bytes, base_url: str, out_dir: Path) -> list[dict]:
    prefix = entry["crawl"]["prefix"]
    limit = entry["crawl"].get("limit", 300)
    soup = BeautifulSoup(index_html, "lxml")
    ordered: list[str] = []
    pages = []
    for a in soup.find_all("a", href=True):
        url = urldefrag(urljoin(base_url, a["href"]))[0]
        if not _norm(url).startswith(_norm(prefix)) or url in ordered or _norm(url) == _norm(base_url):
            continue
        ordered.append(url)
        if len(ordered) >= limit:
            break
    pages_dir = out_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    for i, url in enumerate(ordered, start=1):
        try:
            resp = get(session, url)
        except requests.RequestException as exc:
            pages.append({"url": url, "error": str(exc)})
            continue
        name = f"{i:03d}.html"
        (pages_dir / name).write_bytes(resp.content)
        pages.append({"url": url, "file": f"pages/{name}", "status": resp.status_code})
        time.sleep(0.5)
    return pages


def fetch_entry(session: requests.Session, entry: dict) -> dict:
    url = entry.get("source_url")
    record: dict = {"retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    if not url:
        record["error"] = "no source_url in catalog"
        return record
    try:
        resp = get(session, url)
    except requests.RequestException as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
        return record
    record.update(
        {
            "requested_url": url,
            "final_url": resp.url,
            "http_status": resp.status_code,
            "content_type": resp.headers.get("Content-Type", ""),
            "last_modified_header": resp.headers.get("Last-Modified"),
        }
    )
    if resp.status_code >= 400:
        record["error"] = f"HTTP {resp.status_code}"
        return record
    out_dir = DOCS / entry["id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("original.*"):
        old.unlink()
    ext = guess_ext(resp, resp.url)
    target = out_dir / f"original{ext}"
    target.write_bytes(resp.content)
    record.update(
        {
            "file": str(target.relative_to(ROOT)),
            "format": ext.lstrip(".").upper(),
            "bytes": len(resp.content),
            "sha256": hashlib.sha256(resp.content).hexdigest(),
        }
    )
    if entry.get("crawl") and ext == ".html":
        record["pages"] = crawl(session, entry, resp.content, resp.url, out_dir)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ids", nargs="*", help="only fetch these catalog ids")
    parser.add_argument("--force", action="store_true", help="re-download documents already retrieved")
    args = parser.parse_args()

    catalog = load_catalog()
    retrieval = load_retrieval()
    session = requests.Session()
    failures = 0
    for entry in catalog:
        gid = entry["id"]
        if args.ids and gid not in args.ids:
            continue
        if not args.force and not args.ids and retrieval.get(gid, {}).get("sha256"):
            continue
        record = fetch_entry(session, entry)
        retrieval[gid] = record
        status = record.get("error") or f"{record['format']} {record['bytes']:,} bytes"
        print(f"{gid:50s} {status}")
        failures += bool(record.get("error"))
        save_retrieval(retrieval)
    print(f"done; {failures} failure(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

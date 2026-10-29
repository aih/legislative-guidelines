#!/usr/bin/env python3
"""Convert downloaded originals into structured HTML.

For every document under documents/<id>/ this writes:
    content.html   an HTML fragment with h2-h5 headings, paragraphs, lists and tables
    toc.json       [{"id", "level", "title"}] for the page's table of contents
    text.txt       plain text, used for the OpenSearch export

Conversion by source format:
    PDF        PyMuPDF layout analysis: font-size ranks become heading levels,
               running headers/footers and page numbers are dropped, lines are
               joined into paragraphs, and list items are kept as list items.
    HTML       main content region extracted; navigation, scripts and chrome removed.
               Multi-page crawls (documents/<id>/pages/) are concatenated in order.
    DOCX/ODT   pandoc.
    DOC/RTF    LibreOffice to DOCX, then pandoc.

Usage:
    python scripts/convert.py [ids...]
"""
from __future__ import annotations

import collections
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import fitz  # PyMuPDF
from bs4 import BeautifulSoup, Comment

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "documents"

LIST_MARKER = re.compile(
    r"^\s*(?:[•●▪◦‣∙·–—-]|\(?[a-zA-Z]\)|\(?[ivxlcdm]{1,6}\)|\(?\d{1,3}[.)]|\d{1,3}\.\d+(?:\.\d+)*\.?)\s+"
)
NUMERAL_ONLY = re.compile(r"^\W*\d{1,3}\W*$")
INVISIBLE = re.compile(r"[\ufeff\u200b\u200c\u200d\u00ad]")
SECTION_NUMBER = re.compile(r"^(?:\d+(?:\.\d+)+\.?|[A-Z]\.|\d+\.|Chapter\s|Part\s|Article\s|Section\s)\s*", re.I)
RUNNING_HEAD = re.compile(r"^\s*(?:[\divxlc]{1,4}\s+\S.{0,90}|\S.{0,90}\s+[\divxlc]{1,4})\s*$", re.I)
PAGE_NUMBER = re.compile(r"^\s*(?:page\s+)?[\divxlcdm]{1,5}(?:\s*(?:/|of)\s*\d+)?\s*$", re.I)


def slugify(text: str, used: set[str]) -> str:
    base = re.sub(r"[^\w]+", "-", text.lower(), flags=re.UNICODE).strip("-")[:60] or "section"
    slug, n = base, 2
    while slug in used:
        slug, n = f"{base}-{n}", n + 1
    used.add(slug)
    return slug


# --------------------------------------------------------------------------- PDF


def _pdf_lines(doc: fitz.Document) -> list[dict]:
    """Return one record per visual line: text, size, bold, x0, y0, y1, page."""
    lines = []
    for pno, page in enumerate(doc):
        height = page.rect.height
        for block in page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]:
            for line in block.get("lines", []):
                spans = [s for s in line["spans"] if s["text"].strip()]
                if not spans:
                    continue
                text = INVISIBLE.sub("", "".join(s["text"] for s in line["spans"])).strip()
                if not text:
                    continue
                chars = sum(len(s["text"].strip()) for s in spans)
                size = sum(s["size"] * len(s["text"].strip()) for s in spans) / max(chars, 1)
                bold_chars = sum(
                    len(s["text"].strip()) for s in spans if s["flags"] & 16 or "bold" in s["font"].lower()
                )
                x0, y0, x1, y1 = line["bbox"]
                lines.append(
                    {
                        "text": re.sub(r"\s+", " ", text),
                        "size": round(size, 1),
                        "bold": bold_chars >= 0.8 * chars,
                        "x0": x0,
                        "y0": y0,
                        "y1": y1,
                        "page": pno,
                        "rel_y": y0 / height,
                    }
                )
    return _merge_same_baseline(lines)


def _merge_same_baseline(lines: list[dict]) -> list[dict]:
    """PyMuPDF sometimes splits one visual line into several; join them."""
    merged: list[dict] = []
    for ln in lines:
        prev = merged[-1] if merged else None
        if prev and prev["page"] == ln["page"] and abs(prev["y0"] - ln["y0"]) < 1.5 and ln["x0"] > prev["x0"]:
            prev["text"] = f'{prev["text"]} {ln["text"]}'
            prev["bold"] = prev["bold"] and ln["bold"]
            continue
        merged.append(dict(ln))
    return merged


def _furniture(lines: list[dict], pages: int) -> set[str]:
    """Text repeated in the top or bottom margin of many pages (running heads/feet)."""
    if pages < 4:
        return set()
    counts: collections.Counter[str] = collections.Counter()
    for ln in lines:
        if ln["rel_y"] < 0.08 or ln["rel_y"] > 0.92:
            counts[re.sub(r"\d+", "#", ln["text"].lower())] += 1
    return {t for t, c in counts.items() if c >= max(3, pages * 0.25)}


def _mode_size(lines: list[dict]) -> float:
    weight: collections.Counter[float] = collections.Counter()
    for ln in lines:
        weight[ln["size"]] += len(ln["text"])
    return weight.most_common(1)[0][0]


def _heading_levels(lines: list[dict], body: float) -> dict[float, int]:
    """Map font sizes larger than body text to heading levels h2-h5.

    Sizes used on at least three pages get their own level, largest first.
    Rarer, larger sizes (title pages, cover text) share the level of the next
    frequent size above them, or h2.
    """
    size_pages = {(ln["size"], ln["page"]) for ln in lines if ln["size"] >= body + 0.9 and len(ln["text"]) < 200}
    count: collections.Counter[float] = collections.Counter(size for size, _ in size_pages)
    frequent = sorted((s for s, c in count.items() if c >= 3), reverse=True)[:4]
    levels = {s: 2 + i for i, s in enumerate(frequent)}
    for s in count:
        if s not in levels:
            above = [f for f in frequent if f > s]
            levels[s] = levels[above[-1]] if above else 2
    return levels


def convert_pdf(path: Path) -> tuple[str, list[dict], str]:
    doc = fitz.open(path)
    lines = _pdf_lines(doc)
    furniture = _furniture(lines, len(doc))
    lines = [
        ln
        for ln in lines
        if not (
            (ln["rel_y"] < 0.08 or ln["rel_y"] > 0.92)
            and (
                re.sub(r"\d+", "#", ln["text"].lower()) in furniture
                or PAGE_NUMBER.match(ln["text"])
                or RUNNING_HEAD.match(ln["text"])
            )
        )
    ]
    if not lines:
        return "<p><em>No extractable text (the PDF may be scanned images).</em></p>", [], ""

    # decorative numerals (chapter tabs, drop caps) are not content
    lines = [ln for ln in lines if not (NUMERAL_ONLY.match(ln["text"]) and ln["size"] >= _mode_size(lines) + 3)]
    body = _mode_size(lines)
    level_for = _heading_levels(lines, body)
    bold_level = min(2 + len(set(level_for.values())), 5)

    left_margin = collections.Counter(round(ln["x0"]) for ln in lines if ln["size"] == body).most_common(1)[0][0]

    blocks: list[tuple[str, str]] = []  # (kind, text) kind in h2..h5, p, li
    used: set[str] = set()
    toc: list[dict] = []
    para: list[str] = []
    para_kind = "p"
    prev = None

    def flush():
        nonlocal para, para_kind
        if para:
            text = " ".join(para)
            text = re.sub(r"(\w)- (\w)", r"\1\2", text)  # rejoin hyphenated line breaks
            blocks.append((para_kind, text))
        para, para_kind = [], "p"

    for ln in lines:
        text = ln["text"]
        level = level_for.get(ln["size"])
        if (
            level is None
            and ln["bold"]
            and ln["size"] >= body - 0.5
            and len(text) < 120
            and not text.endswith((".", ",", ";"))
            and not LIST_MARKER.match(text)
        ):
            level = bold_level
        if level is not None and len(text) < 200:
            # consecutive heading lines of the same size form one heading
            if (
                blocks
                and prev is not None
                and blocks[-1][0] == f"h{level}"
                and not para
                and prev["page"] == ln["page"]
                and ln["y0"] - prev["y1"] < ln["size"]
                and not SECTION_NUMBER.match(text)
            ):
                kind, prior = blocks.pop()
                blocks.append((kind, f"{prior} {text}"))
            else:
                flush()
                blocks.append((f"h{level}", text))
            prev = ln
            continue

        new_para = (
            prev is None
            or prev["page"] != ln["page"] and para and para[-1].endswith((".", ":", ";"))
            or prev["page"] == ln["page"] and ln["y0"] - prev["y1"] > max(ln["size"], prev["size"]) * 0.8
            or LIST_MARKER.match(text) is not None
            or ln["x0"] > left_margin + 15 and prev is not None and prev["x0"] <= left_margin + 2 and para and para[-1].endswith((".", ":", ";"))
        )
        if new_para:
            flush()
            para_kind = "li" if LIST_MARKER.match(text) else "p"
        para.append(text)
        prev = ln
    flush()

    out, plain = [], []
    in_list = False
    for kind, text in blocks:
        if kind == "li" and not in_list:
            out.append("<ul class=\"source-list\">")
            in_list = True
        elif kind != "li" and in_list:
            out.append("</ul>")
            in_list = False
        esc = html.escape(text)
        if kind.startswith("h"):
            slug = slugify(text, used)
            toc.append({"id": slug, "level": int(kind[1]), "title": text})
            out.append(f'<{kind} id="{slug}">{esc}</{kind}>')
        else:
            out.append(f"<{kind}>{esc}</{kind}>")
        plain.append(text)
    if in_list:
        out.append("</ul>")
    return "\n".join(out), toc, "\n\n".join(plain)


# --------------------------------------------------------------------------- HTML

MAIN_SELECTORS = [
    "main",
    "[role=main]",
    "#wb-cont",
    "#content",
    "#main-content",
    "article",
    ".govspeak",
    "#contenu",
    "#main",
    "body",
]
DROP_TAGS = ["script", "style", "noscript", "nav", "header", "footer", "form", "button", "iframe", "svg", "aside"]
DROP_SELECTORS = [".breadcrumb", "#wb-bc", ".pagedetails", "#wb-info", ".gc-subway", ".skip-link", ".cookie", "[aria-hidden=true]"]


def clean_html_fragment(raw: bytes | str, used: set[str], toc: list[dict], heading_offset: int = 0) -> tuple[str, str]:
    soup = BeautifulSoup(raw, "lxml")
    main = None
    for sel in MAIN_SELECTORS:
        main = soup.select_one(sel)
        if main and len(main.get_text(strip=True)) > 200:
            break
    if main is None:
        return "", ""
    for tag in main.find_all(DROP_TAGS):
        tag.decompose()
    for sel in DROP_SELECTORS:
        for tag in main.select(sel):
            tag.decompose()
    for c in main.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    allowed_attrs = {"href", "id", "colspan", "rowspan", "lang"}
    for tag in main.find_all(True):
        tag.attrs = {k: v for k, v in tag.attrs.items() if k in allowed_attrs}
        if tag.name in {"div", "span", "section", "font", "center"}:
            tag.unwrap()
    for a in main.find_all("a"):
        href = a.get("href", "")
        if href.startswith("#") or not href:
            a.unwrap()
    for h in main.find_all(re.compile(r"^h[1-6]$")):
        level = min(max(int(h.name[1]) + heading_offset, 2), 5)
        title = h.get_text(" ", strip=True)
        if not title:
            h.decompose()
            continue
        h.name = f"h{level}"
        h.attrs = {"id": slugify(title, used)}
        toc.append({"id": h["id"], "level": level, "title": title})
    fragment = main.decode_contents() if main.name in {"body", "main"} else str(main)
    text = main.get_text("\n", strip=True)
    return fragment, text


def convert_html_dir(doc_dir: Path, original: Path) -> tuple[str, list[dict], str]:
    used: set[str] = set()
    toc: list[dict] = []
    parts, texts = [], []
    frag, text = clean_html_fragment(original.read_bytes(), used, toc)
    pages = sorted((doc_dir / "pages").glob("*.html")) if (doc_dir / "pages").exists() else []
    if not pages:
        return frag, toc, text
    # with a crawl, the index page is only a table of contents; the pages carry the text
    for page in pages:
        frag, text = clean_html_fragment(page.read_bytes(), used, toc)
        if frag:
            parts.append(f'<section class="source-page">{frag}</section>')
            texts.append(text)
    return "\n".join(parts), toc, "\n\n".join(texts)


# --------------------------------------------------------------------------- Word


def convert_word(path: Path) -> tuple[str, list[dict], str]:
    src = path
    with tempfile.TemporaryDirectory() as tmp:
        if path.suffix.lower() in {".doc", ".rtf"}:
            subprocess.run(
                ["libreoffice", "--headless", "--convert-to", "docx", "--outdir", tmp, str(path)],
                check=True,
                capture_output=True,
                timeout=300,
            )
            src = Path(tmp) / (path.stem + ".docx")
        result = subprocess.run(
            ["pandoc", str(src), "-t", "html5", "--wrap=none"], check=True, capture_output=True, timeout=300
        )
    used: set[str] = set()
    toc: list[dict] = []
    frag, text = clean_html_fragment(f"<body>{result.stdout.decode('utf-8')}</body>", used, toc, heading_offset=1)
    return frag, toc, text


# --------------------------------------------------------------------------- driver


def convert(doc_dir: Path) -> str:
    originals = sorted(doc_dir.glob("original.*"))
    if not originals:
        return "no original"
    original = originals[0]
    ext = original.suffix.lower()
    if ext == ".pdf":
        content, toc, text = convert_pdf(original)
    elif ext == ".html":
        content, toc, text = convert_html_dir(doc_dir, original)
    elif ext in {".docx", ".odt", ".doc", ".rtf"}:
        content, toc, text = convert_word(original)
    else:
        return f"unsupported format {ext}"
    (doc_dir / "content.html").write_text(content, encoding="utf-8")
    (doc_dir / "toc.json").write_text(json.dumps(toc, indent=1, ensure_ascii=False), encoding="utf-8")
    (doc_dir / "text.txt").write_text(text, encoding="utf-8")
    return f"{ext[1:].upper()}: {len(toc)} headings, {len(text):,} chars"


def main(argv: list[str]) -> int:
    ids = set(argv)
    for doc_dir in sorted(p for p in DOCS.iterdir() if p.is_dir()):
        if ids and doc_dir.name not in ids:
            continue
        try:
            status = convert(doc_dir)
        except Exception as exc:  # keep going; report per document
            status = f"FAILED {type(exc).__name__}: {exc}"
        print(f"{doc_dir.name:50s} {status}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

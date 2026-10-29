# Legislative Drafting Guidelines

A collection of the legislative drafting guidelines of national legislatures and governments and of supranational and
international bodies, with metadata on each document's issuer, edition, currency, original format and source, and the
full text converted to HTML. It follows the approach of the
[Commonwealth Legislative Drafting Manual](https://github.com/aih/commonwealth-leg-drafting-manual) web edition,
extended to many documents.

Site: <https://aih.github.io/legislative-guidelines/> (deployed from `main` by GitHub Actions).

## Layout

| Path | Contents |
|---|---|
| `data/guidelines.yml` | The catalog: one entry per guideline. Fields are documented in [`data/SCHEMA.md`](data/SCHEMA.md). |
| `data/retrieval.json` | Download record per document: date, final URL, HTTP status, size, SHA-256. |
| `documents/<id>/original.*` | Stored copy of the original document as published. |
| `documents/<id>/content.html`, `toc.json`, `text.txt` | Converted HTML, table of contents and plain text. |
| `scripts/fetch.py` | Downloads originals listed in the catalog. |
| `scripts/convert.py` | Converts PDF, HTML and Word originals to structured HTML. |
| `scripts/build_site.py` | Generates the static site in `dist/`. |
| `scripts/export_opensearch.py` | Writes an OpenSearch bulk file (one document per section) and optionally loads it. |
| `opensearch/` | OpenSearch index mapping and a local `docker-compose.yml`. |
| `site_src/` | Site templates, CSS and JavaScript. |
| `research/backlog.md` | Guidelines identified but not yet catalogued. |

## Building locally

```sh
pip install -r requirements.txt          # also needs pandoc and LibreOffice for Word files
python scripts/fetch.py                  # download originals not yet stored
python scripts/convert.py                # documents/<id>/content.html
python scripts/build_site.py             # dist/
npx -y pagefind@1.3.0 --site dist        # full-text search index
python -m http.server -d dist 8000
```

## Search

The site's search uses [Pagefind](https://pagefind.app/), a static index built at deploy time, so it runs on GitHub
Pages without a server. Pages carry Pagefind filters for jurisdiction, level, region, language and currency.
The site also publishes an `opensearch.xml` description so browsers can add it as a search engine.

To run the same content in OpenSearch:

```sh
docker compose -f opensearch/docker-compose.yml up -d
python scripts/export_opensearch.py --load http://localhost:9200
```

The index (`legislative-guidelines`) holds one document per section with the guideline's metadata, the heading path
and the section text; OpenSearch Dashboards runs on port 5601.

## Submissions

The site's [Submit a guideline](https://aih.github.io/legislative-guidelines/contribute.html) form opens a pre-filled
GitHub issue using `.github/ISSUE_TEMPLATE/submit-guideline.yml`. Setting the `FORM_ENDPOINT` environment variable at
build time to a Formspree-compatible endpoint sends submissions there instead.

## Adding a guideline

1. Add an entry to `data/guidelines.yml`.
2. `python scripts/fetch.py <id> && python scripts/convert.py <id>`
3. Commit `data/`, `documents/<id>/` and open a pull request.

## Rights

Each document remains the work of its issuing body; the licence or reuse terms recorded for each entry are shown on
its page. The converted HTML is produced automatically and may contain conversion errors; the original document is
always linked.

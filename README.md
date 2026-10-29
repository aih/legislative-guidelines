# Legislative Drafting Guidelines

A comprehensive collection of the legislative drafting guidelines of national legislatures, devolved governments, and supranational and international bodies, with structured metadata on each document's issuer, legal tradition, edition, currency, original format, and source, the full text converted to navigable HTML, a cross-jurisdictional comparative matrix, and an interactive **Bill & Act Drafting Compliance Auditor**.

It follows and extends the approach of the [Commonwealth Legislative Drafting Manual](https://github.com/aih/commonwealth-leg-drafting-manual) web edition across 80+ national and international instruments.

Site: <https://legdraft.linkedlegislation.org/> (deployed from `main` by GitHub Actions; see [Deployment](#deployment)).

## Key Features

- **Global Catalog (`index.html`)**: Filter by jurisdiction, governance level (`supranational`, `international`, `national`, `subnational`), legal tradition (`common_law`, `civil_law`, `bijural`, `supranational`, `international`), region, language, and currency status.
- **Bill & Act Drafting Compliance Auditor (`auditor.html` & `scripts/evaluate_bill.py`)**: Upload a drafted bill or statutory clauses (`.txt`, `.md`, `.xml` Akoma Ntoso / USLM, `.html`) or load sample bills, select one or more target guidelines, and receive:
  - A **1–10 overall compliance score** and 5 dimensional sub-scores (*Clarity & Plain Language*, *Normative Verbs & Precision*, *Definitions & Cross-References*, *Guideline Conventions*, *Structural Organization*).
  - A **rule-by-rule checklist (`PASS` / `WARN` / `FAIL`)** with citations to the official drafting manual.
  - **Verbatim flagged provisions** with explanations and concrete **proposed redrafts**.
  - **Side-by-side multi-jurisdiction comparison** showing how the same bill scores across different jurisdictions (e.g., why `"shall"` passes EU/US rules but triggers warnings under UK, Canadian, Australian, and New Zealand guidelines).
  - Works 100% client-side on GitHub Pages with optional live AI Counsel critique (Gemini / OpenAI) and a standalone Python CLI / HTTP API server.
- **Cross-Jurisdictional Comparative Matrix (`compare.html`)**: Side-by-side comparison of how 10 benchmark authorities handle modal verbs (`shall` vs `must` vs present indicative), definitions hygiene, recitals/preambles, gender-neutral drafting, sentence structure, amending techniques, and digital-ready / automated decision-making legislation.
- **Full-Text Search (`search.html` & OpenSearch)**: Browser-based full-text search via [Pagefind](https://pagefind.app/) with jurisdiction, level, region, language, and currency facets, plus bulk export (`scripts/export_opensearch.py`) for OpenSearch.

## Layout

| Path | Contents |
|---|---|
| `data/guidelines.yml` | The catalog: one entry per guideline. Fields are documented in [`data/SCHEMA.md`](data/SCHEMA.md). |
| `data/guidelines.schema.json` | Formal JSON Schema (Draft 2020-12) validating `data/guidelines.yml`. |
| `data/comparative_matrix.yml` | Cross-jurisdictional comparative matrix data across 10 benchmark drafting manuals. |
| `data/retrieval.json` | Download record per document: date, final URL, HTTP status, size, SHA-256, or the error. |
| `documents/<id>/original.*` | Downloaded original. Kept locally; not committed. |
| `documents/<id>/content.html`, `toc.json` | Converted HTML and table of contents. Committed. `text.txt` is kept locally. |
| `scripts/validate_catalog.py` | Validates `data/guidelines.yml` against `data/guidelines.schema.json`. |
| `scripts/evaluate_bill.py` | CLI and local HTTP API engine for evaluating draft bills against guidelines (1–10 score). |
| `scripts/fetch.py` | Downloads originals listed in the catalog. |
| `scripts/convert.py` | Converts PDF, HTML and Word originals to structured HTML. |
| `scripts/build_site.py` | Generates the static site in `dist/`. |
| `scripts/export_opensearch.py` | Writes an OpenSearch bulk file (one document per section) and optionally loads it. |
| `site_src/` | Site templates (`index.html`, `auditor.html`, `compare.html`, `guideline.html`, etc.), CSS and JS. |
| `tests/` | Automated pytest suite for schema validation and statutory bill evaluation. |

## Building & Testing Locally

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/validate_catalog.py  # validate YAML catalog against JSON schema
.venv/bin/pytest -v                           # run unit tests
.venv/bin/python scripts/fetch.py             # download originals not yet stored
.venv/bin/python scripts/convert.py           # documents/<id>/content.html
.venv/bin/python scripts/build_site.py        # dist/
npx -y pagefind@1.3.0 --site dist             # full-text search index
python3 -m http.server -d dist 8000
```

## Using the Bill Compliance Evaluator CLI / API

```sh
# Evaluate a drafted bill against a specific guideline
.venv/bin/python scripts/evaluate_bill.py path/to/bill.txt --guideline uk-opc-drafting-guidance

# Compare a drafted bill across multiple national and supranational guidelines
.venv/bin/python scripts/evaluate_bill.py path/to/bill.txt --compare \
  uk-opc-drafting-guidance eu-joint-practical-guide us-holc-guide-legislative-drafting ca-legistics

# Run local HTTP JSON API server on port 8001
.venv/bin/python scripts/evaluate_bill.py --serve --port 8001
```

## Converting documents

Originals are downloaded and converted locally; only the converted `content.html` and `toc.json` are committed.

```sh
.venv/bin/python scripts/fetch.py <id>      # documents/<id>/original.*, record in data/retrieval.json
.venv/bin/python scripts/convert.py <id>    # documents/<id>/content.html, toc.json, text.txt
.venv/bin/pytest tests/test_documents.py    # converted text is substantial and not a block page
git add data/retrieval.json documents/<id>/content.html documents/<id>/toc.json
```

`fetch.py` records an error instead of saving the response when the server returns anything other than HTTP 200,
a body under 2 KB, or an HTML page where the catalog's `original_format` is PDF or Word. These are usually block
pages, bot challenges, login pages or landing pages that a moved document redirects to. When a site blocks automated
downloads, save the document by hand as `documents/<id>/original.<ext>` and run `convert.py <id>`.

`tests/test_documents.py` fails for any converted document under 1,000 words or whose opening text matches a block
or login page.

## Deployment

`.github/workflows/deploy.yml` builds the site on every push to `main` and publishes `dist/` to GitHub Pages with
`actions/deploy-pages`. Pull requests run the build and tests without deploying. The build uses the committed
`documents/<id>/content.html` files; it does not download documents. The repository's Pages source is set to
**GitHub Actions** (Settings → Pages).

The site is served at `legdraft.linkedlegislation.org`:

- DNS: `legdraft  CNAME  aih.github.io.` in the Route 53 hosted zone for `linkedlegislation.org`.
- Pages custom domain: `legdraft.linkedlegislation.org`, with HTTPS enforced. `https://aih.github.io/legislative-guidelines/`
  redirects to it.

Repository variables (Settings → Secrets and variables → Actions → Variables):

| Variable | Purpose |
|---|---|
| `SITE_URL` | Absolute site URL used in `opensearch.xml`. Defaults to `https://legdraft.linkedlegislation.org/`. |
| `FORM_ENDPOINT` | Formspree-compatible endpoint for the submission form. |

All links in the site are relative, so a build works at any address.

## Search

The site's search uses [Pagefind](https://pagefind.app/), a static index built at deploy time, so it runs on GitHub Pages without a server. Pages carry Pagefind filters for jurisdiction, level, region, language and currency. The site also publishes an `opensearch.xml` description so browsers can add it as a search engine.

To run the same content in OpenSearch:

```sh
docker compose -f opensearch/docker-compose.yml up -d
.venv/bin/python scripts/export_opensearch.py --load http://localhost:9200
```

## Submissions

The site's [Submit a guideline](https://legdraft.linkedlegislation.org/contribute.html) form opens a pre-filled GitHub issue using `.github/ISSUE_TEMPLATE/submit-guideline.yml`. Setting the `FORM_ENDPOINT` environment variable at build time to a Formspree-compatible endpoint sends submissions there instead.

## Rights

Each document remains the work of its issuing body; the licence or reuse terms recorded for each entry are shown on its page. The converted HTML is produced automatically and may contain conversion errors; the original document is always linked.

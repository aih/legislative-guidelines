# Catalog fields

The catalog is split across two files with the same entry format, one entry per document:

- `data/guidelines.yml`: national, supranational and international guidelines.
- `data/subnational.yml`: guidelines of states, provinces, territories and devolved governments.

`scripts/catalog.py` loads both. `data/retrieval.json` is written by `scripts/fetch.py`.

| Field | Required | Description |
|---|---|---|
| `id` | yes | Stable slug: `<country-code>-<short-title>`, lower case. Used for `documents/<id>/` and the page URL. |
| `title` | yes | Title in the original language. |
| `title_en` | no | English rendering of a non-English title. |
| `jurisdiction` | yes | Country or organisation; for sub-national entries, the name of the state, province or territory (e.g. `Texas`). |
| `jurisdiction_level` | yes | `national`, `supranational` (e.g. EU), `international` (e.g. UN, Commonwealth) or `subnational`. |
| `country_code` | yes | ISO 3166-1 alpha-2, or an organisation code (`EU`, `UN`, `COMSEC`). For sub-national entries, the parent country's code. Entries sharing a `country_code` are listed together under that country or organisation on the home page. |
| `subdivision_code` | sub-national | ISO 3166-2 code of the state, province, territory or devolved nation (e.g. `US-TX`, `AU-NSW`, `GB-SCT`). Must start with `country_code`. |
| `subdivision_type` | sub-national | Lower-case kind of subdivision: `state`, `territory`, `province`, `canton`, `land`, `region`, `devolved nation`, `autonomous community`, … Used for the navigation label on the country page (e.g. “States & territories”). |
| `region` | yes | `Europe`, `Americas`, `Asia`, `Africa`, `Oceania`, `International`. Sub-national entries use the parent country's region. |
| `issuing_body` | yes | Office that publishes the document. |
| `languages` | yes | ISO 639-1 codes of the language versions held or linked. |
| `document_type` | yes | e.g. `drafting manual`, `drafting guidelines`, `style guide`, `drafting rules`, `process guide`. |
| `legal_status` | no | Binding instrument (with its citation) or guidance. |
| `legal_tradition` | no | `common_law`, `civil_law`, `bijural`, `hybrid`, `supranational`, or `international` (inferred automatically at build time if omitted). |
| `normative_status` | no | `mandatory`, `advisory`, `interinstitutional`, or `statute`. |
| `edition` | no | Edition or version as stated by the issuer. |
| `published` | no | First publication date (`YYYY`, `YYYY-MM` or `YYYY-MM-DD`). |
| `last_updated` | no | Date of the edition or last revision, or `continuously updated …` for online guides. |
| `currency.status` | yes | `current`, `in-force`, `dated`, `superseded` or `unverified` (definitions at the top of `guidelines.yml`). |
| `currency.note` | no | What was found when checking currency. |
| `currency.superseded` / `currency.superseded_by` | no | Earlier edition replaced by this one, or the document that replaces this one. |
| `currency.checked_on` | yes | Date currency was last checked against the issuer's site. |
| `original_format` | yes | Format published by the issuer: `PDF`, `HTML`, `DOCX`, `DOC`. |
| `source_url` | yes* | Direct URL of the document (`null` when only a landing page exists). |
| `landing_url` | no | Publisher's page for the document. |
| `html_edition_url` | no | An existing HTML edition maintained elsewhere. |
| `crawl.prefix` / `crawl.limit` | no | For multi-page HTML guides: fetch pages linked from `source_url` under this URL prefix. |
| `license` | no | Reuse terms stated by the issuer. |
| `topics` | no | List of thematic tags (e.g. `plain_language`, `gender_neutrality`, `recitals`, `definitions`, `amending_formulas`, `digital_ready`). |
| `key_principles` | no | Core actionable drafting rules extracted from the guideline. |
| `notes` | no | Anything else. |
| `credits` | no | Collections or directories through which the document was found: a list of `{name, url, note}` (`note` optional). Shown as “Found via” on the guideline page, next to the issuing body and the host of the linked copy. Entries from the CALC list of drafting manuals credit `Commonwealth Association of Legislative Counsel (CALC)`, `https://www.calc.ngo/drafting-manuals-and-other-resources`. |

A sub-national entry:

```yaml
- id: us-tx-drafting-manual
  title: Texas Legislative Council Drafting Manual
  jurisdiction: Texas
  jurisdiction_level: subnational
  country_code: US
  subdivision_code: US-TX
  subdivision_type: state
  region: Americas
  issuing_body: Texas Legislative Council
  languages: [en]
  document_type: drafting manual
  currency:
    status: unverified
    checked_on: "2026-11-01"
  original_format: PDF
  source_url: https://tlc.texas.gov/docs/legref/draftingmanual.pdf
  credits:
    - name: Commonwealth Association of Legislative Counsel (CALC)
      url: https://www.calc.ngo/drafting-manuals-and-other-resources
```

## Schema Validation

`data/guidelines.schema.json` defines the formal JSON Schema (Draft 2020-12) for `data/guidelines.yml`. Run `python scripts/validate_catalog.py` to validate all catalog entries.

## `retrieval.json`

Per `id`: `retrieved_at` (UTC), `requested_url`, `final_url`, `http_status`, `content_type`,
`last_modified_header`, `file`, `format`, `bytes`, `sha256`, and `pages` for crawled guides.
An `error` key records a failed download.

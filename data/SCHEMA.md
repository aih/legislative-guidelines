# Catalog fields

`data/guidelines.yml` holds one entry per document. `data/retrieval.json` is written by `scripts/fetch.py`.

| Field | Required | Description |
|---|---|---|
| `id` | yes | Stable slug: `<country-code>-<short-title>`, lower case. Used for `documents/<id>/` and the page URL. |
| `title` | yes | Title in the original language. |
| `title_en` | no | English rendering of a non-English title. |
| `jurisdiction` | yes | Country or organisation. |
| `jurisdiction_level` | yes | `national`, `supranational` (e.g. EU) or `international` (e.g. UN, Commonwealth). |
| `country_code` | yes | ISO 3166-1 alpha-2, or an organisation code (`EU`, `UN`, `COMSEC`). |
| `region` | yes | `Europe`, `Americas`, `Asia`, `Africa`, `Oceania`, `International`. |
| `issuing_body` | yes | Office that publishes the document. |
| `languages` | yes | ISO 639-1 codes of the language versions held or linked. |
| `document_type` | yes | e.g. `drafting manual`, `drafting guidelines`, `style guide`, `drafting rules`, `process guide`. |
| `legal_status` | no | Binding instrument (with its citation) or guidance. |
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
| `notes` | no | Anything else. |

## `retrieval.json`

Per `id`: `retrieved_at` (UTC), `requested_url`, `final_url`, `http_status`, `content_type`,
`last_modified_header`, `file`, `format`, `bytes`, `sha256`, and `pages` for crawled guides.
An `error` key records a failed download.

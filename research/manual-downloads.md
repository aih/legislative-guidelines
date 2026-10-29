# Manual downloads

Documents that `scripts/fetch.py` could not download, as of 2026-10-29. Each site either blocks automated requests,
timed out, or no longer serves the catalogued URL. A browser usually gets the file.

The list covers entries with an `error` in `data/retrieval.json`. The 52 catalog entries not yet attempted are not
included; after running `python scripts/fetch.py`, list any new failures with:

```sh
.venv/bin/python -c "import json; [print(k, '-', v['error']) for k, v in json.load(open('data/retrieval.json')).items() if v.get('error')]"
```

## Procedure

For each document:

1. Open the download URL in a browser and save the file.
   - PDF: save the PDF itself, not the browser's viewer page. In Chrome, use the download button in the PDF toolbar.
   - HTML: File → Save Page As… → format **Webpage, HTML Only**, with a `.html` extension.
2. If the URL in the table did not work and you found the document elsewhere (for example on the landing page), note
   the URL you used.
3. Import the file. This copies it to `documents/<id>/original.<ext>` and writes the download record:

   ```sh
   .venv/bin/python scripts/fetch.py <id> --file ~/Downloads/<file>
   # if downloaded from a different URL:
   .venv/bin/python scripts/fetch.py <id> --file ~/Downloads/<file> --url <url-used>
   ```

   The import fails for files under 2 KB and for `.pdf` files that are not PDFs.
4. If you used a different URL because the catalogued one has moved, also update `source_url` for the entry in
   `data/guidelines.yml`.
5. Convert and check:

   ```sh
   .venv/bin/python scripts/convert.py <id>
   .venv/bin/pytest tests/test_documents.py
   ```

   `convert.py` prints the number of headings and characters. Open `documents/<id>/content.html` in a browser to
   check the headings.
6. Commit on a branch and open a pull request:

   ```sh
   git checkout -b manual-downloads
   git add data/retrieval.json data/guidelines.yml documents/<id>/content.html documents/<id>/toc.json
   git commit -m "Add converted text of <id>"
   git push -u origin manual-downloads
   gh pr create --fill
   ```

   Several documents can go in one branch. `original.*` files are not committed.

## Documents

### PDF

| id | Document | Download URL | Problem |
|---|---|---|---|
| `eu-joint-practical-guide` | Joint Practical Guide for persons involved in the drafting of EU legislation (EU) | <https://eur-lex.europa.eu/content/techleg/KB0213228ENN.pdf> | HTTP 202 bot challenge. Alternative: the PDF link on <https://op.europa.eu/en/publication-detail/-/publication/3879747d-7a3c-411b-a3a0-55c14e2ba732> (English). |
| `eu-joint-handbook-olp` | Joint Handbook on the ordinary legislative procedure (EU) | <https://www.consilium.europa.eu/media/ch2b24su/joint_handbook_en_28-november-2025_def_final.pdf> | HTTP 403 |
| `au-opc-plain-english-manual` | Plain English Manual (Australia) | <https://www.opc.gov.au/sites/default/files/2023-01/plain_english_0.pdf> | Timed out. Landing page: <https://www.opc.gov.au/node/145> |
| `au-opc-drafting-manual` | OPC Drafting Manual (Australia) | <https://www.opc.gov.au/sites/default/files/2023-01/s05pq37.v27.pdf> | Timed out. Landing page: <https://www.opc.gov.au/drafting-resources> |
| `nz-legislation-guidelines-2021` | Legislation Guidelines: 2021 edition (New Zealand) | Find the PDF on <https://www.lac.org.nz/guidelines/legislation-guidelines-2021-edition/> | HTTP 404; the catalogued URL (regulation.govt.nz) has moved. Use `--url` and update `source_url`. |
| `fr-guide-de-legistique` | Guide de légistique (France) | <https://www.legifrance.gouv.fr/contenu/Media/files/autour-de-la-loi/guide-de-legistique/guide_legistique_2026.pdf> | HTTP 403 |
| `es-directrices-tecnica-normativa` | Directrices de técnica normativa (Spain) | <https://www.mpr.gob.es/servicios/publicaciones/Documents/Directrices_2reimpr_linea.pdf> | HTTP 403. Alternative: the BOE publication of the 2005 resolution, <https://www.boe.es/boe/dias/2005/07/29/pdfs/BOE-S-2005-180.pdf> (use `--url`). |
| `it-regole-raccomandazioni-2001` | Regole e raccomandazioni per la formulazione tecnica dei testi legislativi (Italy) | <https://moodle2.units.it/pluginfile.php/210470/mod_resource/content/1/Presidenza%20del%20Consiglio%20dei%20ministri%2C%20Circolare%2020%20aprile%202001.pdf> | Requires a University of Trieste Moodle login. Look for the circular of 20 April 2001 on <https://www.senato.it/istituzione/redazione-dei-testi-legislativi> and use `--url`. |
| `no-lovteknikk-og-lovforberedelse` | Lovteknikk og lovforberedelse (Norway) | <https://www.regjeringen.no/globalassets/upload/kilde/jd/bro/2000/0002/ddd/pdfv/108138-lovteknikkboka.pdf> | HTTP 403. Landing page: <https://www.regjeringen.no/no/dokumenter/veiledning-om-lov--og-forskriftsarbeid/id87536/> |

### HTML

Save as **Webpage, HTML Only**.

| id | Document | Download URL | Problem |
|---|---|---|---|
| `br-lei-complementar-95-1998` | Lei Complementar nº 95, de 26 de fevereiro de 1998 (Brazil) | <https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp95.htm> | planalto.gov.br blocks automated requests |
| `br-decreto-12002-2024` | Decreto nº 12.002, de 22 de abril de 2024 (Brazil) | <https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/decreto/d12002.htm> | planalto.gov.br blocks automated requests |

### Not a single file

| id | Document | URL | Problem |
|---|---|---|---|
| `eu-interinstitutional-style-guide` | Interinstitutional Style Guide (EU) | <https://style-guide.europa.eu/en/> | HTTP 403. A multi-page website; saving the home page captures only the table of contents. Check the site for a PDF edition; otherwise leave the entry as source link only. |
| `au-opc-drafting-directions` | OPC Drafting Directions (Australia) | <https://www.opc.gov.au/drafting-resources/drafting-directions> | No `source_url` in the catalog. A series of separate PDF and DOCX documents; the catalog entry needs splitting into one entry per direction, or one chosen document, before it can be downloaded. |

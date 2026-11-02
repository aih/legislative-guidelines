# Manual downloads

Catalog entries without converted text, as of 2026-10-29: 18 of 97. For each, `scripts/fetch.py` either could not
download the document (the site blocks automated requests, refuses the connection, or no longer serves the URL), or
downloaded a page that is not the document. A browser usually gets the file. Each entry's problem is recorded as
`error` in `data/retrieval.json`; list them with:

```sh
.venv/bin/python -c "import json; [print(k, '-', v['error']) for k, v in json.load(open('data/retrieval.json')).items() if v.get('error')]"
```

## Procedure

For each document:

1. Open the download URL in a browser and save the file.
   - PDF: save the PDF itself, not the browser's viewer page. In Chrome, use the download button in the PDF toolbar.
   - HTML: File → Save Page As… → format **Webpage, HTML Only**, with a `.html` extension.
   - HTML pages whose text is loaded by JavaScript (marked *JavaScript* below): wait for the text to appear, then
     File → Save Page As… → **Webpage, Complete**. Import the `.html` file; the `_files` folder is not needed.
     **HTML Only** saves the page before the text loads.
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
| `eu-joint-handbook-olp` | Joint Handbook on the ordinary legislative procedure (EU) | <https://www.consilium.europa.eu/media/ch2b24su/joint_handbook_en_28-november-2025_def_final.pdf> | HTTP 403 |
| `nz-legislation-guidelines-2021` | Legislation Guidelines: 2021 edition (New Zealand) | Find the PDF on <https://www.lac.org.nz/guidelines/legislation-guidelines-2021-edition/> | HTTP 404; the catalogued URL (regulation.govt.nz) has moved. Use `--url` and update `source_url`. |
| `fr-guide-de-legistique` | Guide de légistique (France) | <https://www.legifrance.gouv.fr/contenu/Media/files/autour-de-la-loi/guide-de-legistique/guide_legistique_2026.pdf> | HTTP 403 |
| `no-lovteknikk-og-lovforberedelse` | Lovteknikk og lovforberedelse (Norway) | <https://www.regjeringen.no/globalassets/upload/kilde/jd/bro/2000/0002/ddd/pdfv/108138-lovteknikkboka.pdf> | HTTP 403. Landing page: <https://www.regjeringen.no/no/dokumenter/veiledning-om-lov--og-forskriftsarbeid/id87536/> |
| `co-manual-elaboracion-textos-normativos` | Manual para la elaboración de textos normativos (Colombia) | <https://www.funcionpublica.gov.co/eva/gestornormativo/norma_pdf.php?i=39371> | TLS error from the server. Landing page: <https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=39371> |
| `oecd-regulatory-policy-governance-2012` | Recommendation of the Council on Regulatory Policy and Governance (OECD) | The PDF link on <https://legalinstruments.oecd.org/en/instruments/OECD-LEGAL-0390> | The instrument page is *JavaScript*. Saving the PDF is simpler; use `--url` with the PDF's URL. |

### HTML

| id | Document | Download URL | Problem |
|---|---|---|---|
| `br-lei-complementar-95-1998` | Lei Complementar nº 95, de 26 de fevereiro de 1998 (Brazil) | <https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp95.htm> | planalto.gov.br blocks automated requests. HTML Only. |
| `br-decreto-12002-2024` | Decreto nº 12.002, de 22 de abril de 2024 (Brazil) | <https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/decreto/d12002.htm> | planalto.gov.br blocks automated requests. HTML Only. |
| `pt-regras-legistica-conselho-ministros` | Regras de legística, Anexo II à RCM n.º 105/2025 (Portugal) | <https://diariodarepublica.pt/dr/detalhe/resolucao-conselho-ministros/105-2025-923487049> | *JavaScript*. The Diário da República also offers a PDF of the issue; either works. |
| `bg-zakon-za-normativnite-aktove` | Закон за нормативните актове (Bulgaria) | <https://parliament.bg/bg/laws/ID/15534> | *JavaScript* |

### No usable source URL

These need a URL found and entered as `source_url` in `data/guidelines.yml` before or while importing.

| id | Document | Where to look | Problem |
|---|---|---|---|
| `ro-legea-24-2000-tehnica-legislativa` | Legea nr. 24/2000 privind normele de tehnică legislativă (Romania) | <https://legislatie.just.ro/Public/DetaliiDocument/21698> | No `source_url` in the catalog. The consolidated text on the landing page can be saved as HTML (*JavaScript*). |
| `lt-teises-aktu-projektu-rengimo-rekomendacijos` | Teisės aktų projektų rengimo rekomendacijos (Lithuania) | <https://www.e-tar.lt/portal/lt/legalAct/9f8e8430723411e3a1f1b21417c4c75e/asr> | No `source_url` in the catalog. *JavaScript*. |
| `lv-normativo-aktu-projektu-izstrades-rokasgramata` | Normatīvo aktu projektu izstrādes rokasgrāmata (Latvia) | <https://tai.mk.gov.lv/book/1/chapter/178> | No `source_url` in the catalog. An online book in chapters; one saved page holds one chapter. Look for a PDF edition. |
| `be-principes-technique-legislative` | Principes de technique législative (Belgium, Conseil d'État) | <https://www.raadvst-consetat.be/> → Technique législative | The catalogued URL redirects to the home page. The guide is published as a PDF. |
| `jp-clb-horitsu-an-sakusei` | 法律案の審査・作成 (Japan, Cabinet Legislation Bureau) | <https://www.clb.go.jp/> | The catalogued URL is the list of bills before the Diet, not a drafting guide. The entry needs a different document or removal. |

### Not a single file

| id | Document | URL | Problem |
|---|---|---|---|
| `gb-sct-drafting-matters` | Drafting Matters! (Scotland) | <https://www.gov.scot/publications/drafting-matters/> | HTTP 202 bot challenge. A multi-page publication; gov.scot usually offers a PDF download under "Documents" on the publication page. |
| `eu-interinstitutional-style-guide` | Interinstitutional Style Guide (EU) | <https://style-guide.europa.eu/en/> | HTTP 403. A multi-page website; saving the home page captures only the table of contents. Check the site for a PDF edition; otherwise leave the entry as source link only. |
| `au-opc-drafting-directions` | OPC Drafting Directions (Australia) | <https://www.opc.gov.au/drafting-resources/drafting-directions> | No `source_url` in the catalog. A series of separate PDF and DOCX documents; the catalog entry needs splitting into one entry per direction, or one chosen document, before it can be downloaded. |

## Sub-national entries

As of 2026-11-01, `scripts/fetch.py` downloaded 141 of the 150 sub-national entries with a `source_url`, and 137 were converted. The same procedure applies; edit `data/subnational.yml` instead of `data/guidelines.yml`.

### Download failed

| id | Document | URL | Problem |
|---|---|---|---|
| `au-act-amending-guide` | Amending Guide (Australian Capital Territory) | <https://www.pco.act.gov.au/__data/assets/pdf_file/0015/2216022/Amending-Guide.pdf> | HTTP 403 |
| `au-act-developing-legislation-working-with-pco` | Developing Legislation and Working with PCO (Australian Capital Territory) | <https://www.pco.act.gov.au/__data/assets/pdf_file/0003/2216037/Developing-Legislation-and-Working-with-PCO.pdf> | HTTP 403 |
| `au-act-drafting-practice-guide` | Drafting Practice Guide (Australian Capital Territory) | <https://www.pco.act.gov.au/__data/assets/pdf_file/0017/2216042/Drafting-Practice-Guide-V2024-1.pdf> | HTTP 403 |
| `au-act-spelling-abbreviations-symbols-guide` | Spelling, Abbreviations and Symbols Guide (Australian Capital Territory) | <https://www.pco.act.gov.au/__data/assets/pdf_file/0007/2216077/Spelling,-Abbreviations-and-Symbols-Guide-V2024-1.pdf> | HTTP 403 |
| `au-act-words-and-phrases-guide` | Words and Phrases Guide: A Guide to Plain Legal Language (Australian Capital Territory) | <https://www.pco.act.gov.au/__data/assets/pdf_file/0020/2216081/Words-and-Phrases.pdf> | HTTP 403 |
| `au-tas-guidelines-preparation-statutory-rules` | Guidelines for the preparation of statutory rules (Tasmania) | <https://nla.gov.au/nla.obj-1382146190/view> | Viewer or bot-check page instead of the PDF. |
| `br-mg-manual-de-redacao-parlamentar` | Manual de Redação Parlamentar (Minas Gerais) | <https://dspace.almg.gov.br/bitstream/11037/5229/5/Manual%20de%20reda%C3%A7%C3%A3o%20parlamentar%20-%203%C2%AA%20Edi%C3%A7%C3%A3o.pdf> | Viewer or bot-check page instead of the PDF. |
| `es-ga-directrices-tecnica-normativa` | Directrices de técnica normativa / Directrices de técnica normativa (Xunta de Ga (Galicia) | <https://www.xunta.gal/dog/Publicados/2014/20141114/AnuncioG0244-061114-0010_es.pdf> | HTTP 500 |
| `in-kl-kerala-law-department-manual` | The Kerala Law Department Manual (Kerala) | <https://lawsect.kerala.gov.in/images/law_dept_manu_eng.pdf> | Connection reset. |

### Downloaded, no usable text

| id | Document | URL | Problem |
|---|---|---|---|
| `ch-sh-richtlinien-gestaltung-erlasse` | Richtlinien für die Gestaltung kantonaler Erlasse (Schaffhausen) | <https://www.zfr.uzh.ch/dam/jcr:96bd6e4c-b447-4eed-a719-e2a2219c6ada/Schaffhausen.pdf> | Scanned PDF with no text layer; needs OCR (Tesseract is not installed in the conversion environment). |
| `us-va-legislators-guide-division-legislative-services` | A Legislator's Guide to the Division of Legislative Services (Virginia) | <https://dls.virginia.gov/pubs/LegisGuideToDLS.pdf> | PDF text is mostly images (345 words extracted); needs OCR. |
| `us-al-drafting-style-manual` | Drafting Style Manual (Alabama) | <https://alison.legislature.state.al.us/lsa/legal-division/manual> | *JavaScript* page; the downloaded HTML has no text. Save with **Webpage, Complete**. |
| `us-nc-legislative-drafting-process` | The Bill Drafting Process (Legislative Drafting Division) (North Carolina) | <https://sites.ncleg.gov/legislativedrafting/the-drafting-process/> | The page is a 181-word overview. The entry may need a different document or removal. |

### No usable source URL

| id | Document | URL | Problem |
|---|---|---|---|
| `at-8-vbg-legistische-richtlinien-2022` | Legistische Richtlinien 2022 (Vorarlberg) | <https://vorarlberg.at/-/legislation-tasks-and-services> | See `notes` and `currency.note` for the URL found by search. |
| `au-nsw-drafting-practice-documents` | PCO drafting practice documents (DP series) (New South Wales) | <https://legislation.nsw.gov.au/information> | See `notes` and `currency.note` for the URL found by search. |
| `br-ma-manual-de-elaboracao-de-proposicoes-legislativas` | Manual de Elaboração de Proposições Legislativas (Maranhão) | <https://www.al.ma.leg.br/> | See `notes` and `currency.note` for the URL found by search. |
| `br-mg-manual-de-redacao-e-tecnica-legislativa-executivo` | Manual de Redação e Técnica Legislativa do Poder Executivo (Minas Gerais) | <https://www.governo.mg.gov.br/> | See `notes` and `currency.note` for the URL found by search. |
| `es-ct-manual-elaboracio-normes` | Manual d'elaboració de normes de la Generalitat de Catalunya (Catalonia) | <https://presidencia.bibliotecadigital.gencat.cat/handle/20.500.14623/1298> | See `notes` and `currency.note` for the URL found by search. |
| `jp-47-bunsho-hoki-jimu-no-tebiki` | 文書・法規事務の手引き (Okinawa Prefecture) | <https://ci.nii.ac.jp/ncid/BA89887246> | See `notes` and `currency.note` for the URL found by search. |
| `mx-oax-manual-de-tecnica-legislativa` | Manual de Técnica Legislativa (Oaxaca) | <https://www.congresooaxaca.gob.mx/> | See `notes` and `currency.note` for the URL found by search. |
| `my-sarawak-legislative-drafting-manual` | Sarawak Legislative Drafting Manual (Sarawak) | <https://www.theborneopost.com/2026/09/19/sarawak-launches-legislative-drafting-manual/> | See `notes` and `currency.note` for the URL found by search. |
| `us-il-bill-drafting-manual` | Illinois Bill Drafting Manual (Illinois) | <https://lrb.ilga.gov/> | See `notes` and `currency.note` for the URL found by search. |
| `us-in-administrative-rules-drafting-manual` | Administrative Rules Drafting Manual (Indiana) | <https://iar.iga.in.gov/> | See `notes` and `currency.note` for the URL found by search. |
| `us-in-drafting-manual-general-assembly` | Drafting Manual for the Indiana General Assembly (Indiana) | <https://iga.in.gov/publications/bill_drafting_manual> | See `notes` and `currency.note` for the URL found by search. |
| `us-la-house-drafting-style-usage-manual` | Drafting Style and Usage Manual (Louisiana) | <https://house.louisiana.gov/> | See `notes` and `currency.note` for the URL found by search. |
| `us-mo-essentials-of-bill-drafting` | The Essentials of Bill Drafting in the Missouri General Assembly (Missouri) | <https://lr.mo.gov/> | See `notes` and `currency.note` for the URL found by search. |
| `us-nh-drafting-procedure-manual-administrative-rules` | Drafting and Procedure Manual for Administrative Rules (New Hampshire) | <https://www.gc.nh.gov/rules> | See `notes` and `currency.note` for the URL found by search. |
| `us-pa-legislative-drafting-manual` | Legislative Drafting Manual (101 Pa. Code, Part I, Subpart C) (Pennsylvania) | <https://www.pacodeandbulletin.gov/Display/pacode?file=/secure/pacode/data/101/subpartICtoc.html> | See `notes` and `currency.note` for the URL found by search. |
| `us-wi-administrative-rules-procedures-manual` | Administrative Rules Procedures Manual (Wisconsin) | <https://legis.wisconsin.gov/lc/rules-clearinghouse/rules-clearinghouse/> | See `notes` and `currency.note` for the URL found by search. |
| `us-wi-bill-drafting-manual` | Wisconsin Bill Drafting Manual (Wisconsin) | <https://docs.legis.wisconsin.gov/statutes/drafting_manual/> | See `notes` and `currency.note` for the URL found by search. |

## Imported by hand

| id | File | Notes |
|---|---|---|
| `eu-joint-practical-guide` | `KB0213228ENN.pdf` | |
| `au-opc-drafting-manual` | `s05pq37.v27.pdf` | Edition 3.2, July 2019 |
| `au-opc-plain-english-manual` | `aus_manual.pdf` | |
| `es-directrices-tecnica-normativa` | `Directrices_2reimpr_linea.pdf` | |
| `it-regole-raccomandazioni-2001` | `regole_testi_legislativi.pdf`, Senate of the Republic edition | Recorded with the Senate landing page as its URL |

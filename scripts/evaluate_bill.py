#!/usr/bin/env python3
"""Legislative Drafting Compliance Evaluator Engine.

Evaluates a drafted bill or statutory text against national and supranational
legislative drafting guidelines from `data/guidelines.yml`, producing:
  - A 1–10 overall compliance score (`score` and `scoreExact`)
  - 5 dimensional sub-scores (`clarity`, `normativePrecision`, `structure`, `conventions`, `definitions`)
  - Quantitative drafting metrics (word count, avg/max sentence length, modal verb counts, passive voice, etc.)
  - An executive summary
  - A criterion-by-criterion checklist (`PASS` / `WARN` / `FAIL`) with official manual citations
  - Verbatim flagged provisions with concrete suggested redrafts
  - Side-by-side multi-guideline comparison support

Modes of operation:
  1. CLI evaluation:
       python scripts/evaluate_bill.py path/to/bill.txt --guideline uk-opc-drafting-guidance
       python scripts/evaluate_bill.py path/to/bill.txt --compare uk-opc-drafting-guidance eu-joint-practical-guide us-house-manual-drafting-style
  2. Local HTTP API server (for local web UI & optional LLM integration):
       python scripts/evaluate_bill.py --serve --port 8001
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "data" / "guidelines.yml"

# ---------------------------------------------------------------------------
# Guideline-Specific Rule Profiles
# ---------------------------------------------------------------------------

GUIDELINE_PROFILES: dict[str, dict[str, Any]] = {
    "uk-opc-drafting-guidance": {
        "id": "uk-opc-drafting-guidance",
        "name": "UK Office of the Parliamentary Counsel (OPC) Drafting Guidance (2024)",
        "jurisdiction": "United Kingdom",
        "tradition": "common_law",
        "modal_policy": "forbid_shall",
        "modal_citation": "UK OPC Drafting Guidance § 3.2 ('Shall')",
        "modal_rule_desc": "Avoid 'shall' in operative text; use 'must' for obligations and present tense ('is', 'applies') for legal consequences.",
        "gender_citation": "UK OPC Drafting Guidance § 2.1 ('Gender-neutral drafting')",
        "sentence_citation": "UK OPC Drafting Guidance §§ 3.1 & 3.4 ('Plain language' & 'Paragraphing')",
        "passive_citation": "UK OPC Drafting Guidance § 3.1.4 ('Active and passive')",
        "definitions_citation": "UK OPC Drafting Guidance § 4.4 ('Definitions')",
        "structure_citation": "UK OPC Drafting Guidance Part 1 & Part 9 ('Tell the story' & 'Final provisions')",
        "archaic_citation": "UK OPC Drafting Guidance § 3.3 ('Vocabulary and archaic language')",
        "xref_citation": "UK OPC Drafting Guidance § 4.3 ('Cross-references')",
        "max_avg_sentence": 28,
        "recitals_policy": "discourage_preambles",
    },
    "eu-joint-practical-guide": {
        "id": "eu-joint-practical-guide",
        "name": "EU Joint Practical Guide (European Parliament, Council & Commission)",
        "jurisdiction": "European Union",
        "tradition": "supranational",
        "modal_policy": "eu_shall_in_articles_only",
        "modal_citation": "EU Joint Practical Guide Rule 2 & Rule 10; Interinstitutional Style Guide § 2.3",
        "modal_rule_desc": "Use 'shall' for imperative obligations in English operative Articles, but NEVER use 'shall' or 'must' inside Recitals ('Whereas').",
        "gender_citation": "EU Joint Practical Guide Rule 6 & EP Gender-Neutral Language Guidelines",
        "sentence_citation": "EU Joint Practical Guide Rules 1, 4 & 5 (Concise sentences for 24-language translation)",
        "passive_citation": "EU Joint Practical Guide Rule 5 (Clear identification of the addressee of obligations)",
        "definitions_citation": "EU Joint Practical Guide Rule 14 (Definitions must not contain autonomous normative provisions)",
        "structure_citation": "EU Joint Practical Guide Rules 7–15 (Title, Citations, Recitals, Enacting Formula, Articles, Entry into force)",
        "archaic_citation": "EU Joint Practical Guide Rules 1 & 6 (Avoid national legal jargon and archaic expressions)",
        "xref_citation": "EU Joint Practical Guide Rule 16 (Avoid imprecise or cascading cross-references)",
        "max_avg_sentence": 30,
        "recitals_policy": "require_recitals_no_normative",
    },
    "us-holc-guide-legislative-drafting": {
        "id": "us-holc-guide-legislative-drafting",
        "name": "US House Office of the Legislative Counsel (HOLC) Guide to Legislative Drafting",
        "jurisdiction": "United States",
        "tradition": "common_law",
        "modal_policy": "us_holc_shall_animate",
        "modal_citation": "US HOLC Guide to Legislative Drafting & Manual on Drafting Style § 301",
        "modal_rule_desc": "Use 'shall' only to impose a mandatory duty on an animate actor ('The Secretary shall...'); use 'must' for conditions or inanimate subjects; never use 'shall' for future tense ('shall mean').",
        "gender_citation": "US HOLC Guide ('Gender-Neutral Language: repeat the noun')",
        "sentence_citation": "US HOLC Guide ('Organization and Subdivision: (a)(1)(A)(i)(I)')",
        "passive_citation": "US HOLC Guide ('Use the active voice and identify the actor')",
        "definitions_citation": "US HOLC Guide ('Definitions: do not stuff substantive law into definitions')",
        "structure_citation": "US HOLC Guide ('Short Title, Definitions, Operative Provisions, Effective Date')",
        "archaic_citation": "US HOLC Manual on Drafting Style ('Avoid such, said, aforesaid, herein, thereof')",
        "xref_citation": "US HOLC Guide ('Specify exact section/subsection; avoid above/below/preceding')",
        "max_avg_sentence": 32,
        "recitals_policy": "discourage_findings",
    },
    "us-house-manual-drafting-style": {
        "id": "us-house-manual-drafting-style",
        "name": "US House Legislative Counsel's Manual on Drafting Style",
        "jurisdiction": "United States",
        "tradition": "common_law",
        "modal_policy": "us_holc_shall_animate",
        "modal_citation": "US House Manual on Drafting Style (HLC 104-1) § 351",
        "modal_rule_desc": "Use 'shall' only for mandatory duty on a named actor; use present tense for declarative facts and 'may' for discretionary authority.",
        "gender_citation": "US House Manual on Drafting Style § 352",
        "sentence_citation": "US House Manual on Drafting Style Part II (Subdivisions & Tabulation)",
        "passive_citation": "US House Manual on Drafting Style § 351(b) (Active Voice)",
        "definitions_citation": "US House Manual on Drafting Style § 304 (Definitions)",
        "structure_citation": "US House Manual on Drafting Style Part I (Structure of a Bill)",
        "archaic_citation": "US House Manual on Drafting Style § 353 (Forbidden words: 'herein', 'said', 'such', 'and/or')",
        "xref_citation": "US House Manual on Drafting Style § 331 (Cross-references)",
        "max_avg_sentence": 32,
        "recitals_policy": "discourage_findings",
    },
    "ca-legistics": {
        "id": "ca-legistics",
        "name": "Canada Department of Justice: Legistics",
        "jurisdiction": "Canada",
        "tradition": "bijural",
        "modal_policy": "forbid_shall",
        "modal_citation": "Canada Legistics: 'Shall' and 'Must'",
        "modal_rule_desc": "Do not use 'shall'; use 'must' to impose obligations and the indicative present tense ('is', 'applies') for declaratory rules.",
        "gender_citation": "Canada Legistics: 'Gender-Neutral Language'",
        "sentence_citation": "Canada Legistics: 'Paragraphing' & 'Plain Language'",
        "passive_citation": "Canada Legistics: 'Voice (Active and Passive)'",
        "definitions_citation": "Canada Legistics: 'Definitions' (No substantive rules; avoid 'means and includes')",
        "structure_citation": "Canada Legistics: 'Order of Provisions (Short title, Interpretation, Application, Operative, Transitional, Coming into force)'",
        "archaic_citation": "Canada Legistics: 'Archaic or Legalese Expressions'",
        "xref_citation": "Canada Legistics: 'Cross-References'",
        "max_avg_sentence": 28,
        "recitals_policy": "optional_purpose",
    },
    "au-opc-plain-english-manual": {
        "id": "au-opc-plain-english-manual",
        "name": "Australia OPC Plain English Manual & Drafting Directions",
        "jurisdiction": "Australia",
        "tradition": "common_law",
        "modal_policy": "forbid_shall",
        "modal_citation": "Australia OPC Plain English Manual §§ 44–48 & Drafting Direction 1.5",
        "modal_rule_desc": "Replace 'shall' with 'must' for obligations and present tense ('is') for declarations.",
        "gender_citation": "Australia OPC Drafting Direction 2.1 ('Gender-neutral language')",
        "sentence_citation": "Australia OPC Plain English Manual §§ 22–38 ('Keep sentences short' & 'Subsections and paragraphs')",
        "passive_citation": "Australia OPC Plain English Manual §§ 57–61 ('Use the active voice')",
        "definitions_citation": "Australia OPC Plain English Manual §§ 68–75 ('Definitions')",
        "structure_citation": "Australia OPC Drafting Manual (Simplified Outlines, Dictionary, Commencement table)",
        "archaic_citation": "Australia OPC Plain English Manual §§ 84–99 ('Traditional legal expressions to avoid')",
        "xref_citation": "Australia OPC Plain English Manual §§ 100–106 ('Cross-references')",
        "max_avg_sentence": 26,
        "recitals_policy": "optional_purpose",
    },
    "nz-legislation-guidelines-2021": {
        "id": "nz-legislation-guidelines-2021",
        "name": "New Zealand Legislation Guidelines (2021 Edition)",
        "jurisdiction": "New Zealand",
        "tradition": "common_law",
        "modal_policy": "forbid_shall",
        "modal_citation": "NZ Legislation Guidelines Ch. 2 & PCO Plain Language Standard",
        "modal_rule_desc": "Eliminate 'shall'; express mandatory duties with 'must' and legal effects in the present tense.",
        "gender_citation": "NZ PCO Plain Language Standard ('Gender-neutral language, including singular they')",
        "sentence_citation": "NZ PCO Plain Language Standard ('Sentence length under 25–30 words & clear paragraphing')",
        "passive_citation": "NZ PCO Plain Language Standard ('Use active verbs and identify who holds the duty or power')",
        "definitions_citation": "NZ Legislation Guidelines Ch. 3 ('Interpretation provisions must not contain substantive law')",
        "structure_citation": "NZ Legislation Act 2019 & LDAC Ch. 3 (Title, Commencement, Purpose, Interpretation, Principal provisions)",
        "archaic_citation": "NZ PCO Plain Language Standard ('Avoid archaic legalisms: herein, thereof, aforesaid')",
        "xref_citation": "NZ PCO Plain Language Standard ('Specific, minimal cross-references')",
        "max_avg_sentence": 27,
        "recitals_policy": "optional_purpose",
    },
    "commonwealth-legislative-drafting-manual": {
        "id": "commonwealth-legislative-drafting-manual",
        "name": "Commonwealth Secretariat Legislative Drafting Manual (2017)",
        "jurisdiction": "Commonwealth of Nations",
        "tradition": "common_law",
        "modal_policy": "forbid_shall",
        "modal_citation": "Commonwealth Legislative Drafting Manual Ch. 5.4 ('Must vs Shall')",
        "modal_rule_desc": "Prefer 'must' to impose obligations; never use 'shall' for future tense or declaratory rules.",
        "gender_citation": "Commonwealth Legislative Drafting Manual Ch. 5.6 ('Gender-neutral drafting')",
        "sentence_citation": "Commonwealth Legislative Drafting Manual Ch. 4 & Ch. 5 ('The legislative sentence & paragraphing')",
        "passive_citation": "Commonwealth Legislative Drafting Manual Ch. 5.3 ('Active voice')",
        "definitions_citation": "Commonwealth Legislative Drafting Manual Ch. 8 ('Definitions: no substantive rules, never use means and includes')",
        "structure_citation": "Commonwealth Legislative Drafting Manual Ch. 6 & Ch. 7 ('Arrangement of sections, Preliminary & Final provisions')",
        "archaic_citation": "Commonwealth Legislative Drafting Manual Ch. 5.5 ('Avoid archaic words and legalese')",
        "xref_citation": "Commonwealth Legislative Drafting Manual Ch. 5.7 ('Cross-referencing')",
        "max_avg_sentence": 28,
        "recitals_policy": "optional_purpose",
    },
    "de-handbuch-der-rechtsfoermlichkeit": {
        "id": "de-handbuch-der-rechtsfoermlichkeit",
        "name": "Germany BMJ Handbuch der Rechtsförmlichkeit (4. Auflage, 2024)",
        "jurisdiction": "Germany",
        "tradition": "civil_law",
        "modal_policy": "civil_law_present",
        "modal_citation": "Handbuch der Rechtsförmlichkeit (HdR) Rn. 82–90 (Gebote, Verbote, Soll-Vorschriften)",
        "modal_rule_desc": "Express legal commands in the normative present indicative or explicit 'hat zu'/'muss'; avoid ambiguous future modals.",
        "gender_citation": "HdR Rn. 105–112 (Geschlechtergerechte Sprache: neutral designations or paired forms)",
        "sentence_citation": "HdR Rn. 65–81 (Verständlichkeit: avoid nested 'Schachtelsätze' and limit § to 3–4 Absätze)",
        "passive_citation": "HdR Rn. 72 (Identify the Normadressat clearly; avoid anonymous passive constructions)",
        "definitions_citation": "HdR Rn. 95–104 (Begriffsbestimmungen / Legaldefinitionen: no hidden commands)",
        "structure_citation": "HdR Teil B (Eingangsformel, Paragrafenfolge, Schlussvorschriften, Inkrafttreten)",
        "archaic_citation": "HdR Rn. 68 (Avoid chancery archaisms and ambiguous connectors)",
        "xref_citation": "HdR Rn. 113–145 (Verweisungen: exact citation of §, Absatz, Satz, Nummer)",
        "max_avg_sentence": 28,
        "recitals_policy": "forbid_recitals_in_statute",
    },
    "fr-guide-de-legistique": {
        "id": "fr-guide-de-legistique",
        "name": "France SGG / Conseil d'État Guide de légistique (4e édition, 2026)",
        "jurisdiction": "France",
        "tradition": "civil_law",
        "modal_policy": "civil_law_present",
        "modal_citation": "Guide de légistique Fiche 3.3.1 (Temps des verbes : présent de l'indicatif à valeur impérative)",
        "modal_rule_desc": "Use the indicative present to express imperative legal norms; avoid future tense, 'shall', or non-normative declarations ('neutrons législatifs').",
        "gender_citation": "Guide de légistique Fiche 3.3.2 & Circulaire du 21 nov. 2017 (Termes épicènes)",
        "sentence_citation": "Guide de légistique Fiche 3.1.2 (Un article = une règle ; phrases courtes et directes)",
        "passive_citation": "Guide de légistique Fiche 3.3.1 (Précision du sujet de droit)",
        "definitions_citation": "Guide de légistique Fiche 3.1 (Définitions : uniquement si nécessaire, sans règle de fond)",
        "structure_citation": "Guide de légistique Partie 3 (Intitulé, Dispositif, Dispositions transitoires et finales)",
        "archaic_citation": "Guide de légistique Fiche 3.3.1 (Bannir les termes archaïques : 'susmentionné', 'ledit', 'et/ou')",
        "xref_citation": "Guide de légistique Fiche 3.2.1 (Éviter les renvois imprécis ou en cascade)",
        "max_avg_sentence": 28,
        "recitals_policy": "forbid_recitals_in_statute",
    },
    "osce-odihr-democratic-lawmaking-2024": {
        "id": "osce-odihr-democratic-lawmaking-2024",
        "name": "OSCE / ODIHR Guidelines on Democratic Lawmaking for Better Laws (2024)",
        "jurisdiction": "OSCE / ODIHR",
        "tradition": "international",
        "modal_policy": "forbid_shall",
        "modal_citation": "OSCE/ODIHR Guidelines (2024) Principle 12 & Venice Commission Rule of Law Checklist § II.B.3",
        "modal_rule_desc": "Laws must be foreseeable, accessible, and clearly distinguish mandatory duties ('must') from discretionary powers ('may').",
        "gender_citation": "OSCE/ODIHR Guidelines §§ 52–56 (Gender-sensitive legislative drafting)",
        "sentence_citation": "OSCE/ODIHR Guidelines § 165 (Plain, intelligible language accessible to the public)",
        "passive_citation": "OSCE/ODIHR Guidelines § 166 (Accountability: clearly identify state bodies and duty-bearers)",
        "definitions_citation": "OSCE/ODIHR Guidelines § 167 (Consistent terminology without hidden substantive burdens)",
        "structure_citation": "OSCE/ODIHR Guidelines §§ 162–175 (Logical hierarchy, transitional safeguards, non-retroactivity, clear entry into force)",
        "archaic_citation": "OSCE/ODIHR Guidelines § 165 (Eliminate obscure legalese)",
        "xref_citation": "OSCE/ODIHR Guidelines § 168 (Minimize opaque cross-references)",
        "max_avg_sentence": 28,
        "recitals_policy": "optional_purpose",
    },
}

# ---------------------------------------------------------------------------
# Linguistic & Statutory Pattern Dictionaries
# ---------------------------------------------------------------------------

ARCHAIC_TERMS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"\bherein(?:before|after|under|above)?\b", re.I), "archaic reference ('herein...')", "in this Act / in this section"),
    (re.compile(r"\bthere(?:of|in|to|under|after|by|with|from)\b", re.I), "archaic pronominal adverb ('thereof/therein/thereto')", "of it / in it / under this section"),
    (re.compile(r"\bwhere(?:of|in|to|by|upon)\b", re.I), "archaic connector ('whereof/wherein/whereby')", "of which / in which / by which"),
    (re.compile(r"\baforesaid\b", re.I), "archaic back-reference ('aforesaid')", "referred to in subsection (...)"),
    (re.compile(r"\bforthwith\b", re.I), "vague archaic temporal adverb ('forthwith')", "immediately / without delay / within [N] days"),
    (re.compile(r"\b(?:whatsoever|whomsoever|whosoever|wheresoever)\b", re.I), "archaic emphatic ('whatsoever/whosoever')", "any / any person who"),
    (re.compile(r"\bnull\s+and\s+void\b", re.I), "redundant legal doublet ('null and void')", "void"),
    (re.compile(r"\bcease\s+and\s+desist\b", re.I), "redundant legal doublet ('cease and desist')", "stop / cease"),
    (re.compile(r"\beach\s+and\s+every\b", re.I), "redundant legal doublet ('each and every')", "each / every"),
    (re.compile(r"\bfull\s+force\s+and\s+effect\b", re.I), "redundant legal phrase ('full force and effect')", "in force / effective"),
    (re.compile(r"\band/or\b", re.I), "ambiguous connector ('and/or' — condemned by all drafting manuals)", "'A or B, or both' (or 'A or B' where inclusive 'or' is standard)"),
    (re.compile(r"\bsaid\s+(?=[a-z]+\b)(?!to\b|that\b)", re.I), "archaic determiner ('said [noun]')", "the / that"),
    (re.compile(r"\bdeemed\s+to\s+be\b", re.I), "overused legal fiction ('deemed to be')", "is / is treated as"),
]

GENDERED_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"\b(?:he|him|his|himself)\b(?!\s+or\s+(?:she|her|herself))", re.I), "masculine-generic pronoun ('he/him/his')", "the person / the applicant / they / their"),
    (re.compile(r"\b(?:he\s+or\s+she|his\s+or\s+her|him\s+or\s+her)\b", re.I), "binary paired pronoun ('he or she' — modern manuals prefer repeating the noun or singular 'they')", "repeat the noun ('the officer') or use 'they/their'"),
    (re.compile(r"\b(?:chairman|chairmen|policeman|policemen|fireman|firemen|workman|workmen|draftsman|draftsmen|ombudsman|layman)\b", re.I), "gendered occupational noun", "chair / police officer / firefighter / worker / drafter / ombudsperson"),
]

PASSIVE_PATTERN = re.compile(
    r"\b(?:shall\s+be|must\s+be|is\s+to\s+be|are\s+to\s+be|may\s+be(?!\s+cited\s+as\b)|is\s+required\s+to\s+be)\s+([a-z]+ed|made|given|taken|done|held|sent|paid|kept|set|borne|shown|known)\b(?!\s+by\b)",
    re.I,
)

VAGUE_XREF_PATTERN = re.compile(
    r"\b(?:the\s+preceding\s+(?:section|subsection|paragraph|article)|the\s+following\s+(?:section|subsection|paragraph|article)|hereinbefore|hereinafter|as\s+provided\s+above|as\s+set\s+forth\s+below|section\s+above|section\s+below)\b",
    re.I,
)

INANIMATE_SHALL_SUBJECTS = {
    "notice", "application", "report", "fee", "licence", "license", "permit", "register",
    "order", "regulation", "rule", "form", "certificate", "fund", "account", "penalty",
    "fine", "term", "period", "act", "section", "subsection", "article", "agreement",
    "contract", "record", "document", "statement", "appeal", "decision",
}


def load_catalog_lookup() -> dict[str, dict[str, Any]]:
    if not CATALOG_PATH.exists():
        return {}
    entries = yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8")) or []
    return {e["id"]: e for e in entries if isinstance(e, dict) and "id" in e}


def get_guideline_profile(guideline_id: str) -> dict[str, Any]:
    if guideline_id in GUIDELINE_PROFILES:
        return GUIDELINE_PROFILES[guideline_id]

    catalog = load_catalog_lookup()
    entry = catalog.get(guideline_id)
    if entry:
        cc = entry.get("country_code", "")
        level = entry.get("jurisdiction_level", "national")
        tradition = entry.get("legal_tradition")
        if not tradition:
            if cc in {"GB", "US", "AU", "NZ", "IE", "PK", "KE", "UG", "NR", "IN", "SG", "HK", "MY", "NG", "GH", "ZA", "COMSEC"}:
                tradition = "common_law"
            elif cc in {"CA"}:
                tradition = "bijural"
            elif level == "supranational":
                tradition = "supranational"
            elif level == "international":
                tradition = "international"
            else:
                tradition = "civil_law"

        title = entry.get("title_en") or entry.get("title") or guideline_id
        juris = entry.get("jurisdiction", "")
        modal_policy = "forbid_shall"
        modal_desc = "Use clear, unambiguous normative verbs ('must' or present indicative); avoid archaic 'shall'."
        if cc == "EU":
            modal_policy = "eu_shall_in_articles_only"
            modal_desc = "Use 'shall' in operative articles of binding EU acts, but never in recitals."
        elif cc == "US":
            modal_policy = "us_holc_shall_animate"
            modal_desc = "Use 'shall' only for mandatory duties on animate actors; use 'must' for conditions."
        elif tradition == "civil_law":
            modal_policy = "civil_law_present"
            modal_desc = "Use the normative present indicative or explicit obligation verbs; avoid non-normative statements."

        return {
            "id": guideline_id,
            "name": f"{title} ({juris})",
            "jurisdiction": juris,
            "tradition": tradition,
            "modal_policy": modal_policy,
            "modal_citation": f"{title} — Normative Expression & Modal Verbs",
            "modal_rule_desc": modal_desc,
            "gender_citation": f"{title} — Inclusive & Neutral Formulation",
            "sentence_citation": f"{title} — Sentence Clarity & Subdivision Structure",
            "passive_citation": f"{title} — Active Voice & Identification of Legal Actor",
            "definitions_citation": f"{title} — Definitions Hygiene",
            "structure_citation": f"{title} — Formal Structure & Final Provisions",
            "archaic_citation": f"{title} — Plain Language & Modern Terminology",
            "xref_citation": f"{title} — Precision of Cross-References",
            "max_avg_sentence": 28 if tradition == "common_law" else 30,
            "recitals_policy": "require_recitals_no_normative" if cc == "EU" else (
                "forbid_recitals_in_statute" if tradition == "civil_law" else "optional_purpose"
            ),
        }

    return GUIDELINE_PROFILES["uk-opc-drafting-guidance"]


def preprocess_bill_text(raw_text: str) -> str:
    """Normalizes plain text, Markdown, HTML, or XML (Akoma Ntoso / USLM) into clean text."""
    text = raw_text.strip()
    if text.startswith("<") and (">" in text):
        # Convert block tags to newlines before stripping tags
        text = re.sub(r"</?(?:p|div|section|article|subsection|paragraph|clause|item|recital|h[1-6]|num|heading|content|block|tr|li)\b[^>]*>", "\n", text, flags=re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = html.unescape(text)
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_sentences(text: str) -> list[str]:
    """Splits statutory text into sentences while respecting common legal abbreviations."""
    protected = re.sub(r"\b(Sec|Art|No|Vol|Ch|Pt|Subsec|Para|U\.S\.C|C\.F\.R|et\s+al|e\.g|i\.e|v|vs|Mr|Mrs|Dr|Prof|St)\.", r"\1<DOT>", text)
    # Split on sentence-ending punctuation or double newlines
    parts = re.split(r"(?<=[.!?;])\s+(?=[A-Z0-9(\"§])|\n{2,}", protected)
    sentences = []
    for p in parts:
        restored = p.replace("<DOT>", ".").strip()
        if len(restored.split()) >= 3:
            sentences.append(restored)
    return sentences


def propose_shall_redraft(sentence: str, policy: str) -> str:
    """Produces a concrete redrafted sentence replacing defective 'shall' usage."""
    s = sentence.strip()
    s = re.sub(r"\bshall\s+not\b", "must not", s, flags=re.I)
    s = re.sub(r"\bshall\s+be\s+deemed\s+to\s+be\b", "is treated as", s, flags=re.I)
    s = re.sub(r"\bshall\s+mean\b", "means", s, flags=re.I)
    s = re.sub(r"\bshall\s+apply\b", "applies", s, flags=re.I)
    s = re.sub(r"\bshall\s+come\s+into\s+force\b", "comes into force", s, flags=re.I)
    s = re.sub(r"\bshall\s+take\s+effect\b", "takes effect", s, flags=re.I)
    if policy == "eu_shall_in_articles_only":
        s = re.sub(r"\b(?:shall|must)\b", "should", s, flags=re.I)
    else:
        s = re.sub(r"\bshall\b", "must", s, flags=re.I)
    return s


def evaluate_bill_deterministic(bill_text: str, guideline_id: str) -> dict[str, Any]:
    """Performs a comprehensive multi-dimensional statutory compliance audit."""
    profile = get_guideline_profile(guideline_id)
    cleaned = preprocess_bill_text(bill_text)
    words = re.findall(r"\b[\w'-]+\b", cleaned)
    word_count = len(words)
    sentences = split_sentences(cleaned)
    sentence_count = max(len(sentences), 1)
    sentence_lengths = [len(re.findall(r"\b[\w'-]+\b", s)) for s in sentences]
    avg_sentence_len = round(sum(sentence_lengths) / sentence_count, 1) if sentence_lengths else 0.0
    max_sentence_len = max(sentence_lengths) if sentence_lengths else 0

    checklist: list[dict[str, str]] = []
    flagged: list[dict[str, str]] = []
    recommendations: list[str] = []

    # Separate Recitals / Preambles from Operative Articles/Sections
    recital_lines: list[str] = []
    operative_sentences: list[str] = []
    in_recitals = False
    for line in cleaned.splitlines():
        ls = line.strip()
        if not ls:
            continue
        if re.match(r"^(?:WHEREAS\b|Whereas:|Having\s+regard\s+to\b|\(\d+\)\s+(?!Section|Article))", ls, re.I):
            in_recitals = True
        if re.match(r"^(?:HAVE\s+ADOPTED|BE\s+IT\s+ENACTED|ENACTED\s+by|Article\s+1\b|Section\s+1\b|SECTION\s+1\b|§\s*1\b)", ls, re.I):
            in_recitals = False
        if in_recitals:
            recital_lines.append(ls)
        else:
            operative_sentences.append(ls)

    # -----------------------------------------------------------------------
    # 1. Modal Verb & Normative Precision Check
    # -----------------------------------------------------------------------
    shall_matches = list(re.finditer(r"\bshall\b", cleaned, re.I))
    must_matches = list(re.finditer(r"\bmust\b", cleaned, re.I))
    may_matches = list(re.finditer(r"\bmay\b", cleaned, re.I))
    shall_count = len(shall_matches)
    must_count = len(must_matches)
    may_count = len(may_matches)

    modal_policy = profile["modal_policy"]
    normative_score = 10.0

    if modal_policy == "forbid_shall":
        if shall_count == 0:
            checklist.append({
                "criterion": "Normative Modal Verbs ('must' vs 'shall')",
                "citation": profile["modal_citation"],
                "status": "PASS",
                "findings": f"No occurrences of 'shall' found ({must_count} 'must', {may_count} 'may'). Adheres strictly to modern plain-language obligation standards."
            })
        else:
            penalty = min(6.0, 1.8 + shall_count * 0.8)
            normative_score -= penalty
            status = "FAIL" if shall_count >= 3 else "WARN"
            checklist.append({
                "criterion": "Normative Modal Verbs ('must' vs 'shall')",
                "citation": profile["modal_citation"],
                "status": status,
                "findings": f"Found {shall_count} occurrence(s) of 'shall' (vs {must_count} 'must'). {profile['modal_rule_desc']}"
            })
            recommendations.append(f"Replace all {shall_count} instance(s) of 'shall' with 'must' (for duties) or present indicative ('is', 'applies') per {profile['modal_citation']}.")
            for s in sentences:
                if re.search(r"\bshall\b", s, re.I) and len(flagged) < 8:
                    flagged.append({
                        "category": "Modal Verb Violation",
                        "citation": profile["modal_citation"],
                        "verbatimOriginal": s[:260],
                        "issue": f"Uses archaic modal 'shall'. {profile['modal_rule_desc']}",
                        "suggestedRedraft": propose_shall_redraft(s[:260], modal_policy),
                    })
                    break

    elif modal_policy == "eu_shall_in_articles_only":
        recital_normative = [r for r in recital_lines if re.search(r"\b(?:shall|must)\b", r, re.I)]
        if recital_normative:
            normative_score -= 3.5
            checklist.append({
                "criterion": "EU Recitals vs Operative Articles (No imperative verbs in Recitals)",
                "citation": "EU Joint Practical Guide Rule 10 & Rule 2",
                "status": "FAIL",
                "findings": f"Found {len(recital_normative)} recital(s) containing imperative modal verbs ('shall'/'must'). Recitals must state reasons and never contain normative rules."
            })
            recommendations.append("Remove 'shall' and 'must' from Recitals ('Whereas' clauses); use 'should' in recitals and reserve 'shall' strictly for operative Articles (EU Joint Practical Guide Rule 10).")
            flagged.append({
                "category": "Normative Language in Recital",
                "citation": "EU Joint Practical Guide Rule 10",
                "verbatimOriginal": recital_normative[0][:260],
                "issue": "Recitals must set out concise reasons for the chief provisions of the enacting terms and must not contain normative wording ('shall' or 'must').",
                "suggestedRedraft": propose_shall_redraft(recital_normative[0][:260], "eu_shall_in_articles_only"),
            })
        elif must_count > shall_count and shall_count == 0:
            normative_score -= 1.5
            checklist.append({
                "criterion": "EU Operative Modal Convention ('shall' in English Articles)",
                "citation": profile["modal_citation"],
                "status": "WARN",
                "findings": f"Text uses 'must' ({must_count}x) and 0 'shall'. Under the EU Interinstitutional Style Guide (§ 2.3), English binding articles use 'shall' for positive obligations."
            })
        else:
            checklist.append({
                "criterion": "EU Normative Modal Verbs & Recital Separation",
                "citation": profile["modal_citation"],
                "status": "PASS",
                "findings": f"Operative articles properly use imperative modals ({shall_count} 'shall') with no normative verbs leaked into recitals."
            })

    elif modal_policy == "us_holc_shall_animate":
        bad_shall = []
        for s in sentences:
            m = re.search(r"\b(?:the\s+|a\s+|an\s+|each\s+|every\s+)?([a-z]+)\s+shall\b", s, re.I)
            if m and m.group(1).lower() in INANIMATE_SHALL_SUBJECTS:
                bad_shall.append((s, m.group(1)))
            elif re.search(r"\bshall\s+(?:mean|be\s+deemed|be\s+construed)\b", s, re.I):
                bad_shall.append((s, "declarative/definitional 'shall'"))
        if bad_shall:
            normative_score -= min(3.5, 1.2 * len(bad_shall))
            checklist.append({
                "criterion": "Disciplined Use of 'Shall' vs 'Must' (Animate Duty vs Condition)",
                "citation": profile["modal_citation"],
                "status": "WARN" if len(bad_shall) == 1 else "FAIL",
                "findings": f"Found {len(bad_shall)} instance(s) where 'shall' is attached to an inanimate noun or declarative definition rather than an animate actor with a legal duty."
            })
            s_ex, reason = bad_shall[0]
            flagged.append({
                "category": "Improper 'Shall' on Inanimate/Declarative Subject",
                "citation": profile["modal_citation"],
                "verbatimOriginal": s_ex[:260],
                "issue": f"Under US HOLC & ULC rules, 'shall' imposes a duty on an actor with legal capacity; '{reason}' cannot bear a personal duty. Use 'must' or present tense.",
                "suggestedRedraft": propose_shall_redraft(s_ex[:260], "forbid_shall"),
            })
            recommendations.append("Restrict 'shall' to duties imposed on animate actors ('The Secretary shall...'); use 'must' for conditions on documents/things and 'means'/'is' for definitions.")
        else:
            checklist.append({
                "criterion": "Disciplined Use of 'Shall' vs 'Must' (Animate Duty vs Condition)",
                "citation": profile["modal_citation"],
                "status": "PASS",
                "findings": f"Modal usage ({shall_count} 'shall', {must_count} 'must', {may_count} 'may') properly distinguishes actor duties from conditions and discretionary powers."
            })

    else:  # civil_law_present
        if shall_count > 0:
            normative_score -= min(3.0, 1.0 + shall_count * 0.4)
            checklist.append({
                "criterion": "Normative Present Indicative (Civil Law Tradition)",
                "citation": profile["modal_citation"],
                "status": "WARN",
                "findings": f"Found {shall_count} occurrence(s) of 'shall'. Civil-law legistics ({profile['jurisdiction']}) express binding rules in the present indicative or explicit 'must' ('hat zu'/'muss')."
            })
        else:
            checklist.append({
                "criterion": "Normative Present Indicative (Civil Law Tradition)",
                "citation": profile["modal_citation"],
                "status": "PASS",
                "findings": "Normative commands are expressed cleanly without archaic future/modal constructions."
            })

    # -----------------------------------------------------------------------
    # 2. Definitions Hygiene (No Substantive Rules or 'Means and Includes')
    # -----------------------------------------------------------------------
    def_Score = 10.0
    def_sentences = [
        s for s in sentences
        if re.search(r"(?:[\"“][^\"”]+[\"”]\s+(?:means|includes|shall\s+mean)|the\s+term\s+[\"“][^\"”]+[\"”]\s+means|\bmeans\s+and\s+includes\b)", s, re.I)
    ]
    substantive_defs = [
        s for s in def_sentences
        if re.search(r"\b(?:shall(?!\s+mean)|must|may\s+not|is\s+liable|commits\s+an\s+offen[cs]e|is\s+guilty)\b", s, re.I)
    ]
    means_and_includes = [s for s in sentences if re.search(r"\bmeans\s+and\s+includes\b", s, re.I)]

    if substantive_defs or means_and_includes:
        def_Score -= (3.5 if substantive_defs else 0) + (2.5 if means_and_includes else 0)
        issues_found = []
        if substantive_defs:
            issues_found.append(f"{len(substantive_defs)} definition(s) containing substantive obligations ('shall'/'must')")
            s_def = substantive_defs[0]
            flagged.append({
                "category": "Substantive Rule Hidden in Definition",
                "citation": profile["definitions_citation"],
                "verbatimOriginal": s_def[:260],
                "issue": "Definitions must only assign meaning to a term and must NEVER impose substantive obligations, duties, or penalties.",
                "suggestedRedraft": re.sub(r"[;,.]?\s*\b(?:and\s+)?(?:any\s+such\s+\w+|who|which)\s+(?:shall|must)\b.+", ". [Move the substantive obligation into a separate operative section.]", s_def[:260], flags=re.I),
            })
        if means_and_includes:
            issues_found.append(f"{len(means_and_includes)} occurrence(s) of ambiguous 'means and includes'")
            s_mi = means_and_includes[0]
            flagged.append({
                "category": "Ambiguous Definition ('means and includes')",
                "citation": profile["definitions_citation"],
                "verbatimOriginal": s_mi[:260],
                "issue": "'Means' is exhaustive whereas 'includes' is enlarging; combining 'means and includes' creates a contradiction in statutory interpretation.",
                "suggestedRedraft": re.sub(r"\bmeans\s+and\s+includes\b", "means", s_mi[:260], flags=re.I),
            })
        checklist.append({
            "criterion": "Definitions Hygiene (No Substantive Duties in Definitions)",
            "citation": profile["definitions_citation"],
            "status": "FAIL",
            "findings": f"Defective definition drafting detected: {'; '.join(issues_found)}."
        })
        recommendations.append(f"Extract substantive duties out of definition clauses into operative sections and replace 'means and includes' with either 'means' or 'includes' ({profile['definitions_citation']}).")
    else:
        checklist.append({
            "criterion": "Definitions Hygiene (No Substantive Duties in Definitions)",
            "citation": profile["definitions_citation"],
            "status": "PASS",
            "findings": f"Inspected {len(def_sentences)} definition clause(s); none embed substantive obligations or use contradictory 'means and includes'."
        })

    # -----------------------------------------------------------------------
    # 3. Archaic Legalese, Redundant Doublets & 'and/or'
    # -----------------------------------------------------------------------
    clarity_score = 10.0
    archaic_hits: list[tuple[str, str, str, str]] = []
    for s in sentences:
        for pat, desc, replacement in ARCHAIC_TERMS:
            m = pat.search(s)
            if m:
                archaic_hits.append((m.group(0), desc, replacement, s))

    if archaic_hits:
        clarity_score -= min(4.5, 1.0 + len(archaic_hits) * 0.65)
        unique_terms = sorted({h[0].lower() for h in archaic_hits})
        checklist.append({
            "criterion": "Plain Language & Elimination of Archaic Legalese",
            "citation": profile["archaic_citation"],
            "status": "FAIL" if len(archaic_hits) >= 3 else "WARN",
            "findings": f"Found {len(archaic_hits)} archaic or ambiguous legalism(s): {', '.join(repr(t) for t in unique_terms[:6])}."
        })
        for term, desc, repl, sent in archaic_hits[:2]:
            redrafted = re.sub(re.escape(term), f"[{repl}]", sent[:260], count=1, flags=re.I)
            flagged.append({
                "category": "Archaic Legalese / Ambiguous Connector",
                "citation": profile["archaic_citation"],
                "verbatimOriginal": sent[:260],
                "issue": f"Contains {desc} ('{term}'), which reduces readability and creates interpretive ambiguity.",
                "suggestedRedraft": redrafted,
            })
        recommendations.append(f"Eliminate archaic legalisms ({', '.join(unique_terms[:5])}) and replace with precise plain-language equivalents per {profile['archaic_citation']}.")
    else:
        checklist.append({
            "criterion": "Plain Language & Elimination of Archaic Legalese",
            "citation": profile["archaic_citation"],
            "status": "PASS",
            "findings": "Zero archaic pronominal adverbs ('herein', 'thereof', 'aforesaid'), redundant doublets ('null and void'), or 'and/or' connectors detected."
        })

    # -----------------------------------------------------------------------
    # 4. Sentence Length, Complexity & Paragraph Tabulation
    # -----------------------------------------------------------------------
    max_avg = profile["max_avg_sentence"]
    long_sentences = [(s, l) for s, l in zip(sentences, sentence_lengths) if l > 42]
    has_tabulation = bool(re.search(r"(?:^|\s)\([a-z1-9]\)\s+", cleaned))

    if avg_sentence_len > max_avg + 8 or (long_sentences and not has_tabulation):
        clarity_score -= 2.5
        checklist.append({
            "criterion": "Sentence Length & Tabulated Paragraphing",
            "citation": profile["sentence_citation"],
            "status": "FAIL",
            "findings": f"Average sentence length is {avg_sentence_len} words (benchmark <= {max_avg} words), with {len(long_sentences)} sentence(s) exceeding 42 words (max: {max_sentence_len} words)."
        })
        if long_sentences:
            longest_s, longest_l = max(long_sentences, key=lambda x: x[1])
            # Suggest tabular split at conditions/commas
            tabular_redraft = re.sub(r",\s+(?:and|or)\s+", "; or\n  (b) ", longest_s[:260], count=1)
            if tabular_redraft == longest_s[:260]:
                tabular_redraft = longest_s[:120] + ":\n  (a) ...;\n  (b) ..."
            flagged.append({
                "category": "Run-on Statutory Sentence",
                "citation": profile["sentence_citation"],
                "verbatimOriginal": longest_s[:260],
                "issue": f"Sentence contains {longest_l} words without clear vertical subdivision, making conditional logic hard to parse.",
                "suggestedRedraft": f"Break conditions into tabulated paragraphs (a), (b), (c): {tabular_redraft}",
            })
        recommendations.append(f"Shorten sentences (currently averaging {avg_sentence_len} words; target <={max_avg}) by breaking compound conditions into tabulated paragraphs (a), (b), (c).")
    elif avg_sentence_len > max_avg or long_sentences:
        clarity_score -= 1.0
        checklist.append({
            "criterion": "Sentence Length & Tabulated Paragraphing",
            "citation": profile["sentence_citation"],
            "status": "WARN",
            "findings": f"Average sentence length is {avg_sentence_len} words (target <={max_avg} words); {len(long_sentences)} sentence(s) exceed 42 words (longest: {max_sentence_len} words)."
        })
    else:
        checklist.append({
            "criterion": "Sentence Length & Tabulated Paragraphing",
            "citation": profile["sentence_citation"],
            "status": "PASS",
            "findings": f"Concise statutory sentences averaging {avg_sentence_len} words (max: {max_sentence_len} words; target <={max_avg} words)."
        })

    # -----------------------------------------------------------------------
    # 5. Active Voice & Clear Identification of Legal Actor
    # -----------------------------------------------------------------------
    passive_sentences = [s for s in sentences if PASSIVE_PATTERN.search(s)]
    passive_count = len(passive_sentences)
    if passive_count >= 3 or (sentence_count > 0 and passive_count / sentence_count > 0.35):
        clarity_score -= 1.8
        normative_score -= 1.0
        checklist.append({
            "criterion": "Active Voice & Identification of Responsible Actor",
            "citation": profile["passive_citation"],
            "status": "FAIL" if passive_count >= 4 else "WARN",
            "findings": f"Found {passive_count} agentless passive construction(s) (e.g. 'shall/must be [verb]ed' without specifying who bears the legal duty)."
        })
        ps = passive_sentences[0]
        pm = PASSIVE_PATTERN.search(ps)
        verb_phrase = pm.group(0) if pm else "passive verb"
        flagged.append({
            "category": "Agentless Passive Voice",
            "citation": profile["passive_citation"],
            "verbatimOriginal": ps[:260],
            "issue": f"Uses passive construction ('{verb_phrase}') without naming the legal actor responsible for performing the obligation.",
            "suggestedRedraft": f"Specify the actor in active voice, e.g.: 'The [Minister / Agency / applicant] must {pm.group(1) if pm else 'perform the action'}...'",
        })
        recommendations.append(f"Convert agentless passive verbs ({passive_count} found) into active voice naming the exact person or authority bearing the legal duty.")
    elif passive_count > 0:
        clarity_score -= 0.6
        checklist.append({
            "criterion": "Active Voice & Identification of Responsible Actor",
            "citation": profile["passive_citation"],
            "status": "WARN",
            "findings": f"Found {passive_count} passive verb construction(s) missing an explicit 'by [actor]' agent; verify that the duty-bearer is unmistakable."
        })
    else:
        checklist.append({
            "criterion": "Active Voice & Identification of Responsible Actor",
            "citation": profile["passive_citation"],
            "status": "PASS",
            "findings": "Provisions consistently use the active voice and identify the legal subject bearing each obligation or power."
        })

    # -----------------------------------------------------------------------
    # 6. Gender-Neutral & Inclusive Drafting
    # -----------------------------------------------------------------------
    conventions_score = 10.0
    gender_hits: list[tuple[str, str, str, str]] = []
    for s in sentences:
        for pat, desc, repl in GENDERED_PATTERNS:
            m = pat.search(s)
            if m:
                gender_hits.append((m.group(0), desc, repl, s))

    if gender_hits:
        masculine_only = [h for h in gender_hits if "masculine" in h[1] or "occupational" in h[1]]
        conventions_score -= min(6.5, 2.5 + len(masculine_only) * 1.2) if masculine_only else 1.5
        checklist.append({
            "criterion": "Gender-Neutral Drafting",
            "citation": profile["gender_citation"],
            "status": "FAIL" if masculine_only else "WARN",
            "findings": f"Found {len(gender_hits)} gender-specific expression(s): {', '.join(repr(h[0]) for h in gender_hits[:5])}."
        })
        term, desc, repl, sent = gender_hits[0]
        flagged.append({
            "category": "Gendered Statutory Language",
            "citation": profile["gender_citation"],
            "verbatimOriginal": sent[:260],
            "issue": f"Uses {desc} ('{term}'). {profile['gender_citation']} requires gender-neutral drafting.",
            "suggestedRedraft": re.sub(r"\b" + re.escape(term) + r"\b", f"[{repl}]", sent[:260], count=1, flags=re.I),
        })
        recommendations.append(f"Replace gendered pronouns/nouns ({', '.join(sorted({h[0].lower() for h in gender_hits}))}) by repeating the defined noun or using gender-neutral terms ({profile['gender_citation']}).")
    else:
        checklist.append({
            "criterion": "Gender-Neutral Drafting",
            "citation": profile["gender_citation"],
            "status": "PASS",
            "findings": "Text is drafted in gender-neutral language with no masculine-generic pronouns or dated occupational titles."
        })

    # -----------------------------------------------------------------------
    # 7. Structural Organization, Cross-References & Final Provisions
    # -----------------------------------------------------------------------
    structure_score = 10.0
    has_numbered_sections = bool(re.search(r"(?:^|\n)\s*(?:Section|SECTION|Sec\.|Article|ARTICLE|Art\.|§|\d+\.)\s*\d*", cleaned))
    has_short_title_or_heading = bool(re.search(r"\b(?:Short\s+title|may\s+be\s+cited\s+as|Act\s+\d{4}|REGULATION|DIRECTIVE|AN\s+ACT|A\s+BILL|Gesetz|Loi)\b", cleaned, re.I))
    has_commencement = bool(re.search(r"\b(?:commencement|comes?\s+into\s+force|enter(?:s)?\s+into\s+force|effective\s+date|takes?\s+effect|Inkrafttreten|entrée\s+en\s+vigueur)\b", cleaned, re.I))

    if not has_numbered_sections:
        structure_score -= 2.5
    if not has_commencement and word_count > 120:
        structure_score -= 1.2

    recitals_policy = profile["recitals_policy"]
    if recitals_policy == "require_recitals_no_normative" and not recital_lines:
        structure_score -= 2.0
        conventions_score -= 2.0
        checklist.append({
            "criterion": "EU Formal Structure (Citations, Recitals & Enacting Formula)",
            "citation": profile["structure_citation"],
            "status": "WARN",
            "findings": "No EU Recitals ('Whereas:') or Citations ('Having regard to...') detected. Under Art. 296 TFEU and EU Joint Practical Guide Rules 8–10, binding EU acts require citations and recitals preceding the enacting formula."
        })
    elif recitals_policy == "forbid_recitals_in_statute" and recital_lines:
        structure_score -= 2.5
        conventions_score -= 2.0
        checklist.append({
            "criterion": "Civil Law Statute Structure (No Recitals Inside Statutory Text)",
            "citation": profile["structure_citation"],
            "status": "FAIL",
            "findings": f"Detected {len(recital_lines)} recital/preamble clause(s) ('Whereas'). Under {profile['name']}, policy justifications belong strictly in the external explanatory memorandum (Begründung / Exposé des motifs), never inside the statute."
        })
        recommendations.append(f"Move 'Whereas' recitals out of the statutory text into the accompanying Explanatory Memorandum ({profile['structure_citation']}).")
    else:
        struct_notes = []
        if has_numbered_sections:
            struct_notes.append("numbered sections/articles present")
        else:
            struct_notes.append("missing clear section/article numbering")
        if has_commencement:
            struct_notes.append("commencement/entry-into-force provision present")
        elif word_count > 120:
            struct_notes.append("no explicit commencement/effective-date clause found")
        checklist.append({
            "criterion": "Statutory Hierarchy, Structure & Final Provisions",
            "citation": profile["structure_citation"],
            "status": "PASS" if has_numbered_sections and (has_commencement or word_count <= 120) else "WARN",
            "findings": f"Structural audit: {', '.join(struct_notes).capitalize()}."
        })

    # Vague cross-references check
    vague_xrefs = [s for s in sentences if VAGUE_XREF_PATTERN.search(s)]
    if vague_xrefs:
        def_Score -= min(2.5, 1.0 * len(vague_xrefs))
        structure_score -= 1.0
        vx = vague_xrefs[0]
        vm = VAGUE_XREF_PATTERN.search(vx)
        vterm = vm.group(0) if vm else "vague reference"
        checklist.append({
            "criterion": "Precision of Internal & External Cross-References",
            "citation": profile["xref_citation"],
            "status": "WARN",
            "findings": f"Found {len(vague_xrefs)} relative/positional cross-reference(s) ('{vterm}'). Relative references break when intervening provisions are inserted by amendment."
        })
        flagged.append({
            "category": "Imprecise Relative Cross-Reference",
            "citation": profile["xref_citation"],
            "verbatimOriginal": vx[:260],
            "issue": f"Uses positional cross-reference ('{vterm}') instead of an explicit section or subsection number.",
            "suggestedRedraft": re.sub(re.escape(vterm), "section [X](Y)", vx[:260], count=1, flags=re.I),
        })
        recommendations.append(f"Replace positional references ('{vterm}') with exact section/subsection citations ({profile['xref_citation']}).")
    else:
        checklist.append({
            "criterion": "Precision of Internal & External Cross-References",
            "citation": profile["xref_citation"],
            "status": "PASS",
            "findings": "No fragile positional cross-references ('above', 'below', 'preceding section', 'hereinbefore') detected."
        })

    # Clamp subscores to [1.0, 10.0]
    subscores = {
        "clarity": round(max(1.0, min(10.0, clarity_score)), 1),
        "normativePrecision": round(max(1.0, min(10.0, normative_score)), 1),
        "structure": round(max(1.0, min(10.0, structure_score)), 1),
        "conventions": round(max(1.0, min(10.0, conventions_score)), 1),
        "definitions": round(max(1.0, min(10.0, def_Score)), 1),
    }

    weighted = (
        subscores["clarity"] * 0.25
        + subscores["normativePrecision"] * 0.25
        + subscores["definitions"] * 0.20
        + subscores["conventions"] * 0.15
        + subscores["structure"] * 0.15
    )
    score_exact = round(max(1.0, min(10.0, weighted)), 1)
    score_int = max(1, min(10, round(score_exact)))

    pass_count = sum(1 for c in checklist if c["status"] == "PASS")
    warn_count = sum(1 for c in checklist if c["status"] == "WARN")
    fail_count = sum(1 for c in checklist if c["status"] == "FAIL")

    if score_exact >= 8.0:
        quality_band = "high compliance"
    elif score_exact >= 5.5:
        quality_band = "moderate compliance with notable drafting issues"
    else:
        quality_band = "low compliance requiring substantial redrafting"

    exec_summary = (
        f"Evaluated {word_count} words ({sentence_count} sentences, avg. {avg_sentence_len} words/sentence) "
        f"against {profile['name']}. The draft achieves a compliance score of {score_exact}/10 ({quality_band}), "
        f"passing {pass_count} of {len(checklist)} criteria with {warn_count} warning(s) and {fail_count} failure(s)."
    )

    if not recommendations:
        recommendations.append(f"The text aligns well with {profile['name']}; verify cross-references and commencement dates prior to introduction.")

    return {
        "guidelineId": profile["id"],
        "guidelineName": profile["name"],
        "jurisdiction": profile["jurisdiction"],
        "tradition": profile["tradition"],
        "score": score_int,
        "scoreExact": score_exact,
        "subscores": subscores,
        "metrics": {
            "wordCount": word_count,
            "sentenceCount": sentence_count,
            "avgSentenceLength": avg_sentence_len,
            "maxSentenceLength": max_sentence_len,
            "shallCount": shall_count,
            "mustCount": must_count,
            "mayCount": may_count,
            "passiveCount": passive_count,
            "archaicCount": len(archaic_hits),
            "genderedCount": len(gender_hits),
            "definitionCount": len(def_sentences),
        },
        "executiveSummary": exec_summary,
        "checklist": checklist,
        "flaggedExcerpts": flagged,
        "recommendations": recommendations,
        "engine": "deterministic-v2",
    }


def compare_bill_across_guidelines(bill_text: str, guideline_ids: list[str]) -> dict[str, Any]:
    """Evaluates a single bill against multiple guidelines for side-by-side comparison."""
    evaluations = [evaluate_bill_deterministic(bill_text, gid) for gid in guideline_ids]
    return {
        "primary": evaluations[0] if evaluations else None,
        "comparisons": evaluations,
    }


# ---------------------------------------------------------------------------
# Local HTTP API Server (optional backend for `/api/evaluate`)
# ---------------------------------------------------------------------------

class EvaluatorRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self._send_json(200, {"ok": True})

    def do_GET(self) -> None:
        if self.path == "/api/guidelines":
            self._send_json(200, {"profiles": list(GUIDELINE_PROFILES.values())})
            return
        self._send_json(200, {"service": "legislative-guidelines-evaluator", "status": "ok"})

    def do_POST(self) -> None:
        if self.path != "/api/evaluate":
            self._send_json(404, {"error": "Not found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        try:
            req = json.loads(raw)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON body"})
            return

        bill_text = (req.get("billText") or "").strip()
        guideline_id = req.get("guidelineId") or "uk-opc-drafting-guidance"
        compare_ids = req.get("compareGuidelineIds") or []

        if not bill_text:
            self._send_json(400, {"error": "billText is required"})
            return

        result = evaluate_bill_deterministic(bill_text, guideline_id)
        if compare_ids:
            all_ids = [guideline_id] + [cid for cid in compare_ids if cid != guideline_id]
            result["comparisons"] = [evaluate_bill_deterministic(bill_text, cid) for cid in all_ids]
        self._send_json(200, result)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", nargs="?", help="Path to drafted bill (.txt, .md, .xml, .html)")
    parser.add_argument("--guideline", "-g", default="uk-opc-drafting-guidance", help="Target guideline ID")
    parser.add_argument("--compare", "-c", nargs="+", help="Compare bill across multiple guideline IDs")
    parser.add_argument("--json", action="store_true", help="Output full evaluation as JSON")
    parser.add_argument("--serve", action="store_true", help="Run local HTTP API server on --port")
    parser.add_argument("--port", type=int, default=8001, help="Port for --serve (default: 8001)")
    args = parser.parse_args()

    if args.serve:
        server = HTTPServer(("127.0.0.1", args.port), EvaluatorRequestHandler)
        print(f"Legislative Guidelines Evaluator API listening on http://127.0.0.1:{args.port}/api/evaluate")
        server.serve_forever()
        return 0

    if not args.file:
        parser.error("Provide a bill file path or pass --serve")

    bill_path = Path(args.file)
    if not bill_path.exists():
        print(f"File not found: {bill_path}", file=sys.stderr)
        return 1

    bill_text = bill_path.read_text(encoding="utf-8")
    if args.compare:
        comp = compare_bill_across_guidelines(bill_text, args.compare)
        if args.json:
            print(json.dumps(comp, indent=2, ensure_ascii=False))
        else:
            print(f"=== Multi-Guideline Comparison ({bill_path.name}) ===")
            for res in comp["comparisons"]:
                print(f"  * {res['guidelineName']:65s} -> {res['scoreExact']:4.1f} / 10 (Score: {res['score']}/10)")
        return 0

    result = evaluate_bill_deterministic(bill_text, args.guideline)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Guideline: {result['guidelineName']}")
        print(f"Score:     {result['score']} / 10 ({result['scoreExact']} / 10)")
        print(f"Summary:   {result['executiveSummary']}\n")
        print("Checklist:")
        for item in result["checklist"]:
            print(f"  [{item['status']:4s}] {item['criterion']} ({item['citation']})")
            print(f"         {item['findings']}")
        if result["flaggedExcerpts"]:
            print("\nFlagged Excerpts & Suggested Redrafts:")
            for ex in result["flaggedExcerpts"]:
                print(f"  - Issue:   {ex['issue']} [{ex['citation']}]")
                print(f"    Quote:   \"{ex['verbatimOriginal']}\"")
                print(f"    Redraft: \"{ex['suggestedRedraft']}\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())

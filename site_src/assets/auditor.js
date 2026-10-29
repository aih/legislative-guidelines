(function () {
  'use strict';

  // -------------------------------------------------------------------------
  // Sample Draft Bills for 1-Click Testing
  // -------------------------------------------------------------------------
  var SAMPLE_BILLS = {
    flawed_draft: [
      'A BILL ENTITLED',
      'AN ACT TO REGULATE AUTOMATED ALGORITHMIC SYSTEMS AND FOR CONNECTED PURPOSES.',
      '',
      'WHEREAS it is expedient and necessary that citizens shall be protected from opaque algorithmic decisions;',
      '',
      'BE IT ENACTED as follows:',
      '',
      'Section 1. Definitions.',
      'In this Act—',
      '"Algorithmic System" means and includes any software, hardware, and/or mathematical model utilized by a public authority, and any person operating such system shall register the same with the Chairman forthwith.',
      '"High-Risk Decision" shall mean any determination affecting a citizen in his employment, credit, or liberty.',
      '',
      'Section 2. Registration and Compliance.',
      'Whosoever deploys a High-Risk Decision system hereinafter described shall file an impact assessment in writing with the Chairman, and if he fails to do so, the permit thereof shall be deemed to be null and void and he shall cease and desist from operating the aforesaid system until such time as the fee is paid and all conditions set forth in the preceding section have been satisfied by the applicant.',
      '',
      'Section 3. Penalties.',
      'An administrative fine not exceeding $50,000 shall be imposed and collected whenever a violation of the provisions hereof is committed.'
    ].join('\n'),

    modern_plain: [
      'Short title',
      '1. This Act may be cited as the Algorithmic Transparency Act 2026.',
      '',
      'Commencement',
      '2. This Act comes into force on 1 January 2027.',
      '',
      'Interpretation',
      '3. In this Act—',
      '"algorithmic system" means an automated computational process used to make or assist an administrative decision;',
      '"covered authority" means a public department or agency listed in Schedule 1;',
      '"Register" means the Public Register of Algorithmic Systems established under section 4.',
      '',
      'Public Register of Algorithmic Systems',
      '4. (1) The Commissioner must establish and maintain a Public Register of Algorithmic Systems.',
      '(2) The Commissioner must publish the Register online in a machine-readable format that is accessible to the public free of charge.',
      '',
      'Duty to register before deployment',
      '5. (1) A covered authority must not deploy an algorithmic system to make a decision affecting an individual\'s legal rights unless the authority has—',
      '  (a) completed an algorithmic impact assessment in accordance with section 6;',
      '  (b) submitted the assessment to the Commissioner; and',
      '  (c) published a plain-language notice of the system in the Register.',
      '(2) If a covered authority modifies the training data or decision logic of a registered algorithmic system, the authority must update its entry in the Register within 14 days after the modification takes effect.',
      '',
      'Right to explanation and human review',
      '6. (1) An individual affected by a decision made with an algorithmic system may request a written explanation of the principal factors that led to the decision.',
      '(2) The covered authority must provide the explanation within 21 days after receiving the request.'
    ].join('\n'),

    eu_regulation: [
      'REGULATION (EU) 2026/... OF THE EUROPEAN PARLIAMENT AND OF THE COUNCIL',
      'on transparency of public sector automated decision-making systems',
      '',
      'THE EUROPEAN PARLIAMENT AND THE COUNCIL OF THE EUROPEAN UNION,',
      'Having regard to the Treaty on the Functioning of the European Union, and in particular Article 114 thereof,',
      'Having regard to the proposal from the European Commission,',
      'Acting in accordance with the ordinary legislative procedure,',
      'Whereas:',
      '(1) Automated decision-making systems are increasingly deployed by public authorities across the Member States to allocate public services and assess regulatory compliance.',
      '(2) Harmonised transparency rules are necessary to ensure legal certainty and safeguard fundamental rights across the internal market.',
      '(3) Member States shall impose administrative fines of at least EUR 500 000 on authorities that fail to register their systems forthwith.',
      '',
      'HAVE ADOPTED THIS REGULATION:',
      '',
      'Article 1',
      'Subject matter and scope',
      '1. This Regulation lays down harmonised rules on the registration and auditing of automated decision-making systems used by public sector bodies.',
      '2. This Regulation shall apply to all public sector bodies established in the Union.',
      '',
      'Article 2',
      'Definitions',
      'For the purposes of this Regulation, the following definitions apply:',
      '(1) "automated decision-making system" means a computational system that generates administrative outputs affecting natural or legal persons;',
      '(2) "competent authority" means the national authority designated by a Member State pursuant to Article 4.',
      '',
      'Article 3',
      'Transparency obligations',
      '1. A public sector body shall register each automated decision-making system in the Union repository prior to putting the system into service.',
      '2. The registration shall include a description of the system\'s purpose, data sources, and human oversight measures.',
      '',
      'Article 4',
      'Entry into force',
      'This Regulation shall enter into force on the twentieth day following that of its publication in the Official Journal of the European Union.'
    ].join('\n'),

    us_federal_bill: [
      '119TH CONGRESS',
      '2D SESSION',
      'H. R. 4820',
      '',
      'A BILL',
      'To require Federal agencies to publish an inventory of automated decision systems, and for other purposes.',
      '',
      'Be it enacted by the Senate and House of Representatives of the United States of America in Congress assembled,',
      '',
      'SECTION 1. SHORT TITLE.',
      'This Act may be cited as the "Federal Automated Decision System Transparency Act of 2026".',
      '',
      'SEC. 2. DEFINITIONS.',
      'In this Act:',
      '  (1) AGENCY.—The term "agency" has the meaning given the term in section 551 of title 5, United States Code.',
      '  (2) AUTOMATED DECISION SYSTEM.—The term "automated decision system" means any computational process derived from machine learning, statistical modeling, or artificial intelligence that issues or recommends an administrative determination.',
      '  (3) DIRECTOR.—The term "Director" means the Director of the Office of Management and Budget.',
      '',
      'SEC. 3. PUBLIC INVENTORY OF AUTOMATED DECISION SYSTEMS.',
      '  (a) IN GENERAL.—Not later than 180 days after the date of enactment of this Act, the head of each agency shall—',
      '    (1) compile a comprehensive inventory of each automated decision system used by the agency; and',
      '    (2) submit the inventory to the Director and publish the inventory on a publicly accessible website of the agency.',
      '  (b) CONTENTS OF NOTICE.—Each notice published under subsection (a)(2) shall include—',
      '    (1) a description of the statutory authority for the automated decision system;',
      '    (2) the categories of data processed by the system; and',
      '    (3) the procedures by which an affected individual may request human review.',
      '',
      'SEC. 4. EFFECTIVE DATE.',
      'This Act shall take effect on the date that is 90 days after the date of enactment of this Act.'
    ].join('\n')
  };

  // -------------------------------------------------------------------------
  // Guideline Profiles (Matching scripts/evaluate_bill.py)
  // -------------------------------------------------------------------------
  var PROFILES = {
    'uk-opc-drafting-guidance': {
      id: 'uk-opc-drafting-guidance',
      name: 'UK Office of the Parliamentary Counsel (OPC) Drafting Guidance (2024)',
      jurisdiction: 'United Kingdom',
      tradition: 'Common Law',
      modalPolicy: 'forbid_shall',
      modalCitation: 'UK OPC Drafting Guidance § 3.2 ("Shall")',
      modalDesc: 'Avoid "shall" in operative text; use "must" for obligations and present tense ("is", "applies") for legal consequences.',
      genderCitation: 'UK OPC Drafting Guidance § 2.1 ("Gender-neutral drafting")',
      sentenceCitation: 'UK OPC Drafting Guidance §§ 3.1 & 3.4 ("Plain language" & "Paragraphing")',
      passiveCitation: 'UK OPC Drafting Guidance § 3.1.4 ("Active and passive")',
      definitionsCitation: 'UK OPC Drafting Guidance § 4.4 ("Definitions")',
      structureCitation: 'UK OPC Drafting Guidance Part 1 & Part 9 ("Tell the story" & "Final provisions")',
      archaicCitation: 'UK OPC Drafting Guidance § 3.3 ("Vocabulary and archaic language")',
      xrefCitation: 'UK OPC Drafting Guidance § 4.3 ("Cross-references")',
      maxAvgSentence: 28,
      recitalsPolicy: 'discourage_preambles'
    },
    'eu-joint-practical-guide': {
      id: 'eu-joint-practical-guide',
      name: 'EU Joint Practical Guide (European Parliament, Council & Commission)',
      jurisdiction: 'European Union',
      tradition: 'Supranational',
      modalPolicy: 'eu_shall_in_articles_only',
      modalCitation: 'EU Joint Practical Guide Rule 2 & Rule 10; Interinstitutional Style Guide § 2.3',
      modalDesc: 'Use "shall" for imperative obligations in English operative Articles, but NEVER use "shall" or "must" inside Recitals ("Whereas").',
      genderCitation: 'EU Joint Practical Guide Rule 6 & EP Gender-Neutral Language Guidelines',
      sentenceCitation: 'EU Joint Practical Guide Rules 1, 4 & 5 (Concise sentences for 24-language translation)',
      passiveCitation: 'EU Joint Practical Guide Rule 5 (Clear identification of the addressee of obligations)',
      definitionsCitation: 'EU Joint Practical Guide Rule 14 (Definitions must not contain autonomous normative provisions)',
      structureCitation: 'EU Joint Practical Guide Rules 7–15 (Title, Citations, Recitals, Enacting Formula, Articles, Entry into force)',
      archaicCitation: 'EU Joint Practical Guide Rules 1 & 6 (Avoid national legal jargon and archaic expressions)',
      xrefCitation: 'EU Joint Practical Guide Rule 16 (Avoid imprecise or cascading cross-references)',
      maxAvgSentence: 30,
      recitalsPolicy: 'require_recitals_no_normative'
    },
    'us-holc-guide-legislative-drafting': {
      id: 'us-holc-guide-legislative-drafting',
      name: 'US House Office of the Legislative Counsel (HOLC) Guide to Legislative Drafting',
      jurisdiction: 'United States',
      tradition: 'Common Law',
      modalPolicy: 'us_holc_shall_animate',
      modalCitation: 'US HOLC Guide to Legislative Drafting & Manual on Drafting Style § 351',
      modalDesc: 'Use "shall" only to impose a mandatory duty on an animate actor ("The Secretary shall..."); use "must" for conditions or inanimate subjects; never use "shall" for definitions ("shall mean").',
      genderCitation: 'US HOLC Guide ("Gender-Neutral Language: repeat the noun")',
      sentenceCitation: 'US HOLC Guide ("Organization and Subdivision: (a)(1)(A)(i)(I)")',
      passiveCitation: 'US HOLC Guide ("Use the active voice and identify the actor")',
      definitionsCitation: 'US HOLC Guide ("Definitions: do not stuff substantive law into definitions")',
      structureCitation: 'US HOLC Guide ("Short Title, Definitions, Operative Provisions, Effective Date")',
      archaicCitation: 'US HOLC Manual on Drafting Style ("Avoid such, said, aforesaid, herein, thereof, and/or")',
      xrefCitation: 'US HOLC Guide ("Specify exact section/subsection; avoid above/below/preceding")',
      maxAvgSentence: 32,
      recitalsPolicy: 'discourage_findings'
    },
    'ca-legistics': {
      id: 'ca-legistics',
      name: 'Canada Department of Justice: Legistics',
      jurisdiction: 'Canada',
      tradition: 'Bijural / Bilingual',
      modalPolicy: 'forbid_shall',
      modalCitation: 'Canada Legistics: "Shall" and "Must"',
      modalDesc: 'Do not use "shall"; use "must" to impose obligations and the indicative present tense ("is", "applies") for declaratory rules.',
      genderCitation: 'Canada Legistics: "Gender-Neutral Language"',
      sentenceCitation: 'Canada Legistics: "Paragraphing" & "Plain Language"',
      passiveCitation: 'Canada Legistics: "Voice (Active and Passive)"',
      definitionsCitation: 'Canada Legistics: "Definitions" (No substantive rules; avoid "means and includes")',
      structureCitation: 'Canada Legistics: "Order of Provisions"',
      archaicCitation: 'Canada Legistics: "Archaic or Legalese Expressions"',
      xrefCitation: 'Canada Legistics: "Cross-References"',
      maxAvgSentence: 28,
      recitalsPolicy: 'optional_purpose'
    },
    'au-opc-plain-english-manual': {
      id: 'au-opc-plain-english-manual',
      name: 'Australia OPC Plain English Manual & Drafting Directions',
      jurisdiction: 'Australia',
      tradition: 'Common Law',
      modalPolicy: 'forbid_shall',
      modalCitation: 'Australia OPC Plain English Manual §§ 44–48 & Drafting Direction 1.5',
      modalDesc: 'Replace "shall" with "must" for obligations and present tense ("is") for declarations.',
      genderCitation: 'Australia OPC Drafting Direction 2.1 ("Gender-neutral language")',
      sentenceCitation: 'Australia OPC Plain English Manual §§ 22–38 ("Keep sentences short & tabulated")',
      passiveCitation: 'Australia OPC Plain English Manual §§ 57–61 ("Use the active voice")',
      definitionsCitation: 'Australia OPC Plain English Manual §§ 68–75 ("Definitions")',
      structureCitation: 'Australia OPC Drafting Manual (Simplified Outlines, Dictionary, Commencement)',
      archaicCitation: 'Australia OPC Plain English Manual §§ 84–99 ("Traditional legal expressions to avoid")',
      xrefCitation: 'Australia OPC Plain English Manual §§ 100–106 ("Cross-references")',
      maxAvgSentence: 26,
      recitalsPolicy: 'optional_purpose'
    },
    'nz-legislation-guidelines-2021': {
      id: 'nz-legislation-guidelines-2021',
      name: 'New Zealand Legislation Guidelines (2021 Edition)',
      jurisdiction: 'New Zealand',
      tradition: 'Common Law',
      modalPolicy: 'forbid_shall',
      modalCitation: 'NZ Legislation Guidelines Ch. 2 & PCO Plain Language Standard',
      modalDesc: 'Eliminate "shall"; express mandatory duties with "must" and legal effects in the present tense.',
      genderCitation: 'NZ PCO Plain Language Standard ("Gender-neutral language, including singular they")',
      sentenceCitation: 'NZ PCO Plain Language Standard ("Sentence length under 25–30 words & clear paragraphing")',
      passiveCitation: 'NZ PCO Plain Language Standard ("Use active verbs and identify who holds the duty")',
      definitionsCitation: 'NZ Legislation Guidelines Ch. 3 ("Interpretation provisions must not contain substantive law")',
      structureCitation: 'NZ Legislation Act 2019 & LDAC Ch. 3 (Title, Commencement, Purpose, Interpretation)',
      archaicCitation: 'NZ PCO Plain Language Standard ("Avoid archaic legalisms: herein, thereof, aforesaid")',
      xrefCitation: 'NZ PCO Plain Language Standard ("Specific, minimal cross-references")',
      maxAvgSentence: 27,
      recitalsPolicy: 'optional_purpose'
    },
    'commonwealth-legislative-drafting-manual': {
      id: 'commonwealth-legislative-drafting-manual',
      name: 'Commonwealth Secretariat Legislative Drafting Manual (2017)',
      jurisdiction: 'Commonwealth of Nations',
      tradition: 'Common Law',
      modalPolicy: 'forbid_shall',
      modalCitation: 'Commonwealth Legislative Drafting Manual Ch. 5.4 ("Must vs Shall")',
      modalDesc: 'Prefer "must" to impose obligations; never use "shall" for future tense or declaratory rules.',
      genderCitation: 'Commonwealth Legislative Drafting Manual Ch. 5.6 ("Gender-neutral drafting")',
      sentenceCitation: 'Commonwealth Legislative Drafting Manual Ch. 4 & Ch. 5 ("The legislative sentence & paragraphing")',
      passiveCitation: 'Commonwealth Legislative Drafting Manual Ch. 5.3 ("Active voice")',
      definitionsCitation: 'Commonwealth Legislative Drafting Manual Ch. 8 ("Definitions: no substantive rules, never use means and includes")',
      structureCitation: 'Commonwealth Legislative Drafting Manual Ch. 6 & Ch. 7 ("Arrangement of sections & Final provisions")',
      archaicCitation: 'Commonwealth Legislative Drafting Manual Ch. 5.5 ("Avoid archaic words and legalese")',
      xrefCitation: 'Commonwealth Legislative Drafting Manual Ch. 5.7 ("Cross-referencing")',
      maxAvgSentence: 28,
      recitalsPolicy: 'optional_purpose'
    },
    'de-handbuch-der-rechtsfoermlichkeit': {
      id: 'de-handbuch-der-rechtsfoermlichkeit',
      name: 'Germany BMJ Handbuch der Rechtsförmlichkeit (4. Auflage, 2024)',
      jurisdiction: 'Germany',
      tradition: 'Civil Law',
      modalPolicy: 'civil_law_present',
      modalCitation: 'Handbuch der Rechtsförmlichkeit (HdR) Rn. 82–90 (Gebote, Verbote, Soll-Vorschriften)',
      modalDesc: 'Express legal commands in the normative present indicative or explicit "hat zu"/"muss"; avoid ambiguous future modals.',
      genderCitation: 'HdR Rn. 105–112 (Geschlechtergerechte Sprache: neutral designations or paired forms)',
      sentenceCitation: 'HdR Rn. 65–81 (Verständlichkeit: avoid nested "Schachtelsätze" and limit § to 3–4 Absätze)',
      passiveCitation: 'HdR Rn. 72 (Identify the Normadressat clearly; avoid anonymous passive constructions)',
      definitionsCitation: 'HdR Rn. 95–104 (Begriffsbestimmungen / Legaldefinitionen: no hidden commands)',
      structureCitation: 'HdR Teil B (Eingangsformel, Paragrafenfolge, Schlussvorschriften, Inkrafttreten)',
      archaicCitation: 'HdR Rn. 68 (Avoid chancery archaisms and ambiguous connectors)',
      xrefCitation: 'HdR Rn. 113–145 (Verweisungen: exact citation of §, Absatz, Satz, Nummer)',
      maxAvgSentence: 28,
      recitalsPolicy: 'forbid_recitals_in_statute'
    },
    'fr-guide-de-legistique': {
      id: 'fr-guide-de-legistique',
      name: 'France SGG / Conseil d\'État Guide de légistique (4e édition, 2026)',
      jurisdiction: 'France',
      tradition: 'Civil Law',
      modalPolicy: 'civil_law_present',
      modalCitation: 'Guide de légistique Fiche 3.3.1 (Temps des verbes : présent de l\'indicatif à valeur impérative)',
      modalDesc: 'Use the indicative present to express imperative legal norms; avoid future tense, "shall", or non-normative recitals ("neutrons législatifs").',
      genderCitation: 'Guide de légistique Fiche 3.3.2 & Circulaire du 21 nov. 2017 (Termes épicènes)',
      sentenceCitation: 'Guide de légistique Fiche 3.1.2 (Un article = une règle ; phrases courtes et directes)',
      passiveCitation: 'Guide de légistique Fiche 3.3.1 (Précision du sujet de droit)',
      definitionsCitation: 'Guide de légistique Fiche 3.1 (Définitions : uniquement si nécessaire, sans règle de fond)',
      structureCitation: 'Guide de légistique Partie 3 (Intitulé, Dispositif, Dispositions transitoires et finales)',
      archaicCitation: 'Guide de légistique Fiche 3.3.1 (Bannir les termes archaïques et "et/ou")',
      xrefCitation: 'Guide de légistique Fiche 3.2.1 (Éviter les renvois imprécis ou en cascade)',
      maxAvgSentence: 28,
      recitalsPolicy: 'forbid_recitals_in_statute'
    },
    'osce-odihr-democratic-lawmaking-2024': {
      id: 'osce-odihr-democratic-lawmaking-2024',
      name: 'OSCE / ODIHR Guidelines on Democratic Lawmaking for Better Laws (2024)',
      jurisdiction: 'OSCE / ODIHR',
      tradition: 'International',
      modalPolicy: 'forbid_shall',
      modalCitation: 'OSCE/ODIHR Guidelines (2024) Principle 12 & Venice Commission Rule of Law Checklist § II.B.3',
      modalDesc: 'Laws must be foreseeable, accessible, and clearly distinguish mandatory duties ("must") from discretionary powers ("may").',
      genderCitation: 'OSCE/ODIHR Guidelines §§ 52–56 (Gender-sensitive legislative drafting)',
      sentenceCitation: 'OSCE/ODIHR Guidelines § 165 (Plain, intelligible language accessible to the public)',
      passiveCitation: 'OSCE/ODIHR Guidelines § 166 (Accountability: clearly identify state bodies and duty-bearers)',
      definitionsCitation: 'OSCE/ODIHR Guidelines § 167 (Consistent terminology without hidden substantive burdens)',
      structureCitation: 'OSCE/ODIHR Guidelines §§ 162–175 (Logical hierarchy, transitional safeguards, clear entry into force)',
      archaicCitation: 'OSCE/ODIHR Guidelines § 165 (Eliminate obscure legalese)',
      xrefCitation: 'OSCE/ODIHR Guidelines § 168 (Minimize opaque cross-references)',
      maxAvgSentence: 28,
      recitalsPolicy: 'optional_purpose'
    }
  };
  PROFILES['us-house-manual-drafting-style'] = PROFILES['us-holc-guide-legislative-drafting'];

  var ARCHAIC_TERMS = [
    { re: /\bherein(?:before|after|under|above)?\b/i, desc: 'archaic reference ("herein...")', repl: 'in this Act / in this section' },
    { re: /\bthere(?:of|in|to|under|after|by|with|from)\b/i, desc: 'archaic pronominal adverb ("thereof/therein/thereto")', repl: 'of it / in it / under this section' },
    { re: /\bwhere(?:of|in|to|by|upon)\b/i, desc: 'archaic connector ("whereof/wherein/whereby")', repl: 'of which / in which / by which' },
    { re: /\baforesaid\b/i, desc: 'archaic back-reference ("aforesaid")', repl: 'referred to in subsection (...)' },
    { re: /\bforthwith\b/i, desc: 'vague archaic temporal adverb ("forthwith")', repl: 'immediately / within [N] days' },
    { re: /\b(?:whatsoever|whomsoever|whosoever|wheresoever)\b/i, desc: 'archaic emphatic ("whatsoever/whosoever")', repl: 'any / any person who' },
    { re: /\bnull\s+and\s+void\b/i, desc: 'redundant legal doublet ("null and void")', repl: 'void' },
    { re: /\bcease\s+and\s+desist\b/i, desc: 'redundant legal doublet ("cease and desist")', repl: 'stop / cease' },
    { re: /\beach\s+and\s+every\b/i, desc: 'redundant legal doublet ("each and every")', repl: 'each / every' },
    { re: /\bfull\s+force\s+and\s+effect\b/i, desc: 'redundant legal phrase ("full force and effect")', repl: 'in force / effective' },
    { re: /\band\/or\b/i, desc: 'ambiguous connector ("and/or" — condemned by all drafting manuals)', repl: '"A or B, or both"' },
    { re: /\bsaid\s+(?=[a-z]+\b)(?!to\b|that\b)/i, desc: 'archaic determiner ("said [noun]")', repl: 'the / that' },
    { re: /\bdeemed\s+to\s+be\b/i, desc: 'overused legal fiction ("deemed to be")', repl: 'is / is treated as' }
  ];

  var GENDERED_PATTERNS = [
    { re: /\b(?:he|him|his|himself)\b(?!\s+or\s+(?:she|her|herself))/i, desc: 'masculine-generic pronoun ("he/him/his")', repl: 'the person / the applicant / they / their' },
    { re: /\b(?:he\s+or\s+she|his\s+or\s+her|him\s+or\s+her)\b/i, desc: 'binary paired pronoun ("he or she")', repl: 'repeat the noun or use "they/their"' },
    { re: /\b(?:chairman|chairmen|policeman|policemen|fireman|firemen|workman|workmen|draftsman|draftsmen|ombudsman|layman)\b/i, desc: 'gendered occupational noun', repl: 'chair / police officer / firefighter / worker / drafter / ombudsperson' }
  ];

  var PASSIVE_RE = /\b(?:shall\s+be|must\s+be|is\s+to\s+be|are\s+to\s+be|may\s+be(?!\s+cited\s+as\b)|is\s+required\s+to\s+be)\s+([a-z]+ed|made|given|taken|done|held|sent|paid|kept|set|borne|shown|known)\b(?!\s+by\b)/i;
  var VAGUE_XREF_RE = /\b(?:the\s+preceding\s+(?:section|subsection|paragraph|article)|the\s+following\s+(?:section|subsection|paragraph|article)|hereinbefore|hereinafter|as\s+provided\s+above|as\s+set\s+forth\s+below|section\s+above|section\s+below)\b/i;
  var INANIMATE_SUBJECTS = {
    notice: 1, application: 1, report: 1, fee: 1, licence: 1, license: 1, permit: 1, register: 1,
    order: 1, regulation: 1, rule: 1, form: 1, certificate: 1, fund: 1, account: 1, penalty: 1,
    fine: 1, term: 1, period: 1, act: 1, section: 1, subsection: 1, article: 1, agreement: 1,
    contract: 1, record: 1, document: 1, statement: 1, appeal: 1, decision: 1
  };

  function getProfile(guidelineId) {
    if (PROFILES[guidelineId]) return PROFILES[guidelineId];
    var sel = document.getElementById('guidelineSelect');
    var opt = sel ? sel.querySelector('option[value="' + guidelineId + '"]') : null;
    var label = opt ? opt.textContent : guidelineId;
    var juris = opt && opt.dataset.jurisdiction ? opt.dataset.jurisdiction : 'National';
    var code = opt && opt.dataset.code ? opt.dataset.code : '';
    var level = opt && opt.dataset.level ? opt.dataset.level : 'national';
    var commonLawCodes = { GB: 1, US: 1, AU: 1, NZ: 1, IE: 1, PK: 1, KE: 1, UG: 1, NR: 1, IN: 1, SG: 1, HK: 1, MY: 1, NG: 1, GH: 1, ZA: 1, COMSEC: 1 };
    var tradition = code === 'CA' ? 'Bijural' : (commonLawCodes[code] ? 'Common Law' : (level === 'supranational' ? 'Supranational' : (level === 'international' ? 'International' : 'Civil Law')));
    var modalPolicy = code === 'EU' ? 'eu_shall_in_articles_only' : (code === 'US' ? 'us_holc_shall_animate' : (tradition === 'Civil Law' ? 'civil_law_present' : 'forbid_shall'));
    return {
      id: guidelineId,
      name: label,
      jurisdiction: juris,
      tradition: tradition,
      modalPolicy: modalPolicy,
      modalCitation: label + ' — Normative Verbs & Obligations',
      modalDesc: modalPolicy === 'forbid_shall' ? 'Avoid "shall"; use "must" for duties and present tense for legal state.' : 'Use consistent, unambiguous normative verbs.',
      genderCitation: label + ' — Gender-Neutral Drafting',
      sentenceCitation: label + ' — Sentence Length & Paragraphing',
      passiveCitation: label + ' — Active Voice & Actor Identification',
      definitionsCitation: label + ' — Definitions Hygiene',
      structureCitation: label + ' — Statutory Structure & Final Clauses',
      archaicCitation: label + ' — Plain Language & Modern Terminology',
      xrefCitation: label + ' — Precision of Cross-References',
      maxAvgSentence: tradition === 'Common Law' ? 28 : 30,
      recitalsPolicy: code === 'EU' ? 'require_recitals_no_normative' : (tradition === 'Civil Law' ? 'forbid_recitals_in_statute' : 'optional_purpose')
    };
  }

  function preprocessText(raw) {
    var t = (raw || '').trim();
    if (t.indexOf('<') !== -1 && t.indexOf('>') !== -1) {
      t = t.replace(/<\/?(?:p|div|section|article|subsection|paragraph|clause|item|recital|h[1-6]|num|heading|content|block|tr|li)\b[^>]*>/gi, '\n');
      t = t.replace(/<[^>]+>/g, ' ');
    }
    return t.replace(/\r\n?/g, '\n').replace(/[ \t]+/g, ' ').replace(/\n{3,}/g, '\n\n').trim();
  }

  function splitSentences(text) {
    var prot = text.replace(/\b(Sec|Art|No|Vol|Ch|Pt|Subsec|Para|U\.S\.C|C\.F\.R|et\s+al|e\.g|i\.e|v|vs|Mr|Mrs|Dr|Prof|St)\./g, '$1<DOT>');
    var parts = prot.split(/(?<=[.!?;])\s+(?=[A-Z0-9("§])|\n{2,}/);
    var out = [];
    parts.forEach(function (p) {
      var s = p.replace(/<DOT>/g, '.').trim();
      if (s.split(/\s+/).length >= 3) out.push(s);
    });
    return out;
  }

  function proposeShallRedraft(s, policy) {
    var out = s.trim()
      .replace(/\bshall\s+not\b/gi, 'must not')
      .replace(/\bshall\s+be\s+deemed\s+to\s+be\b/gi, 'is treated as')
      .replace(/\bshall\s+mean\b/gi, 'means')
      .replace(/\bshall\s+apply\b/gi, 'applies')
      .replace(/\bshall\s+come\s+into\s+force\b/gi, 'comes into force')
      .replace(/\bshall\s+take\s+effect\b/gi, 'takes effect');
    if (policy === 'eu_shall_in_articles_only') {
      return out.replace(/\b(?:shall|must)\b/gi, 'should');
    }
    return out.replace(/\bshall\b/gi, 'must');
  }

  function evaluateBill(rawText, guidelineId) {
    var profile = getProfile(guidelineId);
    var cleaned = preprocessText(rawText);
    var words = cleaned.match(/\b[\w'-]+\b/g) || [];
    var wordCount = words.length;
    var sentences = splitSentences(cleaned);
    var sentenceCount = Math.max(sentences.length, 1);
    var sentenceLengths = sentences.map(function (s) { return (s.match(/\b[\w'-]+\b/g) || []).length; });
    var totalSentWords = sentenceLengths.reduce(function (a, b) { return a + b; }, 0);
    var avgSentenceLen = sentenceLengths.length ? Math.round((totalSentWords / sentenceCount) * 10) / 10 : 0;
    var maxSentenceLen = sentenceLengths.length ? Math.max.apply(null, sentenceLengths) : 0;

    var checklist = [];
    var flagged = [];
    var recommendations = [];

    // Separate Recitals from Operative clauses
    var recitalLines = [];
    var inRecitals = false;
    cleaned.split('\n').forEach(function (line) {
      var ls = line.trim();
      if (!ls) return;
      if (/^(?:WHEREAS\b|Whereas:|Having\s+regard\s+to\b|\(\d+\)\s+(?!Section|Article))/i.test(ls)) {
        inRecitals = true;
      }
      if (/^(?:HAVE\s+ADOPTED|BE\s+IT\s+ENACTED|ENACTED\s+by|Article\s+1\b|Section\s+1\b|SECTION\s+1\b|§\s*1\b|1\.\s)/i.test(ls)) {
        inRecitals = false;
      }
      if (inRecitals) recitalLines.push(ls);
    });

    var shallCount = (cleaned.match(/\bshall\b/gi) || []).length;
    var mustCount = (cleaned.match(/\bmust\b/gi) || []).length;
    var mayCount = (cleaned.match(/\bmay\b/gi) || []).length;

    var normativeScore = 10.0;
    var clarityScore = 10.0;
    var defScore = 10.0;
    var conventionsScore = 10.0;
    var structureScore = 10.0;

    // 1. Modal Verbs
    if (profile.modalPolicy === 'forbid_shall') {
      if (shallCount === 0) {
        checklist.push({
          criterion: 'Normative Modal Verbs ("must" vs "shall")',
          citation: profile.modalCitation,
          status: 'PASS',
          findings: 'Zero occurrences of "shall" (' + mustCount + ' "must", ' + mayCount + ' "may"). Adheres to modern plain-language obligation standards.'
        });
      } else {
        normativeScore -= Math.min(6.0, 1.8 + shallCount * 0.8);
        checklist.push({
          criterion: 'Normative Modal Verbs ("must" vs "shall")',
          citation: profile.modalCitation,
          status: shallCount >= 3 ? 'FAIL' : 'WARN',
          findings: 'Found ' + shallCount + ' occurrence(s) of "shall" (vs ' + mustCount + ' "must"). ' + profile.modalDesc
        });
        recommendations.push('Replace all ' + shallCount + ' instance(s) of "shall" with "must" (for obligations) or present tense ("is", "applies") per ' + profile.modalCitation + '.');
        for (var i = 0; i < sentences.length; i++) {
          if (/\bshall\b/i.test(sentences[i])) {
            flagged.push({
              category: 'Modal Verb Violation',
              citation: profile.modalCitation,
              verbatimOriginal: sentences[i].slice(0, 260),
              issue: 'Uses archaic modal "shall". ' + profile.modalDesc,
              suggestedRedraft: proposeShallRedraft(sentences[i].slice(0, 260), profile.modalPolicy)
            });
            break;
          }
        }
      }
    } else if (profile.modalPolicy === 'eu_shall_in_articles_only') {
      var badRecitals = recitalLines.filter(function (r) { return /\b(?:shall|must)\b/i.test(r); });
      if (badRecitals.length > 0) {
        normativeScore -= 3.5;
        checklist.push({
          criterion: 'EU Recitals vs Operative Articles (No imperative verbs in Recitals)',
          citation: 'EU Joint Practical Guide Rule 10 & Rule 2',
          status: 'FAIL',
          findings: 'Found ' + badRecitals.length + ' recital(s) containing imperative modal verbs ("shall"/"must"). Recitals must state reasons and never contain normative rules.'
        });
        flagged.push({
          category: 'Normative Language in Recital',
          citation: 'EU Joint Practical Guide Rule 10',
          verbatimOriginal: badRecitals[0].slice(0, 260),
          issue: 'Recitals must set out concise reasons for the chief provisions of the enacting terms and must not contain normative wording ("shall" or "must").',
          suggestedRedraft: proposeShallRedraft(badRecitals[0].slice(0, 260), 'eu_shall_in_articles_only')
        });
        recommendations.push('Remove "shall" and "must" from Recitals ("Whereas" clauses); use "should" in recitals and reserve "shall" strictly for operative Articles (EU Joint Practical Guide Rule 10).');
      } else if (mustCount > shallCount && shallCount === 0) {
        normativeScore -= 1.5;
        checklist.push({
          criterion: 'EU Operative Modal Convention ("shall" in English Articles)',
          citation: profile.modalCitation,
          status: 'WARN',
          findings: 'Text uses "must" (' + mustCount + 'x) and 0 "shall". Under the EU Interinstitutional Style Guide (§ 2.3), English binding articles use "shall" for positive obligations.'
        });
      } else {
        checklist.push({
          criterion: 'EU Normative Modal Verbs & Recital Separation',
          citation: profile.modalCitation,
          status: 'PASS',
          findings: 'Operative articles properly use imperative modals (' + shallCount + ' "shall") with no normative verbs leaked into recitals.'
        });
      }
    } else if (profile.modalPolicy === 'us_holc_shall_animate') {
      var badShall = [];
      sentences.forEach(function (s) {
        var m = s.match(/\b(?:the\s+|a\s+|an\s+|each\s+|every\s+)?([a-z]+)\s+shall\b/i);
        if (m && INANIMATE_SUBJECTS[m[1].toLowerCase()]) {
          badShall.push({ s: s, reason: m[1] });
        } else if (/\bshall\s+(?:mean|be\s+deemed|be\s+construed)\b/i.test(s)) {
          badShall.push({ s: s, reason: 'declarative/definitional "shall"' });
        }
      });
      if (badShall.length > 0) {
        normativeScore -= Math.min(3.5, 1.2 * badShall.length);
        checklist.push({
          criterion: 'Disciplined Use of "Shall" vs "Must" (Animate Duty vs Condition)',
          citation: profile.modalCitation,
          status: badShall.length === 1 ? 'WARN' : 'FAIL',
          findings: 'Found ' + badShall.length + ' instance(s) where "shall" is attached to an inanimate noun or declarative definition rather than an animate actor with a legal duty.'
        });
        flagged.push({
          category: 'Improper "Shall" on Inanimate/Declarative Subject',
          citation: profile.modalCitation,
          verbatimOriginal: badShall[0].s.slice(0, 260),
          issue: 'Under US HOLC & ULC rules, "shall" imposes a duty on an actor with legal capacity; "' + badShall[0].reason + '" cannot bear a personal duty. Use "must" or present tense.',
          suggestedRedraft: proposeShallRedraft(badShall[0].s.slice(0, 260), 'forbid_shall')
        });
        recommendations.push('Restrict "shall" to duties imposed on animate actors ("The Secretary shall..."); use "must" for conditions on documents/things and "means"/"is" for definitions.');
      } else {
        checklist.push({
          criterion: 'Disciplined Use of "Shall" vs "Must" (Animate Duty vs Condition)',
          citation: profile.modalCitation,
          status: 'PASS',
          findings: 'Modal usage (' + shallCount + ' "shall", ' + mustCount + ' "must", ' + mayCount + ' "may") properly distinguishes actor duties from conditions and discretionary powers.'
        });
      }
    } else {
      if (shallCount > 0) {
        normativeScore -= Math.min(3.0, 1.0 + shallCount * 0.4);
        checklist.push({
          criterion: 'Normative Present Indicative (Civil Law Tradition)',
          citation: profile.modalCitation,
          status: 'WARN',
          findings: 'Found ' + shallCount + ' occurrence(s) of "shall". Civil-law legistics (' + profile.jurisdiction + ') express binding rules in the present indicative or explicit "must".'
        });
      } else {
        checklist.push({
          criterion: 'Normative Present Indicative (Civil Law Tradition)',
          citation: profile.modalCitation,
          status: 'PASS',
          findings: 'Normative commands are expressed cleanly without archaic future/modal constructions.'
        });
      }
    }

    // 2. Definitions Hygiene
    var defSentences = sentences.filter(function (s) {
      return /(?:["“][^"”]+["”]\s+(?:means|includes|shall\s+mean)|the\s+term\s+["“][^"”]+["”]\s+means|\bmeans\s+and\s+includes\b)/i.test(s);
    });
    var subDefs = defSentences.filter(function (s) {
      return /\b(?:shall(?!\s+mean)|must|may\s+not|is\s+liable|commits\s+an\s+offen[cs]e|is\s+guilty)\b/i.test(s);
    });
    var meansAndIncludes = sentences.filter(function (s) { return /\bmeans\s+and\s+includes\b/i.test(s); });

    if (subDefs.length > 0 || meansAndIncludes.length > 0) {
      defScore -= (subDefs.length ? 3.5 : 0) + (meansAndIncludes.length ? 2.5 : 0);
      var defIssues = [];
      if (subDefs.length) {
        defIssues.push(subDefs.length + ' definition(s) containing substantive obligations ("shall"/"must")');
        flagged.push({
          category: 'Substantive Rule Hidden in Definition',
          citation: profile.definitionsCitation,
          verbatimOriginal: subDefs[0].slice(0, 260),
          issue: 'Definitions must only assign meaning to a term and must NEVER impose substantive obligations, duties, or penalties.',
          suggestedRedraft: subDefs[0].slice(0, 260).replace(/[;,.]?\s*\b(?:and\s+)?(?:any\s+such\s+\w+|who|which)\s+(?:shall|must)\b.+/i, '. [Move substantive obligation to an operative section.]')
        });
      }
      if (meansAndIncludes.length) {
        defIssues.push(meansAndIncludes.length + ' occurrence(s) of contradictory "means and includes"');
        flagged.push({
          category: 'Ambiguous Definition ("means and includes")',
          citation: profile.definitionsCitation,
          verbatimOriginal: meansAndIncludes[0].slice(0, 260),
          issue: '"Means" is exhaustive whereas "includes" is enlarging; combining "means and includes" creates a contradiction in statutory interpretation.',
          suggestedRedraft: meansAndIncludes[0].slice(0, 260).replace(/\bmeans\s+and\s+includes\b/i, 'means')
        });
      }
      checklist.push({
        criterion: 'Definitions Hygiene (No Substantive Duties in Definitions)',
        citation: profile.definitionsCitation,
        status: 'FAIL',
        findings: 'Defective definition drafting detected: ' + defIssues.join('; ') + '.'
      });
      recommendations.push('Extract substantive obligations out of definition clauses into operative sections and replace "means and includes" with either "means" or "includes" (' + profile.definitionsCitation + ').');
    } else {
      checklist.push({
        criterion: 'Definitions Hygiene (No Substantive Duties in Definitions)',
        citation: profile.definitionsCitation,
        status: 'PASS',
        findings: 'Inspected ' + defSentences.length + ' definition clause(s); none embed substantive obligations or use contradictory "means and includes".'
      });
    }

    // 3. Archaic Legalese
    var archaicHits = [];
    sentences.forEach(function (s) {
      ARCHAIC_TERMS.forEach(function (item) {
        var m = s.match(item.re);
        if (m) archaicHits.push({ term: m[0], desc: item.desc, repl: item.repl, sent: s });
      });
    });

    if (archaicHits.length > 0) {
      clarityScore -= Math.min(4.5, 1.0 + archaicHits.length * 0.65);
      var uniq = [];
      archaicHits.forEach(function (h) {
        var low = h.term.toLowerCase();
        if (uniq.indexOf(low) === -1) uniq.push(low);
      });
      checklist.push({
        criterion: 'Plain Language & Elimination of Archaic Legalese',
        citation: profile.archaicCitation,
        status: archaicHits.length >= 3 ? 'FAIL' : 'WARN',
        findings: 'Found ' + archaicHits.length + ' archaic or ambiguous legalism(s): ' + uniq.slice(0, 6).map(function (u) { return '"' + u + '"'; }).join(', ') + '.'
      });
      archaicHits.slice(0, 2).forEach(function (h) {
        flagged.push({
          category: 'Archaic Legalese / Ambiguous Connector',
          citation: profile.archaicCitation,
          verbatimOriginal: h.sent.slice(0, 260),
          issue: 'Contains ' + h.desc + ' ("' + h.term + '"), which reduces readability and creates interpretive ambiguity.',
          suggestedRedraft: h.sent.slice(0, 260).replace(h.term, '[' + h.repl + ']')
        });
      });
      recommendations.push('Eliminate archaic legalisms (' + uniq.slice(0, 5).join(', ') + ') and replace with plain-language equivalents per ' + profile.archaicCitation + '.');
    } else {
      checklist.push({
        criterion: 'Plain Language & Elimination of Archaic Legalese',
        citation: profile.archaicCitation,
        status: 'PASS',
        findings: 'Zero archaic pronominal adverbs ("herein", "thereof", "aforesaid"), redundant doublets ("null and void"), or "and/or" connectors detected.'
      });
    }

    // 4. Sentence Length & Tabulation
    var longSents = sentences.filter(function (s) { return (s.match(/\b[\w'-]+\b/g) || []).length > 42; });
    var hasTab = /(?:^|\s)\([a-z1-9]\)\s+/.test(cleaned);
    if (avgSentenceLen > profile.maxAvgSentence + 8 || (longSents.length > 0 && !hasTab)) {
      clarityScore -= 2.5;
      checklist.push({
        criterion: 'Sentence Length & Tabulated Paragraphing',
        citation: profile.sentenceCitation,
        status: 'FAIL',
        findings: 'Average sentence length is ' + avgSentenceLen + ' words (benchmark <= ' + profile.maxAvgSentence + ' words), with ' + longSents.length + ' sentence(s) exceeding 42 words (max: ' + maxSentenceLen + ' words).'
      });
      if (longSents.length > 0) {
        var longest = longSents.reduce(function (a, b) { return a.length >= b.length ? a : b; });
        flagged.push({
          category: 'Run-on Statutory Sentence',
          citation: profile.sentenceCitation,
          verbatimOriginal: longest.slice(0, 260),
          issue: 'Sentence contains ' + (longest.match(/\b[\w'-]+\b/g) || []).length + ' words without vertical subdivision, making conditional logic hard to parse.',
          suggestedRedraft: 'Break compound conditions into tabulated paragraphs (a), (b), (c): ' + longest.slice(0, 140) + ':\n  (a) ...;\n  (b) ...'
        });
      }
      recommendations.push('Shorten sentences (currently averaging ' + avgSentenceLen + ' words; target <=' + profile.maxAvgSentence + ') by splitting compound conditions into tabulated paragraphs (a), (b), (c).');
    } else if (avgSentenceLen > profile.maxAvgSentence || longSents.length > 0) {
      clarityScore -= 1.0;
      checklist.push({
        criterion: 'Sentence Length & Tabulated Paragraphing',
        citation: profile.sentenceCitation,
        status: 'WARN',
        findings: 'Average sentence length is ' + avgSentenceLen + ' words (target <=' + profile.maxAvgSentence + ' words); ' + longSents.length + ' sentence(s) exceed 42 words (longest: ' + maxSentenceLen + ' words).'
      });
    } else {
      checklist.push({
        criterion: 'Sentence Length & Tabulated Paragraphing',
        citation: profile.sentenceCitation,
        status: 'PASS',
        findings: 'Concise statutory sentences averaging ' + avgSentenceLen + ' words (max: ' + maxSentenceLen + ' words; target <=' + profile.maxAvgSentence + ' words).'
      });
    }

    // 5. Active Voice vs Agentless Passive
    var passiveSents = sentences.filter(function (s) { return PASSIVE_RE.test(s); });
    var passiveCount = passiveSents.length;
    if (passiveCount >= 3 || (sentenceCount > 0 && passiveCount / sentenceCount > 0.35)) {
      clarityScore -= 1.8;
      normativeScore -= 1.0;
      checklist.push({
        criterion: 'Active Voice & Identification of Responsible Actor',
        citation: profile.passiveCitation,
        status: passiveCount >= 4 ? 'FAIL' : 'WARN',
        findings: 'Found ' + passiveCount + ' agentless passive construction(s) (e.g. "shall/must be [verb]ed" without specifying who bears the legal duty).'
      });
      var pm = passiveSents[0].match(PASSIVE_RE);
      flagged.push({
        category: 'Agentless Passive Voice',
        citation: profile.passiveCitation,
        verbatimOriginal: passiveSents[0].slice(0, 260),
        issue: 'Uses passive construction ("' + (pm ? pm[0] : 'passive verb') + '") without naming the legal actor responsible for performing the obligation.',
        suggestedRedraft: 'Specify the actor in active voice, e.g.: "The [Minister / Agency / applicant] must ' + (pm ? pm[1] : 'act') + '..."'
      });
      recommendations.push('Convert agentless passive verbs (' + passiveCount + ' found) into active voice naming the exact person or authority bearing the legal duty.');
    } else if (passiveCount > 0) {
      clarityScore -= 0.6;
      checklist.push({
        criterion: 'Active Voice & Identification of Responsible Actor',
        citation: profile.passiveCitation,
        status: 'WARN',
        findings: 'Found ' + passiveCount + ' passive verb construction(s) missing an explicit "by [actor]" agent; verify that the duty-bearer is unmistakable.'
      });
    } else {
      checklist.push({
        criterion: 'Active Voice & Identification of Responsible Actor',
        citation: profile.passiveCitation,
        status: 'PASS',
        findings: 'Provisions consistently use the active voice and identify the legal subject bearing each obligation or power.'
      });
    }

    // 6. Gender-Neutral Drafting
    var genderHits = [];
    sentences.forEach(function (s) {
      GENDERED_PATTERNS.forEach(function (pat) {
        var m = s.match(pat.re);
        if (m) genderHits.push({ term: m[0], desc: pat.desc, repl: pat.repl, sent: s });
      });
    });
    if (genderHits.length > 0) {
      var masc = genderHits.filter(function (h) { return h.desc.indexOf('masculine') !== -1 || h.desc.indexOf('occupational') !== -1; });
      conventionsScore -= masc.length > 0 ? Math.min(6.5, 2.5 + masc.length * 1.2) : 1.5;
      checklist.push({
        criterion: 'Gender-Neutral Drafting',
        citation: profile.genderCitation,
        status: masc.length > 0 ? 'FAIL' : 'WARN',
        findings: 'Found ' + genderHits.length + ' gender-specific expression(s): ' + genderHits.slice(0, 5).map(function (h) { return '"' + h.term + '"'; }).join(', ') + '.'
      });
      var gh = genderHits[0];
      flagged.push({
        category: 'Gendered Statutory Language',
        citation: profile.genderCitation,
        verbatimOriginal: gh.sent.slice(0, 260),
        issue: 'Uses ' + gh.desc + ' ("' + gh.term + '"). ' + profile.genderCitation + ' requires gender-neutral drafting.',
        suggestedRedraft: gh.sent.slice(0, 260).replace(new RegExp('\\b' + gh.term + '\\b', 'i'), '[' + gh.repl + ']')
      });
      recommendations.push('Replace gendered pronouns/nouns by repeating the defined noun or using gender-neutral terms (' + profile.genderCitation + ').');
    } else {
      checklist.push({
        criterion: 'Gender-Neutral Drafting',
        citation: profile.genderCitation,
        status: 'PASS',
        findings: 'Text is drafted in gender-neutral language with no masculine-generic pronouns or dated occupational titles.'
      });
    }

    // 7. Structure & Cross-References
    var hasSections = /(?:^|\n)\s*(?:Section|SECTION|Sec\.|Article|ARTICLE|Art\.|§|\d+\.)\s*\d*/.test(cleaned);
    var hasCommence = /\b(?:commencement|comes?\s+into\s+force|enter(?:s)?\s+into\s+force|effective\s+date|takes?\s+effect|Inkrafttreten|entrée\s+en\s+vigueur)\b/i.test(cleaned);
    if (!hasSections) structureScore -= 2.5;
    if (!hasCommence && wordCount > 120) structureScore -= 1.2;

    if (profile.recitalsPolicy === 'require_recitals_no_normative' && recitalLines.length === 0) {
      structureScore -= 2.0;
      conventionsScore -= 2.0;
      checklist.push({
        criterion: 'EU Formal Structure (Citations, Recitals & Enacting Formula)',
        citation: profile.structureCitation,
        status: 'WARN',
        findings: 'No EU Recitals ("Whereas:") or Citations ("Having regard to...") detected. Binding EU acts require citations and recitals preceding the enacting formula.'
      });
    } else if (profile.recitalsPolicy === 'forbid_recitals_in_statute' && recitalLines.length > 0) {
      structureScore -= 2.5;
      conventionsScore -= 2.0;
      checklist.push({
        criterion: 'Civil Law Statute Structure (No Recitals Inside Statutory Text)',
        citation: profile.structureCitation,
        status: 'FAIL',
        findings: 'Detected ' + recitalLines.length + ' recital/preamble clause(s) ("Whereas"). Under ' + profile.name + ', policy justifications belong strictly in the external explanatory memorandum.'
      });
      recommendations.push('Move "Whereas" recitals out of the statutory text into the accompanying Explanatory Memorandum (' + profile.structureCitation + ').');
    } else {
      var notes = [];
      notes.push(hasSections ? 'numbered sections/articles present' : 'missing clear section/article numbering');
      if (hasCommence) notes.push('commencement/entry-into-force provision present');
      else if (wordCount > 120) notes.push('no explicit commencement/effective-date clause found');
      checklist.push({
        criterion: 'Statutory Hierarchy, Structure & Final Provisions',
        citation: profile.structureCitation,
        status: (hasSections && (hasCommence || wordCount <= 120)) ? 'PASS' : 'WARN',
        findings: 'Structural audit: ' + notes.join(', ') + '.'
      });
    }

    var vagueXrefs = sentences.filter(function (s) { return VAGUE_XREF_RE.test(s); });
    if (vagueXrefs.length > 0) {
      defScore -= Math.min(2.5, 1.0 * vagueXrefs.length);
      structureScore -= 1.0;
      var vm = vagueXrefs[0].match(VAGUE_XREF_RE);
      var vterm = vm ? vm[0] : 'vague reference';
      checklist.push({
        criterion: 'Precision of Internal & External Cross-References',
        citation: profile.xrefCitation,
        status: 'WARN',
        findings: 'Found ' + vagueXrefs.length + ' relative/positional cross-reference(s) ("' + vterm + '"). Relative references break when intervening provisions are inserted by amendment.'
      });
      flagged.push({
        category: 'Imprecise Relative Cross-Reference',
        citation: profile.xrefCitation,
        verbatimOriginal: vagueXrefs[0].slice(0, 260),
        issue: 'Uses positional cross-reference ("' + vterm + '") instead of an explicit section or subsection number.',
        suggestedRedraft: vagueXrefs[0].slice(0, 260).replace(vterm, 'section [X](Y)')
      });
      recommendations.push('Replace positional references ("' + vterm + '") with exact section/subsection citations (' + profile.xrefCitation + ').');
    } else {
      checklist.push({
        criterion: 'Precision of Internal & External Cross-References',
        citation: profile.xrefCitation,
        status: 'PASS',
        findings: 'No fragile positional cross-references ("above", "below", "preceding section", "hereinbefore") detected.'
      });
    }

    var clamp = function (v) { return Math.round(Math.max(1.0, Math.min(10.0, v)) * 10) / 10; };
    var subscores = {
      clarity: clamp(clarityScore),
      normativePrecision: clamp(normativeScore),
      definitions: clamp(defScore),
      conventions: clamp(conventionsScore),
      structure: clamp(structureScore)
    };
    var weighted = subscores.clarity * 0.25 + subscores.normativePrecision * 0.25 + subscores.definitions * 0.20 + subscores.conventions * 0.15 + subscores.structure * 0.15;
    var scoreExact = clamp(weighted);
    var scoreInt = Math.max(1, Math.min(10, Math.round(scoreExact)));

    var passCount = checklist.filter(function (c) { return c.status === 'PASS'; }).length;
    var warnCount = checklist.filter(function (c) { return c.status === 'WARN'; }).length;
    var failCount = checklist.filter(function (c) { return c.status === 'FAIL'; }).length;
    var band = scoreExact >= 8.0 ? 'high compliance' : (scoreExact >= 5.5 ? 'moderate compliance with notable drafting issues' : 'low compliance requiring substantial redrafting');

    var execSummary = 'Evaluated ' + wordCount + ' words (' + sentenceCount + ' sentences, avg. ' + avgSentenceLen + ' words/sentence) against ' + profile.name + '. The draft achieves a compliance score of ' + scoreExact + '/10 (' + band + '), passing ' + passCount + ' of ' + checklist.length + ' criteria with ' + warnCount + ' warning(s) and ' + failCount + ' failure(s).';

    if (recommendations.length === 0) {
      recommendations.push('The text aligns well with ' + profile.name + '; verify cross-references and commencement dates prior to introduction.');
    }

    return {
      guidelineId: profile.id,
      guidelineName: profile.name,
      jurisdiction: profile.jurisdiction,
      tradition: profile.tradition,
      score: scoreInt,
      scoreExact: scoreExact,
      subscores: subscores,
      metrics: {
        wordCount: wordCount,
        sentenceCount: sentenceCount,
        avgSentenceLength: avgSentenceLen,
        maxSentenceLength: maxSentenceLen,
        shallCount: shallCount,
        mustCount: mustCount,
        mayCount: mayCount,
        passiveCount: passiveCount,
        archaicCount: archaicHits.length,
        genderedCount: genderHits.length,
        definitionCount: defSentences.length
      },
      executiveSummary: execSummary,
      checklist: checklist,
      flaggedExcerpts: flagged,
      recommendations: recommendations
    };
  }

  // -------------------------------------------------------------------------
  // UI Rendering & Event Wiring
  // -------------------------------------------------------------------------
  var lastResult = null;
  var lastComparisons = [];

  function escapeHtml(s) {
    return String(s || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function scoreClass(score) {
    if (score >= 8) return 'score-pass';
    if (score >= 5.5) return 'score-warn';
    return 'score-fail';
  }

  function statusBadgeClass(status) {
    if (status === 'PASS') return 'badge-current';
    if (status === 'WARN') return 'badge-dated';
    return 'badge-superseded';
  }

  function renderEvaluation(result, comparisons) {
    lastResult = result;
    lastComparisons = comparisons || [];
    var sec = document.getElementById('resultsSection');
    sec.hidden = false;

    document.getElementById('resJurisdiction').textContent = result.jurisdiction + ' · ' + result.tradition;
    document.getElementById('resTitle').textContent = 'Evaluation: ' + result.guidelineName;
    document.getElementById('resSubtitle').innerHTML = 'View full manual in catalog: <a href="guidelines/' + encodeURIComponent(result.guidelineId) + '/index.html">' + escapeHtml(result.guidelineName) + '</a>';

    var sBox = document.getElementById('scoreBox');
    sBox.className = 'score-box ' + scoreClass(result.scoreExact);
    document.getElementById('scoreDisplay').textContent = result.score + ' / 10';
    document.getElementById('scoreExactDisplay').textContent = 'Exact index: ' + result.scoreExact.toFixed(1) + ' / 10.0';

    document.getElementById('executiveSummary').textContent = result.executiveSummary;

    // Sub-scores
    var subLabels = [
      { key: 'clarity', label: 'Clarity & Plain Language (25%)' },
      { key: 'normativePrecision', label: 'Normative Verbs & Precision (25%)' },
      { key: 'definitions', label: 'Definitions & Cross-Refs (20%)' },
      { key: 'conventions', label: 'Guideline Conventions (15%)' },
      { key: 'structure', label: 'Structural Organization (15%)' }
    ];
    var subHtml = subLabels.map(function (item) {
      var val = result.subscores[item.key] || 0;
      var pct = Math.round(val * 10);
      return '<div class="subscore-card">' +
        '<div class="subscore-top"><span>' + escapeHtml(item.label) + '</span><strong>' + val.toFixed(1) + '/10</strong></div>' +
        '<div class="subscore-bar"><div class="subscore-fill ' + scoreClass(val) + '" style="width:' + pct + '%"></div></div>' +
        '</div>';
    }).join('');
    document.getElementById('subscoresContainer').innerHTML = subHtml;

    // Metrics
    var m = result.metrics;
    document.getElementById('metricsContainer').innerHTML = [
      '<span><strong>Words:</strong> ' + m.wordCount + '</span>',
      '<span><strong>Sentences:</strong> ' + m.sentenceCount + ' (avg ' + m.avgSentenceLength + 'w, max ' + m.maxSentenceLength + 'w)</span>',
      '<span><strong>"shall":</strong> ' + m.shallCount + '</span>',
      '<span><strong>"must":</strong> ' + m.mustCount + '</span>',
      '<span><strong>"may":</strong> ' + m.mayCount + '</span>',
      '<span><strong>Agentless passives:</strong> ' + m.passiveCount + '</span>',
      '<span><strong>Archaic terms:</strong> ' + m.archaicCount + '</span>',
      '<span><strong>Definitions checked:</strong> ' + m.definitionCount + '</span>'
    ].join(' · ');

    // Multi-guideline comparison table
    var compBlock = document.getElementById('multiCompareSection');
    var compTbody = document.querySelector('#multiCompareTable tbody');
    if (comparisons && comparisons.length > 1) {
      compBlock.hidden = false;
      compTbody.innerHTML = comparisons.map(function (c) {
        var active = c.guidelineId === result.guidelineId ? ' class="active-comp-row"' : '';
        return '<tr' + active + ' data-gid="' + escapeHtml(c.guidelineId) + '" style="cursor:pointer" title="Click to inspect detailed checklist for ' + escapeHtml(c.guidelineName) + '">' +
          '<td><strong>' + escapeHtml(c.guidelineName) + '</strong></td>' +
          '<td>' + escapeHtml(c.tradition) + '</td>' +
          '<td><span class="badge ' + (c.scoreExact >= 8 ? 'badge-current' : (c.scoreExact >= 5.5 ? 'badge-dated' : 'badge-superseded')) + '">' + c.score + '/10 (' + c.scoreExact.toFixed(1) + ')</span></td>' +
          '<td>' + c.subscores.clarity.toFixed(1) + '</td>' +
          '<td>' + c.subscores.normativePrecision.toFixed(1) + '</td>' +
          '<td>' + c.subscores.definitions.toFixed(1) + '</td>' +
          '<td>' + c.subscores.conventions.toFixed(1) + '</td>' +
          '<td>' + c.subscores.structure.toFixed(1) + '</td>' +
          '</tr>';
      }).join('');
      Array.prototype.slice.call(compTbody.querySelectorAll('tr')).forEach(function (tr) {
        tr.addEventListener('click', function () {
          var gid = tr.dataset.gid;
          document.getElementById('guidelineSelect').value = gid;
          var chosen = comparisons.filter(function (x) { return x.guidelineId === gid; })[0];
          if (chosen) renderEvaluation(chosen, comparisons);
        });
      });
    } else {
      compBlock.hidden = true;
    }

    // Checklist
    document.getElementById('checklistContainer').innerHTML = result.checklist.map(function (item) {
      return '<div class="check-row">' +
        '<span class="badge ' + statusBadgeClass(item.status) + '">' + escapeHtml(item.status) + '</span>' +
        '<div class="check-body">' +
        '<div><strong>' + escapeHtml(item.criterion) + '</strong> <span class="check-cite">(' + escapeHtml(item.citation) + ')</span></div>' +
        '<div class="check-findings">' + escapeHtml(item.findings) + '</div>' +
        '</div></div>';
    }).join('');

    // Flagged Excerpts
    var revContainer = document.getElementById('revisionsContainer');
    if (!result.flaggedExcerpts || result.flaggedExcerpts.length === 0) {
      revContainer.innerHTML = '<p class="pass-banner">No critical guideline violations flagged in the statutory text.</p>';
    } else {
      revContainer.innerHTML = result.flaggedExcerpts.map(function (ex) {
        return '<div class="revision-card">' +
          '<div class="rev-meta"><strong>' + escapeHtml(ex.category || 'Drafting Issue') + '</strong> · <span>' + escapeHtml(ex.citation || '') + '</span></div>' +
          '<div class="rev-orig"><span class="rev-tag rev-tag-orig">Original Clause</span> <code>"' + escapeHtml(ex.verbatimOriginal) + '"</code></div>' +
          '<div class="rev-issue"><strong>Why flagged:</strong> ' + escapeHtml(ex.issue) + '</div>' +
          '<div class="rev-redraft"><span class="rev-tag rev-tag-new">Proposed Redraft</span> <code>"' + escapeHtml(ex.suggestedRedraft) + '"</code></div>' +
          '</div>';
      }).join('');
    }

    // Recommendations
    document.getElementById('recommendationsList').innerHTML = result.recommendations.map(function (r) {
      return '<li>' + escapeHtml(r) + '</li>';
    }).join('');
  }

  async function runOptionalLlmCritique(billText, result) {
    var provider = document.getElementById('llmProvider').value;
    var apiKey = (document.getElementById('llmApiKey').value || '').trim();
    var llmBlock = document.getElementById('llmCritiqueBlock');
    var llmContent = document.getElementById('llmCritiqueContent');

    if (provider === 'none' || !apiKey) {
      llmBlock.hidden = true;
      return;
    }

    llmBlock.hidden = false;
    llmContent.innerHTML = '<p class="muted">Requesting deep parliamentary counsel critique from ' + escapeHtml(provider.toUpperCase()) + '…</p>';

    var prompt = 'You are Senior Parliamentary Counsel evaluating a drafted bill against ' + result.guidelineName + '.\n' +
      'Provide a concise 3-paragraph critique covering: (1) overarching structural and constitutional clarity, (2) specific normative or interpretive traps in the clauses, and (3) a polished redraft of the weakest provision.\n\n' +
      'DRAFT BILL:\n' + billText.slice(0, 12000);

    try {
      var replyText = '';
      if (provider === 'gemini') {
        var gemUrl = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=' + encodeURIComponent(apiKey);
        var r = await fetch(gemUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] })
        });
        if (!r.ok) throw new Error('Gemini API HTTP ' + r.status);
        var j = await r.json();
        replyText = (((j.candidates || [])[0] || {}).content || {}).parts[0].text || '';
      } else if (provider === 'openai') {
        var oaiRes = await fetch('https://api.openai.com/v1/chat/completions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + apiKey },
          body: JSON.stringify({
            model: 'gpt-4o-mini',
            temperature: 0.2,
            messages: [{ role: 'user', content: prompt }]
          })
        });
        if (!oaiRes.ok) throw new Error('OpenAI API HTTP ' + oaiRes.status);
        var oj = await oaiRes.json();
        replyText = oj.choices[0].message.content || '';
      }
      llmContent.innerHTML = '<div class="llm-prose">' + escapeHtml(replyText).replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>') + '</div>';
    } catch (err) {
      llmContent.innerHTML = '<p class="muted">AI provider call failed (' + escapeHtml(err.message) + '). The deterministic statutory rule audit above is complete.</p>';
    }
  }

  function triggerAudit() {
    var billText = document.getElementById('billText').value.trim();
    var guidelineId = document.getElementById('guidelineSelect').value;
    if (!billText) {
      alert('Please paste a drafted bill, upload a file, or select one of the sample bills.');
      return;
    }

    var checkedIds = [guidelineId];
    Array.prototype.slice.call(document.querySelectorAll('#compareCheckboxes input[type="checkbox"]:checked')).forEach(function (cb) {
      if (checkedIds.indexOf(cb.value) === -1) checkedIds.push(cb.value);
    });

    var primaryResult = evaluateBill(billText, guidelineId);
    var comparisons = checkedIds.map(function (cid) {
      return cid === guidelineId ? primaryResult : evaluateBill(billText, cid);
    });

    renderEvaluation(primaryResult, comparisons);
    runOptionalLlmCritique(billText, primaryResult);
    document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function downloadFile(filename, content, mime) {
    var blob = new Blob([content], { type: mime });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  function buildMarkdownReport(res, comparisons) {
    var lines = [
      '# Statutory Drafting Compliance Audit Report',
      '',
      '- **Target Guideline:** ' + res.guidelineName,
      '- **Jurisdiction / Tradition:** ' + res.jurisdiction + ' (' + res.tradition + ')',
      '- **Overall Compliance Score:** **' + res.score + ' / 10** (' + res.scoreExact.toFixed(1) + ' / 10.0)',
      '',
      '## Executive Summary',
      res.executiveSummary,
      '',
      '## Dimensional Sub-Scores',
      '- **Clarity & Plain Language:** ' + res.subscores.clarity.toFixed(1) + ' / 10',
      '- **Normative Verbs & Precision:** ' + res.subscores.normativePrecision.toFixed(1) + ' / 10',
      '- **Definitions & Cross-References:** ' + res.subscores.definitions.toFixed(1) + ' / 10',
      '- **Guideline Conventions:** ' + res.subscores.conventions.toFixed(1) + ' / 10',
      '- **Structural Organization:** ' + res.subscores.structure.toFixed(1) + ' / 10',
      ''
    ];
    if (comparisons && comparisons.length > 1) {
      lines.push('## Cross-Jurisdictional Comparison');
      lines.push('| Guideline | Score | Clarity | Normative | Definitions | Conventions | Structure |');
      lines.push('|---|---|---|---|---|---|---|');
      comparisons.forEach(function (c) {
        lines.push('| ' + c.guidelineName + ' | **' + c.score + '/10** (' + c.scoreExact.toFixed(1) + ') | ' + c.subscores.clarity.toFixed(1) + ' | ' + c.subscores.normativePrecision.toFixed(1) + ' | ' + c.subscores.definitions.toFixed(1) + ' | ' + c.subscores.conventions.toFixed(1) + ' | ' + c.subscores.structure.toFixed(1) + ' |');
      });
      lines.push('');
    }
    lines.push('## Checklist Breakdown');
    res.checklist.forEach(function (c) {
      lines.push('- **[' + c.status + '] ' + c.criterion + '** _((' + c.citation + '))_: ' + c.findings);
    });
    lines.push('');
    lines.push('## Flagged Provisions & Suggested Redrafts');
    if (!res.flaggedExcerpts.length) {
      lines.push('_No critical violations flagged._');
    } else {
      res.flaggedExcerpts.forEach(function (f) {
        lines.push('### ' + (f.category || 'Flagged Clause') + ' (' + f.citation + ')');
        lines.push('- **Original:** `' + f.verbatimOriginal + '`');
        lines.push('- **Issue:** ' + f.issue);
        lines.push('- **Proposed Redraft:** `' + f.suggestedRedraft + '`');
        lines.push('');
      });
    }
    lines.push('## Priority Recommendations');
    res.recommendations.forEach(function (r) {
      lines.push('1. ' + r);
    });
    return lines.join('\n');
  }

  // Event Listeners
  document.getElementById('fileUpload').addEventListener('change', function (e) {
    var file = e.target.files[0];
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function (evt) {
      document.getElementById('billText').value = evt.target.result;
      triggerAudit();
    };
    reader.readAsText(file);
  });

  document.getElementById('sampleSelect').addEventListener('change', function (e) {
    var val = e.target.value;
    if (val && SAMPLE_BILLS[val]) {
      document.getElementById('billText').value = SAMPLE_BILLS[val];
      if (val === 'eu_regulation') {
        document.getElementById('guidelineSelect').value = 'eu-joint-practical-guide';
      } else if (val === 'us_federal_bill') {
        document.getElementById('guidelineSelect').value = 'us-holc-guide-legislative-drafting';
      }
      triggerAudit();
    }
  });

  document.getElementById('runAuditBtn').addEventListener('click', triggerAudit);
  document.getElementById('clearAuditBtn').addEventListener('click', function () {
    document.getElementById('billText').value = '';
    document.getElementById('sampleSelect').value = '';
    document.getElementById('fileUpload').value = '';
    document.getElementById('resultsSection').hidden = true;
  });

  document.getElementById('exportMdBtn').addEventListener('click', function () {
    if (!lastResult) return;
    downloadFile('bill-compliance-audit-' + lastResult.guidelineId + '.md', buildMarkdownReport(lastResult, lastComparisons), 'text/markdown;charset=utf-8');
  });

  document.getElementById('exportJsonBtn').addEventListener('click', function () {
    if (!lastResult) return;
    downloadFile('bill-compliance-audit-' + lastResult.guidelineId + '.json', JSON.stringify({ primary: lastResult, comparisons: lastComparisons }, null, 2), 'application/json;charset=utf-8');
  });

  document.getElementById('printReportBtn').addEventListener('click', function () {
    window.print();
  });

  // Check URL parameters (?guideline=... or ?sample=...)
  var params = new URLSearchParams(window.location.search);
  var qGuideline = params.get('guideline');
  var qSample = params.get('sample');
  if (qGuideline) {
    var sel = document.getElementById('guidelineSelect');
    if (sel.querySelector('option[value="' + qGuideline + '"]')) {
      sel.value = qGuideline;
    }
  }
  if (qSample && SAMPLE_BILLS[qSample]) {
    document.getElementById('sampleSelect').value = qSample;
    document.getElementById('billText').value = SAMPLE_BILLS[qSample];
    triggerAudit();
  } else {
    // Load Sample 1 by default so the user immediately sees how the auditor works
    document.getElementById('sampleSelect').value = 'flawed_draft';
    document.getElementById('billText').value = SAMPLE_BILLS.flawed_draft;
    triggerAudit();
  }
})();

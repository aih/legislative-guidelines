"""Unit tests for the Legislative Drafting Guidelines catalog validator, bill evaluator, and site builder."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import evaluate_bill  # noqa: E402
import validate_catalog  # noqa: E402


def test_catalog_schema_valid():
    errors = validate_catalog.validate_catalog()
    assert errors == [], f"Catalog schema validation failed: {errors}"


def test_flawed_bill_scores_low_under_uk_opc():
    flawed = """
    A BILL ENTITLED AN ACT TO REGULATE ALGORITHMS.
    Section 1. Definitions.
    "System" means and includes any software and/or hardware, and any person operating such system shall register the same with the Chairman forthwith.
    Section 2. Offences.
    Whosoever deploys a system hereinafter described shall file a report in writing with the Chairman, and if he fails to do so, the permit thereof shall be deemed to be null and void and he shall cease and desist from operating the aforesaid system until such time as the fee is paid as provided in the preceding section.
    """
    res = evaluate_bill.evaluate_bill_deterministic(flawed, "uk-opc-drafting-guidance")
    assert 1 <= res["score"] <= 4
    assert res["metrics"]["shallCount"] >= 3
    assert res["metrics"]["archaicCount"] >= 4
    assert res["metrics"]["genderedCount"] >= 2
    assert any(c["status"] == "FAIL" for c in res["checklist"])
    assert len(res["flaggedExcerpts"]) >= 3


def test_modern_plain_bill_scores_high_under_uk_opc():
    clean_bill = """
    Short title
    1. This Act may be cited as the Algorithmic Transparency Act 2026.

    Commencement
    2. This Act comes into force on 1 January 2027.

    Interpretation
    3. In this Act—
    "algorithmic system" means an automated computational process used to make an administrative decision;
    "Commissioner" means the Information Commissioner.

    Public Register
    4. (1) The Commissioner must establish and maintain a Public Register of Algorithmic Systems.
    (2) A public authority must register each algorithmic system before deploying it.
    """
    res = evaluate_bill.evaluate_bill_deterministic(clean_bill, "uk-opc-drafting-guidance")
    assert res["score"] >= 9
    assert res["metrics"]["shallCount"] == 0
    assert all(c["status"] == "PASS" for c in res["checklist"])


def test_eu_recital_normative_trap_detected():
    eu_draft = """
    REGULATION (EU) 2026/100 OF THE EUROPEAN PARLIAMENT AND OF THE COUNCIL
    Having regard to the Treaty on the Functioning of the European Union,
    Whereas:
    (1) Harmonised rules are necessary across the internal market.
    (2) Member States shall impose administrative fines of EUR 500,000 on non-compliant operators.
    HAVE ADOPTED THIS REGULATION:
    Article 1
    This Regulation shall apply to public sector bodies.
    Article 2
    This Regulation shall enter into force on 1 January 2027.
    """
    res = evaluate_bill.evaluate_bill_deterministic(eu_draft, "eu-joint-practical-guide")
    recital_checks = [c for c in res["checklist"] if "Recital" in c["criterion"]]
    assert recital_checks and recital_checks[0]["status"] == "FAIL"


def test_multi_guideline_comparison_diverges_on_shall():
    bill_with_shall = """
    Article 1
    1. The Agency shall establish a public registry of automated systems.
    2. An operator shall submit an annual compliance report to the Agency.
    Article 2
    This Act enters into force on 1 January 2027.
    """
    comp = evaluate_bill.compare_bill_across_guidelines(
        bill_with_shall,
        ["uk-opc-drafting-guidance", "us-holc-guide-legislative-drafting"],
    )
    scores = {c["guidelineId"]: c["scoreExact"] for c in comp["comparisons"]}
    # US HOLC allows 'The Agency shall...' (animate actor), while UK OPC penalizes 'shall'
    assert scores["us-holc-guide-legislative-drafting"] > scores["uk-opc-drafting-guidance"]

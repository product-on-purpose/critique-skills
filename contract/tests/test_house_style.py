"""House style: every prose field rejects U+2014 EM DASH and U+2013 EN
DASH, enforced at the contract boundary (contract/README.md, "No em
dash, no en dash").

The dash characters below are built with chr(), never written as literal
characters, so this file itself carries none of the punctuation its
tests exist to reject.
"""

from __future__ import annotations

import pytest

from contract.validate import validate_document, validate_finding

from .fixtures import example_disposition_log, example_envelope, example_finding

EM_DASH = chr(0x2014)
EN_DASH = chr(0x2013)


@pytest.mark.parametrize("dash", [EM_DASH, EN_DASH], ids=["em-dash", "en-dash"])
def test_em_and_en_dash_rejected_in_finding_violation(dash):
    finding = example_finding()
    finding["violation"] = f"Contrast ratio too low {dash} well below the AA minimum"

    issues = validate_finding(finding)

    assert issues, f"expected {dash!r} to be rejected in 'violation'"
    assert any(issue.path == "violation" for issue in issues)


@pytest.mark.parametrize("dash", [EM_DASH, EN_DASH], ids=["em-dash", "en-dash"])
def test_em_and_en_dash_rejected_in_envelope_artifact_path(dash):
    envelope = example_envelope()
    envelope["run"]["artifact"] = f"docs/prd{dash}notes.md"

    result = validate_document(envelope)

    assert not result.ok
    assert any(issue.path == "run.artifact" for issue in result.errors)


def test_plain_hyphen_is_not_rejected():
    finding = example_finding()
    finding["violation"] = "Contrast ratio 2.9:1 - below the 4.5:1 AA minimum"

    issues = validate_finding(finding)

    assert issues == []


def test_em_dash_rejected_in_disposition_note():
    log = example_disposition_log()
    log["dispositions"][0]["note"] = f"Confirmed{EM_DASH}no dispute here."

    result = validate_document(log)

    assert not result.ok
    assert any(issue.path == "dispositions[0].note" for issue in result.errors)

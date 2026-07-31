"""AC-2: the methodology's example finding and envelope validate, and
nine deliberately malformed finding variants (one per required field)
each fail with an error naming the missing field."""

from __future__ import annotations

import copy

import pytest

from contract.validate import validate_document, validate_finding

from .fixtures import FINDING_REQUIRED_FIELDS, example_envelope, example_finding


def test_example_finding_validates():
    issues = validate_finding(example_finding())
    assert issues == []


def test_example_envelope_validates():
    result = validate_document(example_envelope())
    assert result.ok, result.errors
    assert result.errors == []
    assert result.warnings == []


@pytest.mark.parametrize("field", FINDING_REQUIRED_FIELDS)
def test_malformed_finding_missing_field_fails_naming_the_field(field):
    finding = example_finding()
    del finding[field]

    issues = validate_finding(finding)

    assert len(issues) >= 1
    named = [issue for issue in issues if issue.path == field]
    assert named, (
        f"expected an issue naming '{field}', got: {[str(i) for i in issues]}"
    )
    assert field in named[0].message


@pytest.mark.parametrize("field", FINDING_REQUIRED_FIELDS)
def test_malformed_finding_fails_the_full_envelope_too(field):
    finding = example_finding()
    del finding[field]
    envelope = example_envelope()
    envelope["findings"] = [finding]

    result = validate_document(envelope)

    assert not result.ok
    named = [issue for issue in result.errors if issue.path == f"findings[0].{field}"]
    assert named, (
        f"expected an issue naming 'findings[0].{field}', got: "
        f"{[str(i) for i in result.errors]}"
    )


def test_valid_finding_is_not_accidentally_mutated_by_validation():
    finding = example_finding()
    before = copy.deepcopy(finding)
    validate_finding(finding)
    assert finding == before

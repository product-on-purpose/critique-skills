"""AC-3: the disposition log schema, and rule 7 (disposition entries
resolve against the referenced envelope, when it is available)."""

from __future__ import annotations

from contract.validate import document_kind, validate_document

from .fixtures import example_disposition_log, example_envelope


def test_sample_disposition_log_validates():
    result = validate_document(example_disposition_log())
    assert result.ok, result.errors
    assert result.errors == []


def test_disposition_log_dispatches_by_dispositions_key():
    assert document_kind(example_disposition_log()) == "dispositionLog"
    assert document_kind(example_envelope()) == "envelope"


def test_disposition_entries_resolve_against_referenced_envelope():
    log = example_disposition_log()
    result = validate_document(log, referenced_envelope=example_envelope())
    assert result.ok, result.errors


def test_disposition_entries_resolve_flags_unknown_finding_id():
    log = example_disposition_log()
    log["dispositions"][0]["finding_id"] = "F-999"

    result = validate_document(log, referenced_envelope=example_envelope())

    assert not result.ok
    assert any(i.rule == "disposition-entries-resolve" for i in result.errors)
    assert any("F-999" in i.message for i in result.errors)


def test_disposition_entries_resolve_flags_criterion_mismatch():
    log = example_disposition_log()
    log["dispositions"][0]["criterion"] = "NNG-H4"

    result = validate_document(log, referenced_envelope=example_envelope())

    assert not result.ok
    assert any(i.rule == "disposition-entries-resolve" for i in result.errors)


def test_disposition_entries_resolve_skipped_without_referenced_envelope():
    """Rule 7 only fires "whenever the referenced envelope is available"."""
    log = example_disposition_log()
    log["dispositions"][0]["finding_id"] = "F-999"

    result = validate_document(log)

    assert result.ok, result.errors

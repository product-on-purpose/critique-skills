"""Contract 1.1.0 (ADR 0042): the disposition log's iteration field, the
revision brief as a fourth document type, and the reserved selector's
deprecation. Also N4 (the revision-loop chain) spec AC-5: every 1.0.0
disposition log committed under examples/ still validates unchanged."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from contract.validate import document_kind, load_schema, validate_document
from skills._shared.envelope import CONTRACT_VERSION

from .fixtures import (
    example_disposition_log,
    example_envelope,
    example_finding,
    example_revision_brief,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_LOGS = sorted(REPO_ROOT.glob("examples/*/dispositions.json"))


# --------------------------------------------------------------------------
# Version stamps
# --------------------------------------------------------------------------


def test_schema_header_and_emitted_envelopes_agree_on_1_1_0():
    schema = load_schema()
    assert "contract version 1.1.0" in schema["description"]
    assert schema["$comment"].startswith("Contract version 1.1.0.")
    assert CONTRACT_VERSION == "1.1.0"


def test_contract_readme_states_1_1_0():
    readme = (REPO_ROOT / "contract" / "README.md").read_text(encoding="utf-8")
    assert "contract version **1.1.0**" in readme


# --------------------------------------------------------------------------
# AC-5: the iteration field is optional and additive
# --------------------------------------------------------------------------


def test_seven_committed_example_logs_exist():
    # The N4 spec counts seven, one per shipped skill. If a skill is added
    # this number moves with it; if one vanishes the AC below is weaker.
    assert len(EXAMPLE_LOGS) == 7


@pytest.mark.parametrize("path", EXAMPLE_LOGS, ids=lambda p: p.parent.name)
def test_committed_1_0_0_logs_still_validate(path: Path):
    log = json.loads(path.read_text(encoding="utf-8"))
    assert log["contract_version"] == "1.0.0"
    assert "iteration" not in log
    result = validate_document(log)
    assert result.ok, result.errors


def test_log_without_iteration_validates():
    assert validate_document(example_disposition_log()).ok


@pytest.mark.parametrize("iteration", [1, 2, 3, 4, 10])
def test_log_with_integer_iteration_validates(iteration: int):
    # No schema maximum (N4 decision D4): the chain's stop-check enforces 3.
    log = example_disposition_log()
    log["contract_version"] = "1.1.0"
    log["iteration"] = iteration
    result = validate_document(log)
    assert result.ok, result.errors


@pytest.mark.parametrize("iteration", [0, -1, "2", None])
def test_log_with_invalid_iteration_is_rejected(iteration):
    log = example_disposition_log()
    log["iteration"] = iteration
    assert not validate_document(log).ok


def test_log_iteration_written_as_float_is_rejected_by_rule_6():
    log = example_disposition_log()
    log["iteration"] = 2.0
    result = validate_document(log)
    assert not result.ok
    assert any(
        i.rule == "integer-literal" and i.path == "iteration" for i in result.errors
    )


# --------------------------------------------------------------------------
# The revision brief
# --------------------------------------------------------------------------


def test_revision_brief_dispatches_by_items_key():
    assert document_kind(example_revision_brief()) == "revisionBrief"
    assert document_kind(example_disposition_log()) == "dispositionLog"
    assert document_kind(example_envelope()) == "envelope"


def test_dispositions_key_wins_over_items_key():
    log = example_disposition_log()
    log["items"] = []
    assert document_kind(log) == "dispositionLog"
    # And the schema rejects the stray key on a disposition log.
    assert not validate_document(log).ok


def test_revision_brief_validates():
    result = validate_document(example_revision_brief())
    assert result.ok, result.errors


def test_revision_brief_resolves_against_referenced_envelope():
    result = validate_document(
        example_revision_brief(), referenced_envelope=example_envelope()
    )
    assert result.ok, result.errors


@pytest.mark.parametrize("missing", ["envelope", "iteration", "items"])
def test_revision_brief_requires_its_three_fields(missing: str):
    brief = example_revision_brief()
    del brief[missing]
    if missing == "items":
        # Without 'items' the document dispatches as an envelope and fails
        # that shape instead; either way it is not valid.
        assert document_kind(brief) == "envelope"
    assert not validate_document(brief).ok


@pytest.mark.parametrize("missing", ["finding_id", "criterion", "location", "fix"])
def test_revision_brief_item_requires_its_four_fields(missing: str):
    brief = example_revision_brief()
    del brief["items"][0][missing]
    assert not validate_document(brief).ok


def test_revision_brief_rejects_unknown_properties():
    brief = example_revision_brief()
    brief["note"] = "extra"
    assert not validate_document(brief).ok
    brief = example_revision_brief()
    brief["items"][0]["severity"] = 3
    assert not validate_document(brief).ok


def test_empty_revision_brief_is_rejected():
    brief = example_revision_brief()
    brief["items"] = []
    assert not validate_document(brief).ok


def test_revision_brief_iteration_float_is_rejected_by_rule_6():
    brief = example_revision_brief()
    brief["iteration"] = 1.0
    result = validate_document(brief)
    assert any(i.rule == "integer-literal" for i in result.errors)


def test_revision_brief_item_with_unknown_finding_id_fails_rule_7():
    brief = example_revision_brief()
    brief["items"][0]["finding_id"] = "F-999"
    result = validate_document(brief, referenced_envelope=example_envelope())
    assert not result.ok
    assert any(
        i.rule == "disposition-entries-resolve" and "F-999" in i.message
        for i in result.errors
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("criterion", "WCAG-1.4.11"),
        ("location", "Footer, legal line"),
        ("fix", "Use a darker gray"),
    ],
)
def test_revision_brief_item_that_disagrees_with_its_finding_fails_rule_7(
    field: str, value: str
):
    brief = example_revision_brief()
    brief["items"][0][field] = value
    result = validate_document(brief, referenced_envelope=example_envelope())
    assert any(i.path == f"items[0].{field}" for i in result.errors)


def test_revision_brief_dash_is_rejected_by_rule_9():
    brief = example_revision_brief()
    brief["items"][0]["fix"] = "Darken the text — to #595959"
    assert not validate_document(brief).ok


def test_revision_brief_impossible_timestamp_fails_rule_10():
    brief = example_revision_brief()
    brief["envelope"]["timestamp"] = "2026-02-31T00:00:00Z"
    result = validate_document(brief)
    assert any(i.rule == "calendar-valid-timestamp" for i in result.errors)


# --------------------------------------------------------------------------
# selector: deprecated, not deleted
# --------------------------------------------------------------------------


def test_selector_is_marked_deprecated():
    selector = load_schema()["$defs"]["selector"]
    assert selector["deprecated"] is True
    assert selector["description"].startswith("DEPRECATED as of contract 1.1.0")


def test_document_carrying_a_selector_still_validates():
    finding = example_finding()
    finding["selector"] = {"css": "main > p:nth-of-type(2)"}
    envelope = example_envelope()
    envelope["findings"] = [finding]
    result = validate_document(envelope)
    assert result.ok, result.errors

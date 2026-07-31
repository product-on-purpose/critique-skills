"""Tests for skills/_shared/findings.py."""

from __future__ import annotations

from skills._shared.findings import RawFinding, to_finding_dict


def _raw(**overrides) -> RawFinding:
    fields = dict(
        criterion="TOY-ACTIVE",
        severity=2,
        location="Service window, second paragraph, first sentence",
        evidence="The meter log is reviewed before the shift ends.",
        violation="Passive voice with the acting party deleted.",
        fix="Restate with the actor as subject: 'The field crew reviews the meter log.'",
    )
    fields.update(overrides)
    return RawFinding(**fields)


def test_to_finding_dict_forces_scripted_lane_and_high_confidence():
    finding = to_finding_dict(_raw(), finding_id="F-001")

    assert finding["lane"] == "scripted"
    assert finding["confidence"] == "high"
    assert finding["id"] == "F-001"


def test_to_finding_dict_carries_every_required_field():
    raw = _raw()
    finding = to_finding_dict(raw, finding_id="F-002")

    assert finding["criterion"] == raw.criterion
    assert finding["severity"] == raw.severity
    assert finding["location"] == raw.location
    assert finding["evidence"] == raw.evidence
    assert finding["violation"] == raw.violation
    assert finding["fix"] == raw.fix


def test_to_finding_dict_omits_optional_fields_when_absent():
    finding = to_finding_dict(_raw(), finding_id="F-003")

    assert "instances" not in finding
    assert "rubric_source" not in finding
    assert "selector" not in finding


def test_to_finding_dict_defaults_to_scripted_high_confidence():
    finding = to_finding_dict(_raw(), finding_id="F-005")

    assert finding["lane"] == "scripted"
    assert finding["confidence"] == "high"


def test_to_finding_dict_carries_an_explicit_judged_lane_through():
    raw = _raw(lane="judged", confidence="medium")

    finding = to_finding_dict(raw, finding_id="F-006")

    assert finding["lane"] == "judged"
    assert finding["confidence"] == "medium"


def test_to_finding_dict_carries_instances_and_rubric_source_when_present():
    raw = _raw(
        instances=({"location": "s2.p1"}, {"location": "s3.p1"}),
        rubric_source="byor",
        selector={"css": "#hero"},
    )

    finding = to_finding_dict(raw, finding_id="F-004")

    assert finding["instances"] == [{"location": "s2.p1"}, {"location": "s3.p1"}]
    assert finding["rubric_source"] == "byor"
    assert finding["selector"] == {"css": "#hero"}

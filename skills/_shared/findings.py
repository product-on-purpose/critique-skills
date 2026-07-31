"""RawFinding: what a skill's check function returns, and the one place
a RawFinding is turned into a full contract finding.

A check function never sets `id` itself: envelope.py assigns ids once
every RawFinding from every criterion check has been collected and
ranked, so ids are stable under the same determinism rule the rest of
the envelope follows.

`lane` and `confidence` default to "scripted" and "high", which is all
`scripts/checks.py` ever needs (methodology section 5: "confidence:
Applies to the judged lane. Scripted findings are always high or they
are bugs."). A check function that is not certain of a finding does not
belong in the scripted lane at all; see docs/internal/skill-template.md,
"Scripted lane discipline." The two fields are still parameters, not
hardcoded, so `skills/_shared/envelope.py`'s rank-and-bound and summary
logic can also serve a future judged-lane caller (the critic subagent,
S-06) that merges both lanes before bounding; contract.validate.py
still rejects a "scripted" finding carrying anything but "high"
confidence, so a caller cannot use this escape hatch to produce an
invalid document, only a genuinely judged one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class RawFinding:
    """One breach detected by a check, before an id is attached. Field
    meanings are exactly the contract's (contract/critique-contract.
    schema.json, $defs/finding); see docs/explanation/methodology.md
    section 5 for the field contracts (location navigable unaided,
    evidence quoted or measured, violation names the breach, fix is
    actionable) that a schema cannot check but a check function can and
    must still honor.
    """

    criterion: str
    severity: int
    location: str
    evidence: str
    violation: str
    fix: str
    lane: str = "scripted"
    confidence: str = "high"
    instances: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    rubric_source: str | None = None
    selector: Mapping[str, Any] | None = None


def to_finding_dict(raw: RawFinding, *, finding_id: str) -> dict[str, Any]:
    """Materialize one RawFinding into a full contract finding dict,
    carrying `raw.lane` and `raw.confidence` through unchanged."""
    finding: dict[str, Any] = {
        "id": finding_id,
        "criterion": raw.criterion,
        "lane": raw.lane,
        "severity": raw.severity,
        "location": raw.location,
        "evidence": raw.evidence,
        "violation": raw.violation,
        "fix": raw.fix,
        "confidence": raw.confidence,
    }
    if raw.instances:
        finding["instances"] = [dict(instance) for instance in raw.instances]
    if raw.rubric_source is not None:
        finding["rubric_source"] = raw.rubric_source
    if raw.selector is not None:
        finding["selector"] = dict(raw.selector)
    return finding

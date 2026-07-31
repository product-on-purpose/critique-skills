"""Shared fixtures for the bench.metrics test suite: manifest and
envelope builders, and a small worked markdown artifact used across
several test modules. Self-contained on purpose (no dependency on
`contract.tests` or `bench.generator`), matching bench.metrics' own rule
of reading only manifests and envelopes.
"""

from __future__ import annotations

import hashlib
from typing import Any

ARTIFACT_SHA_PLACEHOLDER = "0" * 64

# A small worked markdown artifact, in the style of
# bench/generator/README.md's `toy` domain worked example, small enough to
# reason about by eye. Document-wide paragraph numbering: 1 and 2 under
# "Service window", 3 under "Meter replacement", 4 under "Billing
# adjustments".
TOY_MD = (
    "# Field operations notice\n"
    "\n"
    "## Service window\n"
    "\n"
    "The field crew reviews the meter log before the shift ends. Crews that "
    "finish early return the vehicle to the depot.\n"
    "\n"
    "The outage report is filed within one business day. Any reading "
    "outside the expected band goes to the duty engineer.\n"
    "\n"
    "## Meter replacement\n"
    "\n"
    "The records clerk signs off on the service ticket before the shift "
    "ends. A replacement meter carries its own serial number.\n"
    "\n"
    "## Billing adjustments\n"
    "\n"
    "It may possibly be the case that the billing team closes the rate "
    "table at the start of each week. Adjustments raised after that point "
    "land in the following cycle.\n"
)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def manifest(
    *,
    artifact: str = "bench/corpus/toy/toy-001.md",
    artifact_text: str = TOY_MD,
    domain: str = "toy",
    artifact_type: str = "markdown-prose",
    recipe: str = "toy-001",
    seed: str = "0" * 32,
    defects: list[dict] | None = None,
) -> dict[str, Any]:
    return {
        "manifest_version": "1.0.0",
        "artifact": artifact,
        "artifact_sha256": sha256_hex(artifact_text),
        "seed": seed,
        "domain": domain,
        "artifact_type": artifact_type,
        "recipe": recipe,
        "defects": defects or [],
    }


def paragraph_defect(
    criterion: str,
    paragraph: int,
    *,
    heading_path: list[str] | None = None,
    severity: int = 2,
    description: str = "A defect planted for testing, described in meta-language.",
) -> dict[str, Any]:
    location: dict[str, Any] = {
        "kind": "paragraph",
        "text": f"paragraph {paragraph}",
        "paragraph": paragraph,
    }
    if heading_path:
        location["heading_path"] = heading_path
    return {
        "criterion": criterion,
        "location": location,
        "severity_expected": severity,
        "description": description,
    }


def heading_defect(
    criterion: str, heading_path: list[str], *, severity: int = 3,
    description: str = "A structural defect planted for testing.",
) -> dict[str, Any]:
    return {
        "criterion": criterion,
        "location": {
            "kind": "heading-path",
            "text": f"the {heading_path[-1]} heading",
            "heading_path": heading_path,
        },
        "severity_expected": severity,
        "description": description,
    }


def finding(
    *,
    finding_id: str = "F-001",
    criterion: str = "TOY-ACTIVE",
    location: str = "paragraph 1",
    severity: int = 2,
    lane: str = "judged",
    confidence: str = "medium",
    instances: list[dict] | None = None,
) -> dict[str, Any]:
    built: dict[str, Any] = {
        "id": finding_id,
        "criterion": criterion,
        "lane": lane,
        "severity": severity,
        "location": location,
        "evidence": "Evidence text for testing.",
        "violation": "Violation text for testing.",
        "fix": "Fix text for testing.",
        "confidence": confidence,
    }
    if instances:
        built["instances"] = instances
    return built


def envelope(
    *,
    findings: list[dict] | None = None,
    artifact: str = "bench/corpus/toy/toy-001.md",
    artifact_sha256: str = ARTIFACT_SHA_PLACEHOLDER,
    skill: str = "critique-toy",
    model: str = "claude-sonnet-4-5-20250929",
    timestamp: str = "2026-07-31T00:00:00Z",
    rubrics: list[str] | None = None,
    skill_version: str = "0.1.0",
) -> dict[str, Any]:
    findings = findings or []
    counts = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0}
    for f in findings:
        counts[str(f["severity"])] += 1
    return {
        "run": {
            "skill": skill,
            "skill_version": skill_version,
            "contract_version": "1.0.0",
            "artifact": artifact,
            "artifact_sha256": artifact_sha256,
            "model": model,
            "timestamp": timestamp,
            "rubrics": rubrics or ["TOY"],
        },
        "findings": findings,
        "summary": {
            "by_severity": counts,
            "suppressed_count": 0,
            "gate": "fail" if (counts["4"] > 0 or counts["3"] > 0) else "pass",
            "severity_3_threshold": 0,
        },
    }

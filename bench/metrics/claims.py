"""Claims: the `(criterion, location)` unit recall, precision, and
consistency are all computed over (bench/README.md, "Claims and
assignment"). A finding with no `instances` contributes one claim; a
finding with n instances contributes n+1 claims, one per location. This
makes the contract's two ways to express a recurring breach, n separate
findings or one finding with an instance list, score identically.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Claim:
    criterion: str
    location: str
    finding_id: str
    severity: int


def claims_from_envelope(envelope: dict) -> list[Claim]:
    """Every claim an envelope's `findings[]` makes. Suppressed findings
    are never in `findings[]` to begin with (contract/README.md), so they
    never contribute a claim, matching bench/README.md's precision
    definition: "suppressed findings are excluded, because a suppressed
    finding is never shown to a user and cannot mislead one."
    """
    claims: list[Claim] = []
    for finding in envelope.get("findings", []):
        criterion = finding["criterion"]
        finding_id = finding["id"]
        severity = finding["severity"]
        claims.append(Claim(criterion=criterion, location=finding["location"], finding_id=finding_id, severity=severity))
        for instance in finding.get("instances") or []:
            claims.append(
                Claim(criterion=criterion, location=instance["location"], finding_id=finding_id, severity=severity)
            )
    return claims

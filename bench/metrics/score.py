"""Recall, precision, the clean-artifact false-positive rate, and
consistency, computed exactly as bench/README.md's "Metrics" section
defines them, from a manifest plus one or more contract-valid run
envelopes for the artifact the manifest describes.

Pooling convention (this module's own documented choice; bench/README.md's
metric definitions do not address repeated runs of the same artifact).
Recall, precision, and the clean-artifact rate are aggregated across every
scored envelope matched to an artifact, not per envelope: an artifact
scored by k runs contributes its defects and claims k times, once per run.
Pooled this way, an aggregate is a defect-weighted, run-weighted mean of
the per-run ratios, with no need to designate one run as canonical. This
is offered in the same spirit as the greedy-vs-maximum-matching
simplification bench/README.md itself names and accepts: documented here
so a reader knows exactly what was decided and why, rather than having to
infer it from the arithmetic.

Domain-level consistency is the equal-weight mean of each scored
artifact's own per-artifact consistency (bench/README.md defines
consistency per artifact, over that artifact's k runs; it does not say how
to roll several artifacts' consistency into one domain figure, so this
module picks the plainest aggregation and names it here).
"""

from __future__ import annotations

from dataclasses import dataclass

from bench.metrics import claims as claims_mod
from bench.metrics import locate, match


@dataclass(frozen=True, slots=True)
class ArtifactScore:
    """What one (manifest, envelope) pair contributes to recall,
    precision, and the clean-artifact false-positive rate."""

    artifact: str
    domain: str
    artifact_type: str
    is_clean: bool
    defects_total: int
    defects_matched: int
    claims_total: int
    claims_matched: int
    unresolvable_claims: int


def score_artifact(manifest: dict, envelope: dict, artifact_text: str) -> ArtifactScore:
    """Score one run envelope against the manifest of the artifact it was
    run on.

    `artifact_text` is the artifact's own bytes, decoded, so the resolver
    can re-derive the artifact's structure "using the artifact itself as
    the vocabulary" (bench/README.md). The caller is responsible for
    having confirmed identity before calling this: that `artifact_text`
    hashes to `manifest["artifact_sha256"]`, and that
    `envelope["run"]["artifact_sha256"] == manifest["artifact_sha256"]`
    (the join key). This function does not re-derive either check, only
    trusts the caller matched the right pair, so it stays a pure function
    of its three arguments and is cheap to unit test.
    """
    artifact_type = manifest["artifact_type"]
    defects = manifest["defects"]
    claim_list = claims_mod.claims_from_envelope(envelope)

    parsed = locate.parse_artifact(artifact_type, artifact_text)
    resolved = [
        locate.resolve_location(parsed, artifact_type, c.location, artifact_path=manifest["artifact"])
        for c in claim_list
    ]
    unresolvable = sum(1 for r in resolved if not r.resolvable)

    matched_defects, matched_claims = match.match_claims_to_defects(
        parsed, artifact_type, claim_list, resolved, defects
    )

    return ArtifactScore(
        artifact=manifest["artifact"],
        domain=manifest["domain"],
        artifact_type=artifact_type,
        is_clean=(len(defects) == 0),
        defects_total=len(defects),
        defects_matched=len(matched_defects),
        claims_total=len(claim_list),
        claims_matched=len(matched_claims),
        unresolvable_claims=unresolvable,
    )


@dataclass(frozen=True, slots=True)
class MetricValue:
    """A ratio plus the integers it was formed from. `value` is None when
    the denominator is zero, meaning the metric is not computable rather
    than zero (bench/README.md: "A clean artifact contributes zero to
    both sides, so it is excluded from the denominator rather than scored
    as a perfect or a failed run.")."""

    value: float | None
    numerator: int
    denominator: int


def _ratio(numerator: int, denominator: int) -> MetricValue:
    value = (numerator / denominator) if denominator else None
    return MetricValue(value=value, numerator=numerator, denominator=denominator)


def aggregate_recall(scores: list[ArtifactScore]) -> MetricValue:
    """`recall = matched planted defects / total planted defects`, over
    seeded artifacts only."""
    seeded = [s for s in scores if not s.is_clean]
    return _ratio(sum(s.defects_matched for s in seeded), sum(s.defects_total for s in seeded))


def aggregate_precision(scores: list[ArtifactScore]) -> MetricValue:
    """`precision = claims matched to a planted defect / all claims
    emitted`, over every artifact, clean ones included."""
    return _ratio(sum(s.claims_matched for s in scores), sum(s.claims_total for s in scores))


def aggregate_clean_fp_rate(scores: list[ArtifactScore]) -> MetricValue:
    """`clean_fp_rate = claims on clean artifacts / number of clean
    artifacts`, a mean claims-per-clean-artifact."""
    clean = [s for s in scores if s.is_clean]
    return _ratio(sum(s.claims_total for s in clean), len(clean))


@dataclass(frozen=True, slots=True)
class ConsistencyScore:
    """k runs of the same skill against the same artifact
    (bench/README.md, "Consistency"). `runs` need not be exactly five:
    it records how many envelopes were actually available, so a caller
    can see whether k=5 was met."""

    artifact: str
    runs: int
    pairs: int
    consistency: float | None
    consistency_exact: float | None


def score_consistency(manifest: dict, envelopes: list[dict], artifact_text: str) -> ConsistencyScore:
    """Mean pairwise Jaccard, tolerance-aware and exact, over the
    `C(k, 2)` unordered pairs of `envelopes`. Fewer than two envelopes
    yields no computable consistency (`None`, not 1.0: there is nothing
    to compare, which is a different claim from "every comparison
    agreed")."""
    artifact_type = manifest["artifact_type"]
    parsed = locate.parse_artifact(artifact_type, artifact_text)
    claim_sets = [claims_mod.claims_from_envelope(e) for e in envelopes]
    n = len(claim_sets)
    if n < 2:
        return ConsistencyScore(artifact=manifest["artifact"], runs=n, pairs=0, consistency=None, consistency_exact=None)

    tolerant_values: list[float] = []
    exact_values: list[float] = []
    for i in range(n):
        for j in range(i + 1, n):
            tolerant_values.append(
                match.jaccard_tolerant(
                    parsed, artifact_type, claim_sets[i], claim_sets[j], artifact_path=manifest["artifact"]
                )
            )
            exact_values.append(
                match.jaccard_exact(
                    parsed, artifact_type, claim_sets[i], claim_sets[j], artifact_path=manifest["artifact"]
                )
            )
    pairs = len(tolerant_values)
    return ConsistencyScore(
        artifact=manifest["artifact"],
        runs=n,
        pairs=pairs,
        consistency=sum(tolerant_values) / pairs,
        consistency_exact=sum(exact_values) / pairs,
    )


def _aggregate_mean(values: list[float | None]) -> MetricValue:
    usable = [v for v in values if v is not None]
    if not usable:
        return MetricValue(value=None, numerator=0, denominator=0)
    return MetricValue(value=sum(usable) / len(usable), numerator=len(usable), denominator=len(usable))


def aggregate_consistency(scores: list[ConsistencyScore]) -> MetricValue:
    """Equal-weight mean of every scored artifact's `consistency`, over
    artifacts that had at least two runs to compare."""
    return _aggregate_mean([s.consistency for s in scores])


def aggregate_consistency_exact(scores: list[ConsistencyScore]) -> MetricValue:
    return _aggregate_mean([s.consistency_exact for s in scores])


def round3(value: float | None) -> float | None:
    """Round a ratio to three decimal places, formed once, at the end,
    per bench/README.md, "Metrics": "All arithmetic accumulates in
    integers; a ratio is formed once, at the end, and reported to three
    decimal places." Never applied before a ratio is final: aggregation
    functions above return exact fractions built from integer sums, and
    this is called only when serializing a value for display."""
    return None if value is None else round(value, 3)

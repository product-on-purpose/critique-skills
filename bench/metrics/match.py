"""Greedy assignment of claims to planted defects (recall, precision), and
the symmetric greedy assignment consistency uses (bench/README.md,
"Claims and assignment" and "Consistency").
"""

from __future__ import annotations

from bench.metrics import locate
from bench.metrics.claims import Claim


def _truth_anchor_key(location: dict) -> str:
    """A deterministic, sortable key for one manifest defect location,
    used only to fix the greedy assignment's iteration order (never for
    matching itself, which is `locate.is_hit`)."""
    kind = location["kind"]
    if kind == "paragraph":
        return f"p:{location['paragraph']:012d}"
    if kind == "heading-path":
        return "h:" + "/".join(location["heading_path"])
    if kind == "css":
        return "css:" + location["css"]
    if kind == "element-id":
        return "id:" + location["element_id"]
    if kind == "item-index":
        key = location.get("item_key")
        return f"i:{location.get('item_index', 0):012d}" + (f":{key}" if key else "")
    if kind == "page-path":
        return "page:" + location["page_path"]
    return "?:" + location.get("text", "")


def match_claims_to_defects(
    parsed: locate.ParsedArtifact,
    artifact_type: str,
    claims: list[Claim],
    resolved: list,
    defects: list[dict],
    *,
    ignore_criterion: bool = False,
) -> tuple[set[int], set[int]]:
    """Greedy assignment over every (claim, defect) pair that is a HIT
    under `locate.is_hit`, restricted to matching criterion (exact string
    equality) unless `ignore_criterion` is set. Candidates are sorted by
    `(criterion, truth_anchor_key, claim_anchor_key, finding_id)` and
    taken when both sides are still unclaimed, per bench/README.md.
    Returns `(matched_defect_indices, matched_claim_indices)`, indices
    into `defects` and `claims` respectively.

    `ignore_criterion=True` is the location-level match mode
    (`bench/metrics/score.py`'s `score_artifact_location`): a claim can
    match any defect whose location resolves within the artifact type's
    tolerance, criterion aside. This is what makes a skill and the
    criterion-less `baseline-generic` prompt comparable on a common
    footing (bench/results/README.md, "Baseline comparison"), since the
    default criterion-level match can never credit a baseline finding,
    every one of which carries the fixed criterion `BASELINE-GENERIC`
    that no manifest plants a defect under. The sort key still groups by
    criterion when it is in play; when it is ignored, every candidate
    sorts under the same empty string, so the deterministic tie-break
    falls through to the truth and claim anchor keys.
    """
    candidates: list[tuple[str, str, str, str, int, int]] = []
    for claim_index, (claim, r) in enumerate(zip(claims, resolved)):
        for defect_index, defect in enumerate(defects):
            if not ignore_criterion and defect["criterion"] != claim.criterion:
                continue
            if locate.is_hit(parsed, artifact_type, r, defect["location"]):
                sort_criterion = "" if ignore_criterion else claim.criterion
                candidates.append(
                    (
                        sort_criterion,
                        _truth_anchor_key(defect["location"]),
                        locate.canonical_key(r),
                        claim.finding_id,
                        defect_index,
                        claim_index,
                    )
                )
    candidates.sort(key=lambda t: (t[0], t[1], t[2], t[3]))

    claimed_defects: set[int] = set()
    claimed_claims: set[int] = set()
    for _criterion, _truth_key, _claim_key, _finding_id, defect_index, claim_index in candidates:
        if defect_index in claimed_defects or claim_index in claimed_claims:
            continue
        claimed_defects.add(defect_index)
        claimed_claims.add(claim_index)
    return claimed_defects, claimed_claims


def match_claims_symmetric(
    parsed: locate.ParsedArtifact,
    artifact_type: str,
    claims_a: list[Claim],
    resolved_a: list,
    claims_b: list[Claim],
    resolved_b: list,
) -> int:
    """The maximal matching size `|M|` between two claim sets under the
    same criterion-plus-tolerance predicate recall uses. Candidate pairs
    are sorted by `(criterion, min(key_a, key_b), max(key_a, key_b))`
    before the greedy pass, so `J(A, B) == J(B, A)` by construction
    (bench/README.md, "Consistency": "This is the easiest thing in the
    module to get wrong and the hardest to notice.").
    """
    candidates: list[tuple[str, str, str, int, int]] = []
    for i, (claim_a, ra) in enumerate(zip(claims_a, resolved_a)):
        for j, (claim_b, rb) in enumerate(zip(claims_b, resolved_b)):
            if claim_a.criterion != claim_b.criterion:
                continue
            if not locate.self_match(parsed, artifact_type, ra, rb):
                continue
            key_a, key_b = locate.canonical_key(ra), locate.canonical_key(rb)
            lo, hi = (key_a, key_b) if key_a <= key_b else (key_b, key_a)
            candidates.append((claim_a.criterion, lo, hi, i, j))
    candidates.sort(key=lambda t: (t[0], t[1], t[2]))

    used_a: set[int] = set()
    used_b: set[int] = set()
    matched = 0
    for _criterion, _lo, _hi, i, j in candidates:
        if i in used_a or j in used_b:
            continue
        used_a.add(i)
        used_b.add(j)
        matched += 1
    return matched


def jaccard_tolerant(
    parsed: locate.ParsedArtifact,
    artifact_type: str,
    claims_a: list[Claim],
    claims_b: list[Claim],
    *,
    artifact_path: str | None = None,
) -> float:
    """`J(A, B) = |M| / (|A| + |B| - |M|)`. Two empty claim sets agree
    perfectly (`J = 1.0`): "two runs that both correctly found nothing
    agree perfectly" (bench/README.md, "Consistency")."""
    if not claims_a and not claims_b:
        return 1.0
    resolved_a = [
        locate.resolve_location(parsed, artifact_type, c.location, artifact_path=artifact_path) for c in claims_a
    ]
    resolved_b = [
        locate.resolve_location(parsed, artifact_type, c.location, artifact_path=artifact_path) for c in claims_b
    ]
    matched = match_claims_symmetric(parsed, artifact_type, claims_a, resolved_a, claims_b, resolved_b)
    denom = len(claims_a) + len(claims_b) - matched
    return matched / denom if denom else 1.0


def jaccard_exact(
    parsed: locate.ParsedArtifact,
    artifact_type: str,
    claims_a: list[Claim],
    claims_b: list[Claim],
    *,
    artifact_path: str | None = None,
) -> float:
    """`consistency_exact`: plain Jaccard over `(criterion, canonical
    key)` sets, zero tolerance. Two claim sets that are both vague agree
    with each other, because an unresolvable location canonicalizes to
    its own normalized text (bench/README.md, "Consistency")."""
    if not claims_a and not claims_b:
        return 1.0
    keys_a = {
        (
            c.criterion,
            locate.canonical_key(locate.resolve_location(parsed, artifact_type, c.location, artifact_path=artifact_path)),
        )
        for c in claims_a
    }
    keys_b = {
        (
            c.criterion,
            locate.canonical_key(locate.resolve_location(parsed, artifact_type, c.location, artifact_path=artifact_path)),
        )
        for c in claims_b
    }
    union = keys_a | keys_b
    if not union:
        return 1.0
    return len(keys_a & keys_b) / len(union)

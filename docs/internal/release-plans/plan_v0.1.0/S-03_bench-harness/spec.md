---
id: S-03
title: "Bench harness: generator, corpus, metrics"
type: spec
status: draft
created: 2026-07-31
updated: 2026-07-31
linked-effort: S-03
linked-plan: ../implementation/IMPL-A-foundation.md
linked-strategy-brief: "01-strategy-brief.md (local planning archive, not committed)"
linked-release: ../plan_v0.1.0.md
source-count: 4
ac-count: 8
audience: agent
---

# Spec: Bench harness: generator, corpus, metrics

## Task Summary

- Status: draft
- AC: [ ] AC-1 [ ] AC-2 [ ] AC-3 [ ] AC-4 [ ] AC-5 [ ] AC-6 [ ] AC-7 [ ] AC-8
- Open questions: 2
- Last-updated: 2026-07-31

## Purpose

Give every quality claim ground truth: a deterministic seeded-defect corpus, metric computation, and a baseline runner, so recall, precision, and consistency are computed facts, not assertions [S1][S2].

## Scope

`bench/generator/` (Python), `bench/corpus/` (generated artifacts plus manifests), `bench/metrics/` (recall, precision, Jaccard consistency, baseline comparison), `bench/results/` layout, `bench/README.md` with CC-BY-4.0 notice. Harness core only; per-domain defect libraries are contributed by each skill pipeline (S-05) against the plugin API this spec defines.

## Non-Goals

GitHub-hosted benchmark runs (`bench.yml` mechanics are S-07). Human adjudication tooling for unplanted findings (v0.2). Public benchmark branding [S2].

## Users / Actors

Skill pipelines (contribute domain generators), phase P3 measurement agents (run and compute), CI (verify corpus integrity and envelope validity), skeptical external readers (reproduce results).

## Requirements

The generator MUST be deterministic: identical `(seed, domain, recipe)` inputs produce byte-identical artifacts and manifests, with no wall-clock, locale, or filesystem-order dependence [S1][S2]. Randomness comes only from a seeded PRNG; seeds are recorded in manifests.

The generator MUST expose a domain-plugin API: a domain module registers defect injectors keyed by criterion ID, each able to (a) produce a clean artifact region and (b) inject a specified defect at a recorded location [model-inference: API shape needed for S-05 pipelines to contribute independently].

Each corpus artifact MUST have a manifest recording: artifact path, sha256, seed, domain, and planted defects as `{criterion, location, severity_expected, description}` [S1].

The corpus MUST contain at least 20 artifacts spanning all six launch domains, with at least 3 artifacts per core domain, including at least one clean (zero-defect) artifact per core domain to measure false-positive behavior [S1]. [model-inference: clean-artifact requirement]

Metrics MUST be computed exactly as the methodology defines: recall = fraction of planted defects found (criterion match plus location match within tolerance); precision = fraction of reported findings matching planted defects, with non-matching findings counted against precision in v0.1 (conservative, documented); consistency = mean pairwise Jaccard over `(criterion, location)` sets across k=5 runs [S1]. Location-match tolerance MUST be explicit and documented per domain. [model-inference: tolerance rule required to make recall computable]

The baseline runner MUST execute a fixed generic prompt ("critique this document" family, exact text frozen in the repo) against the same artifacts on the same models, with findings mapped to the contract by a documented, fixed post-processing rule, so skill-vs-baseline comparison is like-for-like [S1].

Results MUST be written as contract-valid envelopes plus a machine-readable `results.json` per run set; human tables are generated from these, never authored [S5].

## Acceptance Criteria

- AC-1: Running the generator twice with the same seeds produces byte-identical `bench/corpus/` trees (verified by hash comparison in CI's corpus job). [S1][S2]
- AC-2: The domain-plugin API is documented in `bench/generator/README.md` with a worked toy-domain example a skill pipeline can copy. [model-inference]
- AC-3: Corpus contains >=20 artifacts, >=3 per core domain, >=1 clean artifact per core domain, every artifact with a schema-valid manifest. [S1]
- AC-4: `bench/metrics/` computes recall, precision, and Jaccard consistency from envelopes plus manifests, with unit tests covering: perfect run, empty run, duplicate findings, location-tolerance edge, clean-artifact false positive. [S1]
- AC-5: The baseline prompt text is frozen in-repo and the baseline runner produces contract-valid envelopes from it. [S1]
- AC-6: `results.json` schema exists; the README results table is generated from it by script with a drift check. [S5]
- AC-7: `bench/README.md` documents corpus design, seeds, metric definitions, reproduction commands, and the CC-BY-4.0 corpus license. [S5]
- AC-8: An adversarial review verifies the generator cannot leak manifest contents into artifact text (the defect description never appears verbatim in the artifact). [model-inference: prevents trivially-findable defects inflating recall]

## Behavior / Examples

Given a clarity-domain artifact seeded with a PLAIN-ACTIVE violation at paragraph 3, when `critique-clarity`'s scripted lane runs, then its envelope contains a finding with `criterion: PLAIN-ACTIVE` whose location resolves to paragraph 3 within tolerance, and the metrics module scores it as a hit.

## Non-Functional Requirements

Python 3.12, stdlib preferred; any third-party dependency ADR-justified [S4]. Full corpus generation under 60 seconds on commodity hardware. Corpus text is original generated content (no copyrighted rubric text), honoring the paraphrase policy [S5].

## Revisions

None (draft).

## Sources & Evidence

- S1: methodology draft sec 8 (metrics, k=5, baseline rule) and sec 5 (manifest-relevant contract fields). Class A.
- S2: strategy doc sec 3.4 mechanism 7 (deterministic generator, Vault Generator precedent). Class A.
- S4: `04-ci-plan.md` (dependency policy, corpus CI job). Class A.
- S5: `00-README.md` D5, D6; `03-documentation-plan.md` (generated tables). Class A.

## Open Questions

- OQ-1: Location-tolerance definitions per domain (exact heading path? paragraph index +-1?). Set during P1 harness design, documented in `bench/README.md`, reviewed at RC.
- OQ-2: Whether precision's conservative treatment of unplanted-but-genuine findings materially understates skill quality. Accepted for v0.1; adjudication tooling is a v0.2 roadmap item.

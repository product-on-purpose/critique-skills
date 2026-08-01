# 0025 - Anthropic Python SDK as a runtime dependency of the bench harness

## TL;DR
- **Decision:** `bench/run_bench.py` depends on the `anthropic` package (`anthropic>=0.40,<1` in `requirements.txt`) to call the judged lane and the frozen baseline condition against the two pinned model tiers. This is the second permitted third-party runtime dependency, alongside `jsonschema` (S-02 critique-contract spec).
- **Why:** The judged lane and the baseline condition each require a real call to the Anthropic Messages API. Writing and maintaining a hand-rolled HTTP client for one vendor's API, against a stdlib-only constraint whose actual purpose is dependency-light audit tooling, is effort spent on a solved problem instead of on the harness itself.
- **Status:** Accepted (2026-07-31).

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, P3 provenance-gap follow-up (Claude)

## Context and problem statement

[S-03 (bench harness) spec](../release-plans/plan_v0.1.0/S-03_bench-harness/spec.md), Non-Functional Requirements: "Python 3.12, stdlib preferred; any third-party dependency ADR-justified." [ADR 0009 (Python and Node toolchain split)](0009-python-node-toolchain-split.md) restates the same rule for the Python half of the repository: "any third-party dependency requiring its own ADR justification," and records `jsonschema` as the one dependency accepted so far, for `contract/validate.py`.

`bench/run_bench.py` is the harness the P3 self-audit found missing ([P3 self-audit report](../execution/P3-report.md), "Provenance gap: no committed harness actually calls a live model or the critic subagent"): the judged lane assembles a prompt from a skill's `SKILL.md` and `references/*.md` and sends it to a pinned model tier, and the frozen baseline condition (`bench/baseline/prompt.txt` plus `bench/baseline/postprocess.py`) does the same with the frozen generic prompt. Both require a real network call to the Anthropic Messages API, authenticated with `ANTHROPIC_API_KEY`. `bench/generator/` and `bench/metrics/` need no model call and stay stdlib-plus-`jsonschema`; the harness is the one part of the bench that necessarily calls a live model, the same distinction `bench/baseline/README.md` already draws for the baseline condition specifically ("the baseline is the one part of the bench that necessarily does [call a model], because it is a comparison against what an unstructured model response looks like").

## Decision drivers

- **The API surface this code needs (authenticated POST, retries, streaming-capable response parsing, typed error objects) is exactly what an official SDK exists to own.** A hand-rolled `urllib` client would have to reimplement authentication headers, retry-on-5xx and rate-limit backoff, and response-shape parsing, all of it already correct and already tested in the official package, for no benefit to the harness's own claims (determinism, contract validity, bounded output) that a stdlib-only implementation would not equally deliver.
- **The dependency is scoped to exactly the two call sites that need it.** `bench/run_bench.py` imports `anthropic` lazily, inside `_client_factory()`, only on a live (non `--dry-run`) invocation. `--dry-run` grid planning, every unit test in `bench/tests/test_run_bench.py`, and every other module in the repository import nothing from it: the package is never on the import path of `contract/validate.py`, `bench/generator/`, or `bench/metrics/`, so it cannot silently widen the dependency surface those modules were built stdlib-plus-`jsonschema` under.
- **Tests never require it to be installed or reachable.** `bench/tests/test_run_bench.py` calls every Anthropic-shaped function (`call_judged_lane`, `call_baseline_lane`, `execute_grid`) through a fake client object implementing the same `client.messages.create(**kwargs) -> response` shape the real SDK exposes; `test_main_dry_run_does_not_import_anthropic` asserts the import never happens on the dry-run path by poisoning `sys.modules["anthropic"]` and confirming `--dry-run` still exits 0. No test in the suite makes a network call or needs the package importable to pass.
- **A hand-rolled client would itself need auditing for the same correctness properties the SDK ships with.** Given the choice between reviewing a small, well-scoped call into a widely used, actively maintained official client versus reviewing and maintaining a bespoke HTTP layer, the former is less audit surface, not more, despite adding a line to `requirements.txt`.
- **The version constraint follows the same convention `jsonschema>=4.20,<5` already set:** a floor recent enough to carry the current Messages API shape (`client.messages.create(model=, max_tokens=, system=, messages=[...])`, confirmed against the SDK's own documentation), and a ceiling one major version wide so a breaking major release does not silently change the harness's behavior underneath it.

## Considered options

1. **Add `anthropic` as a pinned runtime dependency, ADR-justified (chosen).** Matches the precedent `jsonschema` already set: a third-party package is acceptable when the alternative is reimplementing a solved, security- and correctness-sensitive problem inside this repository.
2. **Hand-roll an HTTP client against the Messages API with `urllib.request` from the stdlib.** Rejected. It would still need to reimplement authentication, retry and backoff, and response parsing, all correctness-sensitive and none of it specific to this repository's own claims; the "stdlib preferred" language in S-03's Non-Functional Requirements exists to avoid unnecessary dependencies, not to require reimplementing a vendor SDK by hand.
3. **Defer the harness indefinitely and continue reporting the provenance gap as an open item.** Rejected. This is the exact gap [P3-report.md](../execution/P3-report.md) named as "the single most consequential open item this audit found"; deferring it again does not close it.

## Decision outcome

Option 1. `anthropic>=0.40,<1` is added to `requirements.txt`, alongside `jsonschema>=4.20,<5`, each with a comment naming the module that needs it and the spec or ADR that permits it. `requirements-dev.txt` needs no change: it already inherits `requirements.txt` via `-r requirements.txt`.

## Consequences

**Positive:** `bench/run_bench.py` can make a real, typed, retried call to the Anthropic API instead of a hand-rolled one, closing the provenance gap with production-grade client code rather than a bespoke reimplementation of it. The dependency is lazily imported and never touches the import graph of any module that does not call a live model, so `contract/validate.py`, `bench/generator/`, and `bench/metrics/` remain exactly as dependency-light as [ADR 0009](0009-python-node-toolchain-split.md) described them.

**Negative:** a second third-party package now needs version tracking and, eventually, upgrade attention; a future major-version bump of the SDK (past the `<1` ceiling) requires revisiting this ADR's constraint, not just editing `requirements.txt` in isolation. Anyone running the harness live needs the package installed (`pip install -r requirements.txt`) in addition to `ANTHROPIC_API_KEY`; `--dry-run` and the full test suite need neither.

**Neutral:** this ADR does not change the Node-versus-Python split [ADR 0009](0009-python-node-toolchain-split.md) established; `anthropic` is a Python-side dependency for a Python-side module, the same category `jsonschema` already occupies.

## Implementation sites

- [`requirements.txt`](../../../requirements.txt): `anthropic>=0.40,<1`, with a comment naming this ADR.
- [`bench/run_bench.py`](../../../bench/run_bench.py): `_client_factory()` is the only place the package is imported, lazily, and only on a live run; `call_judged_lane` and `call_baseline_lane` are the only two call sites that use the resulting client.
- [`bench/tests/test_run_bench.py`](../../../bench/tests/test_run_bench.py): every test exercises the same call shape through a fake client, and `test_main_dry_run_does_not_import_anthropic` asserts the dry-run path never imports the real package.
- [ADR 0009 (Python and Node toolchain split)](0009-python-node-toolchain-split.md): the dependency-policy source this ADR satisfies; not edited by this ADR.

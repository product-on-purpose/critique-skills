# 0030 - Replace ANTHROPIC_API_KEY in the bench harness with the mechanism that produced the numbers

## TL;DR
- **Proposal:** stop having `bench/run_bench.py` call the Anthropic Messages API directly. Drive the
  same mechanism that produced the published v0.1.0 numbers instead: Claude Code running the skill
  and the `critique-critic` subagent. Delete `ANTHROPIC_API_KEY` and the `anthropic` dependency once
  the replacement works.
- **Why:** the key is not the problem. The problem is that a paid live run currently answers a
  weaker question than it appears to. The published numbers came from Claude Code workflow
  subagents; `run_bench.py` is a **second, independent implementation** of the same protocol. A live
  run through it validates that implementation. It does not reproduce the numbers, and if the
  figures came out different nobody could say whether that was model variance or the harness
  disagreeing with itself.
- **What that buys:** a live `bench.yml` dispatch would mean "the published figures still hold"
  rather than "a different harness also produces figures." That is the difference between a
  reproduction and a demo, and reproduction is the claim this library trades on.
- **Status:** **Proposed** (2026-08-06). Not accepted. One open question below is load-bearing and
  is not answerable from inside this repository.

- **Status:** Proposed
- **Date:** 2026-08-06
- **Deciders:** Jonathan Prisant (pending)
- **Supersedes in part:** [ADR 0025](0025-anthropic-sdk-runtime-dependency.md), which accepted the
  `anthropic` package as a runtime dependency. That decision was correct for what it solved (closing
  the provenance gap with production-grade client code rather than a hand-rolled HTTP layer). This
  proposal argues the gap it closed was the wrong one.

## Context

Three facts, all independently verifiable in this repository:

1. **The judged lane needs a model.** 54 of the 96 criteria require reading for meaning. The frozen
   baseline condition is definitionally a model call: the whole comparison is "does a rubric-cited
   skill beat a generic prompt." No harness can avoid calling a model.
2. **The published numbers were not produced by `run_bench.py`.** The 502 committed envelopes came
   from a Claude Code multi-agent workflow, one fresh clean-context subagent per run
   ([P3-provenance.md](../execution/P3-provenance.md)). At that time `run_bench.py` was a stub that
   exited 1. It was built afterwards, in P4, to close the provenance gap the P3 self-audit found.
3. **The two mechanisms are not equivalent, and this is already disclosed.**
   [`bench/results/README.md`](../../../bench/results/README.md) states plainly that "a re-run
   through `bench/run_bench.py` should be expected to differ from the figures published here."

Where they differ:

| | v0.1.0 numbers | `run_bench.py` |
|---|---|---|
| Executor | Claude Code subagent under `agents/critique-critic.md` | `client.messages.create()` |
| Skill context | The agent reads `SKILL.md` and `references/` as files | An assembled system-prompt template |
| Scripted lane | The subagent invokes `checks.py` as a tool | The script calls it in-process |
| Protocol | The skill's own protocol, followed by an agent | A reimplementation of that protocol in Python |

`run_bench.py`'s own judged-lane system prompt says it follows "the same clean-context protocol
`agents/critique-critic.md` defines." That sentence is the tell: it is a **copy** of the protocol,
maintained separately from the protocol, and nothing keeps the two in step.

## The problem this creates

The API key is the visible cost. The invisible cost is worse: **the repository now has two
definitions of how a critique runs**, one in `agents/critique-critic.md` plus six `SKILL.md` files,
and one in `bench/run_bench.py`. They can drift, and nothing detects it. A skill protocol change
that nobody mirrors into the harness would silently make the benchmark measure a stale protocol,
and the benchmark is the library's entire evidence base.

Cost is secondary but real: a live grid is 460+ model calls, billed to an API account separate from
any Claude Code subscription.

## Proposal

Replace the direct API call with an invocation of Claude Code itself, running the real skill and the
real subagent. `run_bench.py` keeps its current responsibilities, which are the valuable half and
are not in question:

- planning the grid (artifacts x tiers x k x conditions) and `--dry-run` reporting it;
- staging manifest-free copies so runners cannot see ground truth;
- collecting envelopes, validating them against the contract, and writing them to a fresh branch.

Only the execution step changes: instead of assembling a prompt and calling the API, it asks Claude
Code to run the skill on the staged artifact and returns the envelope.

**What gets deleted when this lands:** `ANTHROPIC_API_KEY` from `bench.yml`, `anthropic>=0.40,<1`
from `requirements.txt`, the `_JUDGED_SYSTEM_TEMPLATE` prompt copy, and ADR 0025's dependency
justification. `jsonschema` remains the only third-party runtime dependency, which restores the
posture [ADR 0009](0009-python-node-toolchain-split.md) set.

**What must not change:** the grid definition, ground-truth isolation, the frozen baseline prompt
and its postprocessor, and the rule that envelopes are immutable evidence. This proposal is about
who executes a run, not what a run is.

## Open questions, in the order they block

1. **Can Claude Code authenticate a non-interactive run in CI under the maintainer's plan?** This is
   the load-bearing one and it cannot be answered from inside this repository. If the only supported
   CI authentication is an API key, this proposal reduces to "same key, better mechanism," which is
   still worth doing for the drift reason above but is a much smaller win. **Answer this before
   estimating anything else.**
2. **Is the baseline condition still comparable?** The frozen baseline is a raw prompt with no
   skill and no subagent. Running it through Claude Code rather than the API changes its execution
   context too. If the baseline moves, the published comparisons are not comparable to new ones, and
   the baseline is supposed to be frozen. This may argue for keeping the baseline on the API path
   even after the skill condition moves, which would mean the key does not fully go away.
3. **Determinism and cost of the k=5 grid.** 460+ Claude Code invocations is a different cost and
   latency profile from 460+ API calls, and the mechanism has to guarantee genuinely fresh context
   per run or the k=5 consistency metric is measuring something else.
4. **What proves the replacement is faithful?** The honest test is a partial re-run of the existing
   grid whose figures land within measured run-to-run variance of the committed ones. That is itself
   a paid run, so the first live dispatch is the acceptance test for this ADR, not a routine check.

## Consequences if accepted

**Positive.** A live `bench.yml` dispatch becomes a reproduction rather than a demo. One definition
of the protocol instead of two. One fewer third-party runtime dependency. The published provenance
caveat in `bench/results/README.md` can be narrowed rather than restated every release.

**Negative.** The harness gains a dependency on a specific agent runtime, where today it depends on
a documented HTTP API. If Claude Code's non-interactive interface changes, the harness breaks in a
way an API version pin would have prevented. Question 2 may mean the key survives for the baseline
condition regardless, which would leave the repository with both mechanisms and none of the
simplification.

## Interim position

Until this is accepted, the position is unchanged and already documented: `--dry-run` needs no
secret and validates wiring, and a live run would validate the harness rather than reproduce the
numbers. Nothing in the repository claims otherwise, and no figure anywhere depends on a run that
has not happened.

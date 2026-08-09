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
- **What it buys, corrected 2026-08-08:** the key goes away entirely, not partially. An earlier
  draft kept the baseline on the API path; that rested on a wrong premise and is corrected under
  "Decisions taken". CI authentication was probed on a clean runner and works with a subscription
  token and no `ANTHROPIC_API_KEY`.
- **Status:** **Accepted** (2026-08-07). Both blockers cleared. `claude setup-token` mints a
  long-lived token from a Claude subscription, so a CI run authenticates without an API key; and the
  acceptance gate ran and passed, producing a contract-valid envelope from the real skill through
  `claude --plugin-dir`. See "Mechanism, established" and "Acceptance gate" below.

- **Status:** Accepted
- **Date:** 2026-08-06, accepted 2026-08-07
- **Deciders:** Jonathan Prisant
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

## Mechanism, established 2026-08-06

Three facts from the installed Claude Code CLI (2.1.224), each verified directly:

- **`claude setup-token`**: "Set up a long-lived authentication token (requires Claude subscription)."
  This is the CI path. The token goes in a repository secret; the subscription authenticates the run;
  no API key and no separate API billing.
- **`claude --print` / `-p`** is the non-interactive mode. `--append-system-prompt` and
  `--output-format` shape the output.
- **`claude --plugin-dir <path>`** loads a plugin from a directory for one session. This is the
  loading hook the harness needs: it can point Claude Code at this repository and have the real
  skill and the real `critique-critic` subagent execute, rather than a reimplementation of them.

**A hard constraint that must be written into the harness.** `--bare` mode sets
`CLAUDE_CODE_SIMPLE=1` and its documentation states that under it "Anthropic auth is strictly
`ANTHROPIC_API_KEY` or `apiKeyHelper` via `--settings` (OAuth and keychain are never read)." So the
harness **must not** run in `--bare` mode, or subscription auth silently stops working and the key
comes back. This is easy to reintroduce accidentally while chasing determinism, since `--bare` is
otherwise attractive for a benchmark: it skips hooks, plugin sync, and CLAUDE.md discovery.

## Decisions taken

**Both conditions move. The API key goes away entirely.**

An earlier draft of this ADR held that the frozen baseline had to stay on the Anthropic API path, on
the grounds that re-measuring it another way would make new baseline numbers incomparable to the
published ones. **That reasoning was wrong, and the error is worth recording because it nearly cost
the whole point of the change.**

The baseline is not a fixed external constant. It is a row in `results.json`, `skill: baseline-generic`,
scored on the same artifacts, the same pinned models, and the same metrics as every skill row. **The
claim this library makes is "a rubric-cited skill beats a generic prompt," and that is a comparison
between two rows of the same run set.** It does not require the baseline to be identical across run
sets; it requires both conditions to be measured the same way *within* one.

What moving both does cost is the ability to compare new absolute figures against the published
ones. That is a real loss and a small one: a re-measurement is its own run set regardless, which is
already how `p3` and `cal1` are handled. Trading cross-run absolute comparability for a harness that
actually runs the shipped skills is the right trade.

## CI authentication: probed 2026-08-08, it works

The question that blocked this ADR was whether Claude Code can authenticate a non-interactive run
on a machine where nobody is logged in. It can.

A temporary workflow installed the CLI on a clean `ubuntu-24.04` runner, with a subscription token
from `claude setup-token` in a repository secret as `CLAUDE_CODE_OAUTH_TOKEN`, and ran one prompt:

```
model said: AUTH_OK
PROBE RESULT: authentication works in CI
```

No `ANTHROPIC_API_KEY` was present. The workflow was deleted after answering; it triggered on push
to its own branch so a temporary file never had to reach `main`.

**Consequences.** Every remaining reason to keep the `anthropic` dependency is now gone. The
public roadmap's "first live `bench.yml` dispatch, on infrastructure the maintainer does not control
end to end" is satisfiable without buying API credit, and satisfiable using the same mechanism that
produced the published numbers, which makes it a reproduction rather than a second implementation
agreeing with itself.

**The token is a real credential and should be treated as one.** It is long-lived, it is tied to a
personal subscription rather than to the repository, and it grants whatever that subscription
grants. Rotating it is `claude setup-token` again followed by re-setting the secret.

## Implemented in two halves; the first is done

**Half one, the transport, landed 2026-08-08.** `_client_factory()` returns a `ClaudeCodeClient`
exposing the same `messages.create(...)` surface the Anthropic SDK did, so both lane call sites and
every SDK-shaped test double are unchanged. `anthropic` is removed from the repository, along with
`requirements-bench.txt`. `bench.yml` installs the CLI and passes `CLAUDE_CODE_OAUTH_TOKEN`.

Verified by a live run rather than by inspection: `critique-clarity` against a corpus artifact on
the pinned haiku tier, with no `ANTHROPIC_API_KEY` in the environment, produced a contract-valid
envelope with 9 findings, 5 scripted and 4 judged, citing real criterion IDs.

**That live run also found a real defect that no unit test or dry-run could have.** The first
attempt failed every skill cell with `[WinError 206] The filename or extension is too long`,
because a judged system prompt assembled from `SKILL.md` plus `references/*.md` exceeds the
platform's command-line argument limit. Baseline cells, which carry no system prompt, succeeded in
the same run. The system prompt now goes to a temp file via `--append-system-prompt-file` and the
user prompt over stdin, so neither can grow into that failure again.

**Half two, fidelity, landed 2026-08-08.** The judged lane no longer assembles a prompt. The
harness stages the artifact, runs the real skill through `claude --plugin-dir`, and keeps the
envelope it emits. `build_judged_system_prompt`, `call_judged_lane`, `_parse_judged_findings`,
`merge_lanes`, `assemble_merged_envelope`, the four response-coercion helpers, and the harness's
own `run_scripted_lane_subprocess` are gone: `bench/run_bench.py` went from 1124 lines to 951, and
what remains contains no second copy of the critique protocol.

The division of responsibility is now explicit, and it is the point of the change. The **skill**
owns `findings` and `summary`, because the skill is what is being measured and it runs both of its
own lanes and applies its own bounded-output rule. The **harness** owns the `run` block, because
the skill is deliberately never told the corpus path, the pinned model id, or the run timestamp.

**This half was not the pure restructuring the previous session predicted, and the reason is worth
recording.** Handing the real skill a real path exposes a leak the old design made impossible.
`bench/corpus/<domain>/<id>.manifest.json` is the complete seeded-defect answer key: criterion,
location, and expected severity for every plant. It sits directly beside `<id>.md`. That was
harmless while the judged lane inlined the artifact's **text** into a prompt, because the model had
no filesystem. It stops being harmless the moment the lane runs the real skill, because
`agents/critique-critic.md` declares `Read` and `Bash` and the protocol tells it to run
`scripts/checks.py` against a path. A skill that can read the answer key it is scored against is
not being measured at all.

`bench/generator/README.md`'s leak rule anticipated the adjacent risk and not this one. Rules 1
through 3 cover the artifact's own text; rule 4 covers the naming of corpus paths, on the stated
grounds that "the artifact path is handed to the skill under test". None of them cover a sibling
answer key, because until this change nothing could read one. So `staged_artifact()` is new work,
not a preserved constraint: it copies the artifact alone into a fresh temp directory, verifies it
against the manifest sha256 on the way through, and the process runs with `cwd` set to that
directory and names the file by its bare filename, so the corpus path never reaches the skill.
Rule 4 is what makes keeping the real filename safe.

**Acceptance status, stated precisely, because the two gates are easy to conflate.**

| Gate | What it proves | Status |
|---|---|---|
| Wiring | The rewritten path runs, and produces a contract-valid envelope | **Attempted 2026-08-09, did not pass.** See below |
| Fidelity (Open question 2) | The replacement measures the same thing: a partial re-run landing within measured run-to-run variance of the committed figures | **Not run,** and blocked behind the wiring gate |

### The wiring gate attempt, 2026-08-09: a blocker the unit tests could not see

A live k=1 run to a fresh `--out-dir` produced **no envelope and no error**. Bisected with bounded
probes, each `claude -p` against the pinned haiku tier:

| Probe | Result |
|---|---|
| Trivial prompt, no plugin | exit 0, immediate |
| Trivial prompt, `--plugin-dir` | exit 0, immediate |
| Read a staged file (tool use, no plugin) | exit 0, immediate |
| Ask the plugin to name its skills | exit 0, all six `critique-*` skills present |
| **Run the real skill on a staged artifact** | **exit 124 at 240s, zero stdout, zero stderr**, with `--permission-mode bypassPermissions` |

So the plugin loads, the skills register, tool use works, and authentication is fine. What does not
finish is a full skill run.

**The skill-listing probe found the reason, and it is worse than a timeout.** The nested run offered
**97 skills**. The six under test were among them; the other ninety-one came from the operator's own
ambient Claude Code configuration, along with whatever plugins, MCP servers and hooks that
configuration carries. `--plugin-dir` adds a plugin, it does not isolate an environment.

That is a measurement defect, not just a performance problem:

1. **The environment is the operator's, so the figures are not reproducible.** A maintainer with 97
   skills and a clean CI runner with 6 are not running the same benchmark, and nothing in the
   envelope records which one produced it.
2. **Other skills can influence the critique.** Several ambient skills describe reviewing or
   authoring documents, and the router sees all of them.
3. **The old design was immune to this by construction.** It sent an assembled system prompt to a
   plain API call, so the environment was exactly what the harness built and nothing else.

**Consequence for this ADR.** The fidelity half is implemented and unit-tested, but it cannot be
accepted until a skill run completes in a *controlled* environment. The remaining work is
environment isolation, not the restructuring itself: the harness has to pin what the nested run
loads rather than inheriting the operator's configuration. Until that exists, a figure produced
this way would be less trustworthy than the one it replaced, which is the opposite of the point.

**This is the third time on this ADR that running the thing found what reading it could not**, after
the `WinError 206` argument limit and the sibling-manifest leak. All three were invisible to a
passing test suite.

Passing the wiring gate does **not** close this ADR. The 2026-08-07 acceptance gate above already
ran one k=1 skill invocation by hand and passed; repeating it through the harness proves the
plumbing, not that the numbers are comparable. Until the fidelity gate runs, the committed figures
in `bench/results/` remain the figures produced by the **old** judged lane, and nothing may claim
otherwise.

**Open question 1 gets worse under this half, not better.** Every judged cell is now a full
plugin-loading agent invocation rather than one API call carrying an assembled prompt. Whatever the
k=5 grid cost before, it costs more now, and that has to be measured before a full re-run is
scheduled rather than discovered partway through one.

Splitting it this way was deliberate: half one removes the API key completely and is small enough
to verify in one live run, and half two changes what is measured and deserves its own scrutiny.

## Open questions

1. **Determinism and cost of the k=5 grid.** 460+ Claude Code invocations is a different cost and
   latency profile from 460+ API calls, and the mechanism must guarantee genuinely fresh context per
   run or the k=5 consistency metric is measuring something else.
2. **What proves the replacement is faithful?** A partial re-run whose figures land within measured
   run-to-run variance of the committed ones. That is itself a paid run, so it is the acceptance
   test for this ADR rather than a routine check.

## Acceptance gate: run 2026-08-07, passed

The gate was a one-skill, one-artifact, k=1 run through `claude --plugin-dir`, required to produce a
contract-valid envelope for the skill condition.

```
claude --plugin-dir <repo> -p "Use the critique-clarity skill to critique <artifact>.
                               Follow the skill's protocol. Output ONLY the final run envelope."
  -> 5,391 bytes of JSON

python -m contract.validate proof.json
  -> valid          (exit 0)
```

The envelope is a genuine run, not a shape that happens to validate:

| Property | Result |
|---|---|
| Findings | 6 |
| Lanes exercised | **both**, `scripted` and `judged` |
| Criteria cited | `PLAIN-PARAGRAPH`, `PLAIN-LISTS`, `PLAIN-AUDIENCE`, `WILLIAMS-COHESION`, `WILLIAMS-CHARACTER-ACTION`, `WILLIAMS-PARALLELISM` |
| `run.artifact_sha256` | present and computed |
| `stripped_context` | populated; the runner recorded that the filename itself named two criteria and treated that as scope steering |

That last row is the strongest signal. The run did not merely execute; it applied the skill's own
clean-context discipline and recorded the steering it noticed, which is behavior that lives in
`SKILL.md` and `critique-critic.md` and is exactly what `run_bench.py`'s reimplementation would have
had to duplicate.

**Two caveats on the proof, both real.**

1. **It used ambient session credentials, not a `setup-token` credential.** The token path is a
   documented command and the same OAuth mechanism, but it has not been exercised in a CI runner. It
   is a one-command check, not an unknown, and it is the remaining thing to confirm before the
   rewrite ships.
2. **The model was not pinned.** The envelope recorded `claude-opus-5`, the session's model, which
   is neither of the two pinned measurement tiers. `claude --model <alias-or-full-name>` exists and
   the harness **must** pass it explicitly; a benchmark that silently inherits whatever model the
   caller happens to be running is measuring nothing reproducible. This is the single most likely
   way to get the rewrite subtly wrong.

**Status: Accepted.** The mechanism is proven. The rewrite is v0.2 work, scoped to the skill
condition only, with the baseline staying on the Anthropic API path per the decision above.

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

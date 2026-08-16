# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **The critic subagent was told to run commands it could not run, and went looking for its own skill instead.** Every path in `agents/critique-critic.md` was relative to the repository root: `python3 skills/<skill>/scripts/checks.py` in "Tools", and `python skills/_shared/merge.py` in protocol pass 5. A subagent starts in whatever working directory its caller was in, which is almost never this plugin, and `SKILL.md`'s "Delegation" section handed it a skill **name** but never a skill **location**. Neither path resolved, and the observed behaviour was not a clean failure: measured 2026-08-16, a delegated run walked outwards from the working directory, escalated to `find /e -maxdepth 3` and `find /c -maxdepth 4`, two whole-drive scans, and never returned. It had come within one directory level of the answer. **The pass 5 path is the sharper miss: `skills/_shared/merge.py` is exactly the location v0.1.5 proved unreachable by four live runs before moving the entry point beside `scripts/checks.py` "because that path resolves".** That release rewrote pass 4 in the six `SKILL.md` files and the critic's protocol and left this pointing at the old path, which is the same lesson it recorded, applied to itself: the instruction a run follows is the one it reads. **The invocation contract now takes a fourth input, `skill_dir`, the absolute path of the skill's own directory**, which the delegating agent already has because Claude Code names it when it loads a skill; every command is built from it, all seven `SKILL.md` files pass it and say it is not optional, and the critic is told in as many words to stop and report rather than search if it was not given one, because searching is not a fallback, it is the failure mode. Verified from a foreign working directory rather than reasoned about: `python <abs>/scripts/checks.py` and `python <abs>/scripts/merge.py` both run correctly, with `merge.py` deriving `skill: critique-clarity` from its own location and the artifact hash from the file. `scripts/tests/test_delegation_contract.py` locks the contract in by asserting the **fenced commands**, not the prose beside them; 16 of its 20 assertions fail against the previous wording.
- **A second, separate instance of the same failure class is recorded but not fixed here.** With the above in place, a sonnet run reached the skill in 3.6 seconds and then ran `find / -maxdepth 6 -iname "<artifact>"`, searching for the artifact this time rather than the plugin, and again did not return. The harness hands the skill a bare filename with the working directory set to the staging directory (`bench/run_bench.py`, `_SKILL_RUN_INSTRUCTION.format(..., artifact=staged_path.name)`), and an unresolved-looking path is evidently enough to trigger a filesystem search, which on Windows is catastrophic. **So no sonnet cell has completed yet, and the fidelity gate is still blocked.** The pattern across both instances is the same and worth naming: when a path is not obviously resolvable, this system searches for it rather than reporting that it cannot find it. Removing the ambiguity beats instructing around it, which is what the next change should do.

- **A measured cost figure this project has been quoting for a week is a timeout, and reading it as a duration hid a defect.** [ADR 0030](docs/internal/decisions/0030-replace-the-api-key-in-the-bench-harness.md)'s cost table records `sonnet | exceeded 9 minutes, killed before finishing`. That is a timeout, not a measurement, and **no sonnet cell has ever completed through the post-ADR-0030 agentic lane**. It has nonetheless been paraphrased as "a sonnet cell exceeds nine minutes" in this changelog's v0.1.4 entry and in session handovers, which turned a failure into a price. Re-measured 2026-08-16: a k=1 probe of `critique-clarity` on sonnet, four cells, ran **60 minutes and wrote 0 of 4 envelopes**, every one hitting the harness's hardcoded 900 second ceiling. **The time is not going into inference.** A cell streamed with no timeout reaches the skill in 3.3 seconds, delegates to the critic subagent at 6.6 seconds, and the subagent then spends the rest of the run hunting the filesystem for the plugin it was asked to run, escalating to `find /e -maxdepth 3` and `find /c -maxdepth 4`, two whole-drive scans it never returned from. It had come within one directory level of the answer. **The cause is a repo-relative path in this repository's own subagent definition**: `agents/critique-critic.md` tells the critic to run `python3 skills/<skill>/scripts/checks.py`, which resolves only from the repository root, while a benchmark cell runs with its working directory set to a manifest-free staging directory by design and the critic is given a skill *name* but never a skill *location*. **This is the same defect class v0.1.5 fixed one layer up**: PR #19 moved the assembler beside `scripts/checks.py` because that path resolves, rewrote pass 4 in the six `SKILL.md` files and the critic's protocol, and left the critic's Tools section carrying the repo-relative invocation, which is the instruction a run actually follows. Two consequences are recorded in ADR 0030's 2026-08-16 amendment: the tier split is a defect rather than a cost difference, so **this harness can currently reproduce only the haiku half of the published grid**; and outside the benchmark entirely, **a user invoking a critique skill from any directory other than the repository root, on a tier that delegates, hits the same wall.** The fix is not in this entry; the finding, its evidence and its blast radius are.
- **[ADR 0031](docs/internal/decisions/0031-fidelity-gate-acceptance-band.md)'s recommended fidelity-gate run cannot be executed and is corrected in place.** It recommended `critique-clarity` on sonnet on the grounds that sonnet's acceptance bands are 2.3x narrower and therefore a stronger test. The bands are measured and unaffected, but the recommendation read the sonnet cost row as a duration, so it traded cost against discriminating power between one option that works and one that has never run. **The fidelity gate can only run on haiku, and can only ever speak for the haiku half of the published grid.** That is a feasibility limit, not a budget choice, and the ADR now says so wherever the gate's result will be published.

- **The one workflow whose only purpose is a live benchmark run could not perform one.** `bench.yml` passed `--skills`, `--k`, `--tiers` and `--dry-run` to `bench/run_bench.py`, and no `--out-dir`. The harness defaults `--out-dir` to `bench/results/runs`, which holds the 462 committed envelopes every published figure is recomputed from, and the immutability guard added in v0.1.4 refuses any directory that already holds envelopes. **A live dispatch therefore exited 1 with `--out-dir bench/results/runs already contains 462 envelope(s)` before reaching its first model call.** Both halves were correct alone: the guard is right to refuse that directory, and the harness is right to default somewhere obvious. Only the combination was wrong. It stayed invisible for two releases because `bench.yml` never runs on push or pull request by design, so CI never executed the path, and because the guard sits after the `--dry-run` early return, so the single dispatch on record (2026-08-05) passed in 19 seconds while the live path was broken. The suite already held the knowledge, in a comment in `bench/tests/test_run_bench.py`: "A fresh `--out-dir`, because the default is the committed evidence directory and the immutability guard would (correctly) refuse it." Nothing checked the workflow against it. **The workflow now names its own directory**, `bench/results/runs-dispatch-<run id>`, keyed on the run id so two dispatches cannot collide and kept under `bench/results/` because the publish step stages exactly that path, with an `out_dir` input for a caller who wants to name it. `bench/tests/test_bench_workflow.py` asserts the contract against the harness rather than against a string: it checks that the harness default would still be refused today, and fails if it ever stops being, so the reasoning cannot rot into a test that passes for the wrong reason. This is a prerequisite for ADR 0030's fidelity gate and for the `ROADMAP.md` commitment to a live dispatch "on infrastructure the maintainer does not control end to end", neither of which could have run.
- **An intermittent test failure that had survived three sessions turned out to be this repository's own tooling racing every other process on the machine.** `scripts/skill-selftest.py`'s `check_pytest` ran the skill's test suite by passing pytest an **absolute path** while itself running from the repository root. For a real skill both are inside the repository and nothing goes wrong. For the fixture skill this file's own tests write into a temp directory, the two sit on different drives, so pytest cannot build a collection tree from its rootdir to the argument, walks up from the argument instead, and creates a directory collector for **the temp root itself**. Listing that directory races every process on the system. Captured on 2026-08-15, the nested run died with `ERROR collecting test session` and `FileNotFoundError: [WinError 2] The system cannot find the file specified`, **naming a temp directory belonging to an unrelated project** that had been deleted between the listing and the stat. That is why the failure was intermittent, why it correlated with machine load, why it moved between two different tests, and why it had never once appeared in CI, where a Linux runner's `/tmp` is quiet. The invocation now passes a path relative to a working directory inside the skill, with `PYTHONPATH` carrying the repository root so a real skill's tests keep importing `skills._shared` and `contract` as running from the root had been providing implicitly. **Measured under deliberate temp-directory churn: the old invocation failed 10 runs out of 10, the new one 0 out of 10, and 25 consecutive runs of the two affected tests passed against a baseline failure rate of roughly 1 in 5.** The nested run also stopped being slow, from about 13 seconds to under one, because walking the temp root was most of what it was doing, and the full Python suite went from 56 to 141 seconds down to 17.
- **The reason that cause took three sessions to find is now fixed too.** `check_pytest` reported a failure as the last 20 lines of stdout, and fell back to stderr only when stdout was empty, so any failure with output at all discarded stderr and never recorded the exit code. It reported the collection error faithfully enough to be seen and nowhere near well enough to be diagnosed. A failure now carries the exit code, both streams, and an explicit note when it elided anything, because silent truncation is what hid this.

### Added

- **The published figures now carry a measured spread, and ADR 0030's fidelity gate has a threshold it can be failed against.** That gate accepts the rewritten judged lane on "a partial re-run whose figures land within measured run-to-run variance of the committed ones." **No such variance figure existed.** `bench/results/results.json` pools every k=5 repetition and every artifact of a domain into one cell figure, so each published number is a ratio of sums carrying no recorded spread: a `critique-clarity` sonnet row reads `recall_location: 89/100`, and those 100 planted defects are 4 artifacts times 5 repetitions collapsed into one ratio, with the five runs behind it recorded nowhere as five things. **The gate could not be failed**, and a re-run returning almost anything could have been argued into it after the fact. New `python -m bench.variance` computes the missing number from the 500 committed envelopes with **no new model runs**, publishing [`bench/results/variance.json`](bench/results/variance.json) against a new `variance.schema.json`. It regroups envelopes on the repetition index in their filenames (`haiku-r3.json`; no contract field records it, which is the `run_set` and lane schema debt `ROADMAP.md` already lists), pools within a single repetition through the same `bench.metrics.score` calls `build_results` uses, and bands the pooled statistic by resampling **whole repetitions** with replacement, because the published figure is a ratio of sums rather than a mean of ratios and only whole-repetition resampling preserves that structure. **It refuses to emit a band unless pooling every repetition back together reproduces the committed numerator and denominator exactly, and refuses equally when no cell matched a committed entry at all, because silence is not verification. Measured: 104 of 104 cell-metrics reproduce exactly.** [ADR 0031](docs/internal/decisions/0031-fidelity-gate-acceptance-band.md) records the method, the gate specification, and what the band does not cover.
- **Three results from that measurement, all of which change how a re-run should be planned.** **The bands are wide**: median width 0.082 across the location-level skill cells, widest 0.247, with single-run spread median 0.135 and maximum 0.412. `critique-accessibility` 0.1.0 on sonnet publishes a location recall of 0.306 from five runs that measured 0.529, 0.294, 0.353, 0.118 and 0.235; the pooled figure is an honest summary and any one run alone would have told a different story. **The cheap tier is the weak test**: haiku's bands are 2.3x wider than sonnet's (median 0.145 against 0.063) while a haiku cell costs 3m35s to 6m01s against sonnet's nine minutes and up, so choosing haiku to save hours buys a gate roughly twice as easy to pass. **Gate power varies 8x across cells**, from 0.031 on `critique-usability`/sonnet precision to 0.247 on `critique-accessibility` 0.1.0/sonnet recall, which makes the choice of which cell to re-run a decision about how hard the gate is rather than a scheduling detail. Recorded so it is taken knowingly.
- **Stated plainly rather than left implied: the consistency floor has no error bar.** `score_consistency` compares pairs of envelopes and is undefined for a single repetition, so it cannot be decomposed the way recall and precision can. The published **0.309** floor, which [ADR 0022](docs/internal/decisions/0022-consistency-floor-overall-lane-min-core.md) sets as a release gate and `ROADMAP.md` lists under known limitations, carries no uncertainty estimate, and neither does any other consistency figure. A band for it needs a different construction and is v0.2.0 measurement debt.
- **`variance.json` does not repeat `results.json`'s run-set mistake.** Every entry carries its own `run_set`, where `results.json` records one identifier on a file holding two concatenated run sets. `python -m bench.variance` also takes `--runs` more than once and emits a single file covering both, so the hand concatenation that `bench/results/README.md`'s reproduction recipe currently instructs is not needed here. The `runs/steering/` probe exclusion is likewise the tool's default rather than a recipe step someone has to remember, which is what that README itself recommends.

## [0.1.5] - 2026-08-09

A reliability release for the last step of a critique. No criterion was added, removed, or re-scored, and no run envelope was touched.

### Added

- **The critic now has the envelope assembler the library always had but never exposed to it.** `skills/_shared/envelope.py` has carried the deterministic assembly logic from the start, and `assemble_envelope`'s own docstring names its intended callers as "skills/_shared/runner.py, or a judged-lane critic merging both lanes". The scripted lane could reach it, because `runner.py` is a CLI. The critic could not: it is prose plus `Read` and `Bash`, and this was a Python function with no entry point, so `SKILL.md` pass 4 told it to rank, bound, histogram and gate by hand from a description of the algorithm. It did not do that reliably. Measured on the pinned haiku tier, 2 of 7 benchmark cells produced a contract-valid envelope, failing on a histogram that did not total `len(findings)` plus `suppressed_count`, on a `scripted` finding claiming less than `high` confidence (which the contract pins, because a deterministic check either fired or it did not), and on an empty `stripped_context` array where the field should simply be absent. **Every skill now carries `scripts/merge.py`, beside its `scripts/checks.py`.** Findings in, one validated envelope out, or nothing at all rather than something invalid. It ranks, bounds, assigns ids after ranking, histograms everything found rather than only what survived bounding, counts the suppressed, computes the gate, and normalises prose to the contract's rules. Everything derivable is derived rather than asked for, because each is a field a critic could otherwise transcribe wrongly: the artifact hash from the file, `run.rubrics` from the namespaces actually cited, the skill version from `SKILL.md`, the relative artifact label (the contract rejects an absolute path), and the skill name, which the script reads from its own location. **It sits beside `checks.py` for a reason that had to be learned the hard way.** Placed in `skills/_shared/` and referenced by path, it was unreachable in a real session: four live runs from an ordinary working directory with the plugin loaded elsewhere failed three different ways, and each time the run fell back to hand assembly and emitted a prose report instead of an envelope, which is worse than the arithmetic errors this replaced, because a readable summary that is not an envelope looks like success to everything downstream while being unusable by it. `scripts/checks.py` has resolved correctly in every shipped release, so the assembler is invoked exactly the same way from exactly the same place. **Measured after: 3 of 4 benchmark cells valid with zero malformed-envelope failures**, against 2 of 7 with three malformed before, and a valid envelope from a userland directory with the plugin loaded from elsewhere. Small samples, so this is evidence the mechanism works rather than a reliability figure, and benchmark cells run roughly twice as slow.

### Changed

- **The benchmark harness now has a stated rule for which repairs it may make to a skill's output, and it is not the one v0.1.4 shipped by accident.** ADR 0030 deleted the harness's reimplementation of the critique protocol, correctly. It also deleted `_sanitize_prose()`, which was sitting next to that logic but is not part of it. The line, decided now and recorded in ADR 0030: **a repair the harness may make is one that cannot change what was found.** Stripping a code fence, extracting an envelope from a narrated run, normalising house-style punctuation and truncating to the schema maximum are all transport, and none of them can alter which criterion was cited, at what severity, or where. Merging lanes, ranking, bounding output, building the histogram and deciding the gate are the measurement itself, and the harness must not touch them.
- **Prose normalisation is restored for the skill lane, because leaving it out made the benchmark unfair.** `bench/baseline/postprocess.py` has always applied it to the baseline, stating the reason itself: the model "was never told this rule, so this function enforces it on its behalf rather than letting a stray dash turn a whole envelope contract-invalid". With it deleted for the skill only, one stray em dash in one `violation` field cost an entire skill cell on 2026-08-09 while the baseline's identical slip would have been repaired in silence. That biases "skill beats generic prompt" against the skill. The frozen baseline could not move to meet the skill, so the skill moved to meet it, and both lanes are now normalised identically. **A malformed `summary` is still a failed cell**, because recomputing that would put the harness back in the business of measuring.

### Added

- **A non-final response is retried rather than scored.** A cell can return a promise instead of a result: measured on 2026-08-09, one returned "The critique-critic agent is running in the background to evaluate clarity-001.md. I'll output the final run envelope when it completes." In a one-shot `claude -p` there is no "when it completes", so that is the skill's delegation pattern meeting non-interactive mode, not the tier failing the critique. An API call cannot fail this way at all. `SKILL_RUN_ATTEMPTS` is 3, deliberately small: each retry costs a full agentic run, and retrying further would hide a systematic failure behind cost instead of reporting it.
- **A scripted-only envelope is rejected as an incomplete run.** It is structurally indistinguishable from a merged one, so a run that never reached the judged lane would otherwise be written and scored as though it had. The harness now requires at least one judged-lane finding whenever the skill's own `SKILL.md` frontmatter declares judged criteria, and names the lanes it did find when it refuses. The check keys off what the skill declares, so a scripted-only skill is never punished for behaving exactly as specified.

## [0.1.4] - 2026-08-09

The release where the API key leaves the project entirely, and where the benchmark stops carrying a second copy of the thing it measures. No skill behavior changed, no criterion was added, removed, or re-scored, and no run envelope was touched.

### Changed

- **The benchmark harness reaches the model through the Claude Code CLI, and the `anthropic` SDK is gone from this repository entirely.** `bench/run_bench.py` used to call the Anthropic Messages API directly, which meant the one command that reproduces the published figures needed an `ANTHROPIC_API_KEY` that nothing else here has ever needed, and a reasonable reader concluded the library wanted a key from them. `_client_factory()` now returns a client exposing the same `messages.create(...)` surface the SDK did, so both lane call sites and every SDK-shaped test double are unchanged, and it authenticates from a Claude subscription rather than a key. `anthropic` and the `requirements-bench.txt` that carried it are deleted, leaving `requirements.txt` at `jsonschema` alone, and `bench.yml` installs the CLI and passes a `CLAUDE_CODE_OAUTH_TOKEN` minted by `claude setup-token`. **There is now no `ANTHROPIC_API_KEY` anywhere in this repository, for a user or for a maintainer.** [ADR 0030](docs/internal/decisions/0030-replace-the-api-key-in-the-bench-harness.md) records the decision and supersedes [ADR 0025](docs/internal/decisions/0025-anthropic-sdk-dependency.md); CI authentication was probed separately on a clean `ubuntu-24.04` runner before the change shipped. Verified by a live run rather than by inspection: `critique-clarity` against a corpus artifact on the pinned haiku tier, with no key in the environment, produced a contract-valid envelope with 9 findings, 5 scripted and 4 judged, citing real criterion IDs.
- **That live run found a defect no unit test or dry-run could have.** The first attempt failed every skill cell with `[WinError 206] The filename or extension is too long`, because a judged system prompt assembled from `SKILL.md` plus `references/*.md` exceeds the platform's command-line argument limit; baseline cells, which carry no system prompt, succeeded in the same run. The system prompt now goes to a temp file via `--append-system-prompt-file` and the user prompt over stdin, so neither can grow into that failure again.

- **The benchmark's judged lane runs the real skill instead of a reimplementation of it.** `bench/run_bench.py` used to assemble its own judged-lane system prompt from a skill's `SKILL.md` and `references/*.md`, parse findings back out of the response, and then merge and bound the two lanes itself. That was a second definition of the critique protocol living alongside the real one in `agents/critique-critic.md` and the six `SKILL.md` files, with nothing keeping the two in step, and deleting it is the whole point of [ADR 0030](docs/internal/decisions/0030-replace-the-api-key-in-the-bench-harness.md). The harness now stages the artifact, runs the skill through `claude --plugin-dir`, and keeps the envelope the skill emits. The split is explicit: the skill owns `findings` and `summary`, because the skill is what is being measured and it runs both of its own lanes; the harness owns the `run` block, because the skill is never told the corpus path, the pinned model id, or the run timestamp. `build_judged_system_prompt`, `call_judged_lane`, `_parse_judged_findings`, `merge_lanes`, `assemble_merged_envelope`, the four response-coercion helpers and the harness's own `run_scripted_lane_subprocess` are all deleted; the module went from 1124 lines to 951. **The committed figures in `bench/results/` are still the old lane's figures.** Nothing here claims otherwise, and the fidelity gate ADR 0030 sets, a partial re-run landing within measured run-to-run variance, has not been run.

### Fixed

- **A benchmark run inherited the operator's own Claude Code configuration, which would have made it unreproducible.** `--plugin-dir` adds a plugin; it does not isolate an environment. A nested run offered **97 skills**, the six under test plus ninety-one from whatever the operator happened to have installed, along with that configuration's plugins, MCP servers and hooks. Two operators would not have been running the same benchmark, and nothing in the envelope recorded which one produced it. The old design was immune by construction, because it sent an assembled prompt to a plain API call and the environment was exactly what the harness built. It also did not merely skew results: a full skill run never finished at all, and was killed at 240 seconds with no output and no error. Adding `--setting-sources ""` and `--strict-mcp-config` takes the same probe to **18 skills**, all of them the CLI's own built-ins plus the plugin under test, and the run then completes in about two minutes. Both flags apply to the baseline lane too, because the committed baseline envelopes came from a plain API call with no environment at all, so isolating it moves the baseline closer to how it was measured rather than further away.
- **Tool access is an explicit allowlist, not a permissions bypass.** `--permission-mode bypassPermissions` would hand write access to the repository being measured, and would contradict what `SECURITY.md` says about the critic having no `Write` and no `Edit`. `Read,Bash,Glob,Grep,Task,Skill` was measured to be sufficient: the same artifact produced 9 findings across both lanes under it.
- **A real skill run narrates, so the envelope had to be extracted rather than parsed.** The measured response was 7403 bytes that opened "Now I'll perform the judged criterion sweep", walked four protocol passes, and only then emitted the envelope, fenced, at the end. Requiring the whole response to be JSON discarded a complete, contract-valid run. The harness now takes the last balanced JSON object carrying `run`, `findings` and `summary`; last rather than first, because a run echoes its own scripted-lane output on the way past and the first object is that intermediate.

**The wiring gate passed** on the pinned haiku tier: `python -m contract.validate` reports `valid` on an envelope carrying 7 findings across both lanes, citing seven real `PLAIN-*` criteria, with `run.artifact` correctly rewritten to the corpus path rather than the staging path and `run.model` the explicitly-passed pinned id. Staging, invocation, envelope extraction, provenance and validation all work.

Three things were measured on the way, all recorded in [ADR 0030](docs/internal/decisions/0030-replace-the-api-key-in-the-bench-harness.md).

**Cost.** A haiku cell takes 94 to 173 seconds and a sonnet cell exceeds nine minutes, against one API call per cell before, so a full k=5 grid is now a many-hour job that has to be budgeted rather than discovered partway through.

**Cell reliability, which blocks a graded re-run.** Only 1 of 4 haiku cells produced a usable envelope, with three distinct failure modes: invalid histogram arithmetic; an em dash in a `violation` field, against the contract's prose rule; and, most seriously, **no envelope at all**, the run returning "the critique-critic agent is running in the background, I'll output the final run envelope when it completes". That last one is a property of driving an agent rather than calling an API: the process returned a promise instead of a result, and nothing currently tells that apart from a skill that found nothing.

**An asymmetry this change created.** The deleted `_sanitize_prose()` stripped em and en dashes from judged findings, because the model was never told the house style, and `bench/baseline/postprocess.py` still does exactly that for the baseline lane. So the baseline's prose is normalised and passes while the skill's identical slip fails the whole cell, which biases "skill beats generic prompt" against the skill. Whatever gets decided about envelope validity, both conditions have to be treated the same way. The old lane could not surface any of this, because it built `summary` itself and every envelope was valid by construction whatever the model returned.

### Added

- **Ground-truth isolation: the artifact is staged away from its answer key before the skill sees it.** `bench/corpus/<domain>/<id>.manifest.json` records every seeded defect with its criterion, location and expected severity, and it sits directly beside `<id>.md`. That was harmless while the judged lane inlined the artifact's text into a prompt, because the model had no filesystem. Running the real skill changes it completely: `agents/critique-critic.md` declares `Read` and `Bash`, and the protocol tells it to run `scripts/checks.py` against a real path, so the answer key would have been one `Read` away and every score built on it worthless. `bench/generator/README.md`'s leak rule already covered the artifact's own text and the naming of corpus paths, on the stated grounds that "the artifact path is handed to the skill under test", but not a sibling answer key, because until now nothing could read one. `staged_artifact()` copies the artifact alone into a fresh temp directory, checks it against the manifest sha256 on the way through, and the skill runs with its working directory set there and is given only the bare filename, so the corpus path never reaches it. The real filename is safe to keep because leak rule 4 already guarantees corpus ids carry no criterion ID or defect count.
- **The two transport constraints ADR 0030 calls the easiest to break are now tested rather than commented.** A run must never pass `--bare`, whose auth is "strictly `ANTHROPIC_API_KEY` or `apiKeyHelper`", so it would silently reintroduce the key this ADR exists to delete; and it must always pass `--model`, because a benchmark inheriting the caller's model measures nothing reproducible. Both were prose in a comment block and are now assertions.
- **The harness refuses an `--out-dir` that already contains envelopes.** `bench/results/runs*/` is immutable measurement evidence: every published figure is recomputed from it. A unit test asserting the old `ANTHROPIC_API_KEY` precondition fell through to the live path with default arguments once that precondition changed, and `--out-dir` defaulted to `bench/results/runs/`, overwriting nine committed baseline envelopes before it was stopped. They were restored from git and verified byte-identical, but nothing in the harness had prevented it, and **the destructive default was the real defect; the broken test only pulled the trigger.** Three guards landed together: the harness refuses to write into a directory that already holds envelopes and says why, `bench/tests/test_run_bench.py` gained a `_forbid()` helper that tests patch over `_client_factory` and `_check_claude_cli` so any test reaching a transport fails loudly instead of running one, and both guards have tests of their own.

### Fixed

- **`SECURITY.md` described a network and credential model this repository no longer has.** Its "one network call" section still said the harness calls the Anthropic Messages API via the `anthropic` SDK and "requires `ANTHROPIC_API_KEY` in the environment", and its supply-chain section still listed `anthropic` as one of two permitted Python runtime dependencies. None of that survived deleting the SDK, and this is a world-readable security policy on a public repository citing an ADR that is now superseded. Rewritten against the CLI transport, with the Python runtime dependency count corrected to one and the reference repointed to ADR 0030. Its "supported versions" section separately still claimed `v0.1.0` was the only shipped version, three releases later; it now states the pre-1.0 support policy in a form that does not go stale at each release.
- **`AGENTS.md` told a future agent session that a live bench run "requires `ANTHROPIC_API_KEY` in the environment".** That is the file agents read as project instructions, so the document most likely to reintroduce the key was the one still asking for it. It now describes the CLI path and records the two rules a live run must follow: pass `--model` explicitly, because a benchmark that inherits the caller's model measures nothing reproducible, and point `--out-dir` at a fresh directory.
- **`docs/how-to/gate-in-ci.md` pointed readers at `requirements-bench.txt`**, a file that no longer exists.

## [0.1.3] - 2026-08-07

A dependency-hygiene release. No skill behavior changed, no criterion was added, removed, or re-scored, and no run envelope was touched.

### Fixed

- **`pip install -r requirements.txt` was installing an Anthropic API client into every environment that installed this plugin.** `requirements.txt` carried `jsonschema`, which every skill genuinely needs, alongside `anthropic`, which only `bench/run_bench.py` needs. Since that is the obvious command, and since the file is what a self-healing agent reaches for after the scripted lane reports a missing dependency, the practical effect was that installing a plugin which never calls a model pulled in an API client, and a reasonable reader concluded the library wanted an API key from them. It does not, and never did: **skills are instructions read by the agent you are already using, and never place a call of their own.** `requirements.txt` is now `jsonschema` alone; `anthropic` moved to a new `requirements-bench.txt`, needed only by someone re-running the benchmark live. `requirements-dev.txt` inherits the runtime file and so no longer pulls the SDK either, and `bench.yml` is the only CI job that changed, because it was the only one that needed it. Verified on a machine with `jsonschema` and no `anthropic` package: all six skills produce contract-valid envelopes, and `run_bench.py --dry-run` plans the full grid without a key.

### Added

- **`docs/explanation/the-benchmark-harness.md`**, which answers "do I need an API key?" in its first line (no) and then explains `bench/run_bench.py` for anyone who wants to know. It states the distinction nothing in this repository had stated plainly: a skill never calls a model, so there is nothing for it to authenticate with, whereas the benchmark is a standalone Python script that must go and fetch a judgment and cannot borrow your agent's login. The key is a property of having written the measurement as a standalone program, not a property of the measurement. The page also records what the harness does step by step and which two of its seven steps touch a model at all, why it exists (the published numbers came from a live multi-agent workflow and nothing committed could have reproduced them), its honest status (never run live, not once), the four ways to run it including two that need no key, and why the frozen baseline condition stays on the API path regardless.
- **The joint-routing eval is scored on both pinned tiers.** Haiku returns 18/18 at k=3, matching sonnet, with contested 9/9, ambiguous 6/6, control 3/3 on each. The non-unanimous cases differ by tier and both sit on boundaries the fixture already labels ambiguous, which is the correct behavior rather than a failure. Recorded because a routing result from one model is not a claim about the other.

### Changed

- **`docs/how-to/gate-in-ci.md`** described installing `jsonschema` directly as a way to skip the `anthropic` dependency. That workaround is no longer necessary and the page says so.
- **ADR 0025** named `pip install -r requirements.txt` as the way to install the harness dependency, which is no longer true. Corrected with a dated note rather than a rewrite, since it is an accepted record.

## [0.1.2] - 2026-08-07

Everything here comes from asking the runtime a question instead of reasoning about it. No skill behavior changed, no criterion was added, removed, or re-scored, and no run envelope was touched. The measured numbers in `bench/results/` are the v0.1.0 numbers.

### Fixed

- **`agents/README.md` was registering as a live subagent.** Claude Code discovers subagents by scanning `agents/` for `*.md` and loads every one it finds. Loading this repository as a plugin and asking what it had returned `critique-skills:critique-critic, critique-skills:README`: a second subagent, with no name and no description, silently, with no warning or error. A probe plugin pinned down the rule, registering three subagents from a directory holding `real-agent.md`, `README.md`, `_README.md` and `README.txt`; the underscore prefix does not protect a file and only the non-`.md` extension is skipped. The cause was upstream, in the family Standard's `G8` check, which **required** a folder README there, so following the rule produced the defect. Fixed in `agent-skills-toolkit` v1.10.0 and adopted here by bumping `TOOLKIT_REF`; the file is deleted. Its content is not lost: the design rationale it carried moves into `docs/explanation/architecture-detail.md`, along with the rule this taught, which is that `agents/` holds subagent definitions and nothing else.
- **Three of the six skill descriptions could not be told apart on the cases most likely to arrive.** `critique-accessibility` and `critique-usability` both accept HTML and markdown UI artifacts, and neither disclaimed the other, so "check the colour contrast on this landing page" routed to usability. Both now name the other. Found by measurement, not review: the case had been written into the eval fixture as an unambiguous control.

### Added

- **A `smoke` CI job that answers the question no other job asked: does this plugin run for someone who just installed it?** Every other job installs dependencies before it runs anything, so none of them sees what `/plugin install` delivers, which is a git clone and nothing else. That gap shipped the v0.1.1 install crash while 784 tests passed and the conformance gate was clean. `scripts/smoke.py` runs every skill's scripted lane on a real committed artifact and asserts the outcome for the environment: with no dependencies each skill must fail naming the exact install command and printing no traceback, and with them each must emit a usable envelope. Both are asserted, in that order, on one runner, because asserting only the second would have missed the original defect. Confirmed able to fail: against the pre-fix code it fails 6 of 6.
- **The joint-routing eval is scored, not just written.** `scripts/run-joint-routing.py` drives `claude --plugin-dir` so all six descriptions sit in context exactly as they do for a user, then puts one query at a time to a pinned model. Result on sonnet at k=3: **18/18**, with contested 9/9, ambiguous 6/6, control 3/3. Routing turned out to be stochastic, so the runner takes `--k`, scores the modal answer, and reports unanimity per case; a k=1 run is an anecdote, which is the same conclusion `bench/` reached with k=5. Two cases remain non-unanimous, both `critique-microcopy` against `critique-usability`, and both are fixture cases labelled ambiguous, where a split is the correct behavior rather than a failure.
- **ADR 0030 (replace the API key in the bench harness), Accepted.** `claude setup-token` mints a long-lived token from a Claude subscription, so a CI benchmark run can authenticate without an API key, and the acceptance gate ran: a one-skill run through `claude --plugin-dir` produced a contract-valid envelope with findings across both lanes citing real criterion IDs. Recorded with the constraint that `--bare` mode reads only `ANTHROPIC_API_KEY` and never OAuth, and the decision that the frozen baseline condition stays on the API path, because moving it would break comparability with every published figure. The key narrows to one condition rather than disappearing.

### Changed

- **`TOOLKIT_REF` bumped twice**, to `9439699` and then to `cafe6b6`, adopting `agent-skills-toolkit` PRs #189 and #193. Above-tier gate findings went 5 to 0 across those adoptions plus the new architecture pair, and `tier-report` now reports `Convergent (no blockers detected)`, meaning nothing blocks Advanced (Gold). The declared tier stays Convergent; declaring Gold is a commitment to keep meeting it, not a score to claim once.

## [0.1.1] - 2026-08-05

The first release after publication, and the first shaped by evidence from outside this repository.
`critique-skills` went public and was listed in the `product-on-purpose` marketplace on 2026-08-04;
two external validators were then run against the shipped v0.1.0, the first time this library had
been checked by anything it did not write itself. Everything below traces to that, or to closing an
item the RC handover carried.

No skill behavior changed. No criterion was added, removed, or re-scored. No run envelope was
touched. The measured numbers in `bench/results/` are the v0.1.0 numbers, unchanged.

### Fixed

- **A fresh install crashed before reading an artifact.** `contract/validate.py` did a bare
  module-level `import jsonschema`, and every skill's `scripts/checks.py` reaches it through
  `skills/_shared/runner.py` and `gate.py`. Claude Code's `/plugin install` clones a repository and
  does not run `pip`, so on any machine without the package a freshly installed plugin answered
  step 2 of every skill's protocol with a raw `ImportError` traceback and no indication of the
  remedy, which existed only in `QUICKSTART.md`, a file no invoking agent reads. The import is now
  lazy behind `_jsonschema()`, raising `MissingDependencyError` whose message carries the exact
  install command; both CLI boundaries catch it and print that message with no traceback, using the
  exit-code convention every other environment error here already uses (4 under `--gate`, 1
  otherwise). The prerequisite is now stated in each of the six `SKILL.md` protocol blocks and in
  `agents/critique-critic.md`. Found by an external plugin validator, not by 784 passing tests or a
  clean conformance gate: the repository's own tooling structurally cannot see the fresh-install
  path.
- **`agents/critique-critic.md` hardcoded `python`, which does not resolve on stock Linux or
  macOS.** Now `python3`, with a note that neither name is portable alone. The six `SKILL.md` files
  were already interpreter-agnostic; the hardcoding was only in the one subagent every skill
  delegates to.
- **Every recorded example-artifact hash was wrong on any Windows checkout.** `.gitattributes`
  protected only `bench/corpus/**`, so the 25 artifacts hashed into
  `expected_envelope.run.artifact_sha256` were left to git's end-of-line normalization. Measured
  before the fix: 22 of 22 matched the LF form stored in git and 0 matched the bytes on disk. The
  repository was right and every Windows checkout was wrong, and nothing read the hashes, so nothing
  complained. Fixed with `skills/**/examples/** -text` and, more importantly,
  `scripts/tests/test_example_artifact_hashes.py`, which recomputes every recorded hash and reports
  a line-ending mismatch as that specific defect with its remedy. The RC handover had carried this
  as hypothetical.
- **The six skills were not distinguishable at trigger time.** Nothing in the pipeline tested
  cross-skill discrimination: each skill's `evals/triggers.eval.json` is validated in isolation and
  the description scorer is per-skill and mechanical, so neither instrument had a term for "is this
  distinguishable from its five siblings". Three collisions are closed in the descriptions
  themselves, which is where they must be, because a `SKILL.md` body is not read until after a skill
  has already been selected: `critique-argument` and `critique-clarity` both claimed proposals and
  memos; `critique-microcopy` and `critique-usability` both claimed error states; and
  `critique-accessibility` and `critique-docs` both used the literal phrase "heading structure" while
  meaning different things by it.
- **Install-path and security-channel documentation that publication made false.** `README.md`,
  `QUICKSTART.md`, `RELEASE-NOTES.md`, and `SECURITY.md` each stated the repository was private and
  that no install path resolved. GitHub Private Vulnerability Reporting was also enabled, since
  `SECURITY.md` names it the preferred channel and links to a form that 404s with the setting off.

### Added

- **`docs/explanation/architecture.md` and `docs/explanation/architecture-detail.md`**, the
  architecture pair. The overview is the shape: the five parts, how one critique runs end to end,
  and the three things the design structurally refuses to do. The detail page is the reasoning: what
  decides the scripted/judged line, why the contract is frozen, why clean context is a structural
  guarantee, the four measurement choices that carry the weight, why the gate points at another
  repository, and what would count as an architecture change rather than a bug fix.
- **`evals/joint-routing.eval.json`**, 18 queries scored with all six descriptions in view, in three
  kinds: `contested` (a defensible winner plus the sibling it contests), `ambiguous` (no correct
  single winner, where asking is the right behavior), and `control`. Four of the ambiguous cases are
  taken verbatim from the skills' own fixtures, where each is currently asserted as an unambiguous
  positive for a different skill. It is deliberately **not scored in CI**: routing is a model
  decision over descriptions in context, and a lexical proxy would measure string overlap rather
  than routing, which is exactly the kind of number this library exists not to publish.
  `scripts/tests/test_joint_routing_eval.py` enforces what can be checked deterministically.
- **`docs/internal/execution/P3-cal1-provenance.md`**, closing an item `bench/results/README.md`,
  `P3-cal1-report.md`, and ADR 0028 all carried as open. It is explicit that it does not reach
  `P3-provenance.md`'s standard, because it was written four days later by a session that was not
  present for the runs. It corrects the round-number timestamp count from six to nine and records
  two anomalies not previously noted: ten envelopes timestamped a day before the calibration date
  the manifest records, and one envelope recording the staging path rather than the corpus path.
  What it cannot establish is listed under "Not established" rather than inferred.

### Changed

- **`TOOLKIT_REF` bumped `6cfd68b` to `9439699`** in `ci.yml` and `release.yml`, adopting
  `agent-skills-toolkit` PR #189. That PR fixed two defects in the grader that were producing four
  of this repository's five above-tier findings: `SKIP_DIRS` covered the Node ecosystem's scratch
  directories and not Python's, so the folder-README check walked into `__pycache__`; and
  `gen-index`'s two boilerplate sections were hardcoded to the toolkit's own repository layout and
  emitted seven links to paths that do not exist here. Verified before bumping: the patched
  toolkit's raw `INDEX.md` output is byte-identical to the committed one.
- **Above-tier gate findings 5 to 0.** `tier-report` now reports `Convergent (no blockers
  detected)`, meaning nothing blocks Advanced (Gold). The declared tier is unchanged at Convergent
  (Silver); declaring Gold is a separate decision with its own ongoing commitments.

## [0.1.0] - 2026-08-03

### Added
- Repo scaffold: `library.json`, generated `.claude-plugin/plugin.json`, the conformance gate
  wrapper (`scripts/check.mjs`), the manifest generator (`scripts/gen-plugin-manifest.mjs`),
  `LICENSE` (Apache-2.0), `AGENTS.md`, `README.md`, `RELEASE-NOTES.md`, and the Diataxis docs tree.
- Critique Contract: `contract/critique-contract.schema.json` (JSON Schema draft 2020-12) defining
  the finding object, the run envelope, and the disposition log; a Python validator and CLI
  (`contract/validate.py`, `contract/validate_envelopes.py`) with `--gate` exit-code semantics;
  `docs/reference/severity-scale.md` (the shared 0-4 scale with per-domain anchors) and
  `docs/reference/criterion-ids.md` (the `<SOURCE>-<CRITERION>` ID grammar); the promoted
  constitution at `docs/explanation/methodology.md`.
- Bench harness: a deterministic seeded-defect generator (`bench/generator/`) with a domain-plugin
  API, a 23-artifact corpus across six domains with at least one clean artifact per core domain
  (`bench/corpus/`), metrics for recall, precision, and k=5 Jaccard consistency (`bench/metrics/`),
  a frozen baseline prompt and postprocessor (`bench/baseline/`), and generated, drift-checked
  results tables (`bench/report.py`).
- Skill template pattern: the canonical skill directory shape and self-test runner
  (`docs/internal/skill-template.md`, `scripts/skill-selftest.py`), plus the shared lane library at
  `skills/_shared/`.
- Six critique skills, all shipped active: `critique-clarity` (US Federal Plain Language
  Guidelines, Williams), `critique-accessibility` (WCAG 2.2 AA), `critique-usability` (Nielsen's 10
  heuristics, narrow artifact claim: HTML/markdown UI specs, not live applications),
  `critique-docs` (Diataxis), `critique-microcopy` (NN/g error-message guidelines), and
  `critique-argument` (Toulmin model). Every criterion carries a permanent ID traceable to its
  source; no stretch skill was held back.
- `critique-critic` subagent (`agents/critique-critic.md`): delegated, clean-context critique that
  refuses authorial framing beyond the artifact itself, runs the named skill's scripted and judged
  lanes, and returns exactly one contract-valid envelope with `tools: [Read, Bash]` (no `Write`, no
  `Edit`: this subagent reports, it never changes the artifact).
- CI pipeline: `.github/workflows/ci.yml` (seven jobs: conformance, unit-python, unit-node, schema,
  corpus, drift, audit), `bench.yml` (`workflow_dispatch`-only, secret-gated, dry-run capable),
  `release.yml` (tag-triggered, version-guarded); `scripts/check-release-versions.mjs` and
  `scripts/lib/version-manifest.mjs` (the single version-bearing-file enumeration);
  `scripts/extract-release-notes.mjs` (the RELEASE-NOTES section extractor for the GitHub release
  body).
- v0.1.0 measurement: 462 envelopes (run set `p3-2026-07-31`, all six skills plus the frozen
  baseline, two pinned model tiers `claude-haiku-4-5-20251001` and `claude-sonnet-5`, k=5) plus 40
  calibration envelopes (run set `cal1-2026-08-01`, `critique-accessibility` 0.1.1 only); at
  location level, `critique-accessibility` (0.1.1) and `critique-clarity` beat the frozen baseline on
  recall at equal-or-better precision on both pinned tiers, `critique-usability` does so on the Haiku
  tier only (its Sonnet cell is a narrow, non-qualifying recall win at a small precision cost); all
  three stretch skills shipped on a recorded baseline win plus the R1 consistency floor (0.309), with
  `critique-docs` shipping on precision dominance at equal recall rather than a recall win. See
  `bench/results/README.md` and `bench/results/verdicts.md`.
- Documentation: `README.md`, `QUICKSTART.md`, the Diataxis `docs/` tree (reference, how-to,
  explanation, tutorials), generated results and skill-catalog tables, `INDEX.md`.
- Examples library: `examples/README.md` indexes nine self-contained pages by task rather than by
  file, six one-skill walkthroughs (`examples/accessibility/`, `argument/`, `clarity/`, `docs/`,
  `microcopy/`, `usability/`, each an artifact plus its `envelope.json` and a human's
  `dispositions.json`) and three cross-cutting recipes (`recipes/gate-in-ci.md`,
  `recipes/revision-loop.md`, `recipes/critic-delegation.md`), explaining once which findings are
  bit-for-bit reproducible (`lane: scripted`) and which are curated from this library's own
  validated golden fixtures (`lane: judged`). Cross-linked from `README.md`'s Examples section and
  `QUICKSTART.md`'s closing pointer.
- Skill-template conformance now runs in CI: `scripts/tests/test_skills_conformance.py` globs
  `skills/critique-*/` and runs `scripts/skill-selftest.py` against each of the six shipped skills
  as a parametrized pytest case, collected automatically by the existing `unit-python` job with no
  workflow edit. Closes S-04's AC-3 ("a template-conformance script validates all six skills
  uniformly in CI"); the spec now records all seven ACs fulfilled. Full suite: 784 tests passing
  (777 prior plus 7 new: one guard test plus six parametrized skill cases).
- Mermaid diagrams, each followed by a plain-text restatement of the same flow: the benchmark
  pipeline, seed and generator version through the corpus, skill and baseline runs, metrics, to
  published tables (`bench/README.md`, "The pipeline, at a glance"); how a scripted-lane finding
  and a judged-lane finding merge into one run envelope (`docs/reference/critique-contract.md`,
  "The two lanes, merged into one envelope"); and the critique, disposition, revise, re-critique
  loop with its three-iteration bound (`examples/recipes/revision-loop.md`).
- `CONTRIBUTING.md`: the Two-Part Gate as the entry test for a new skill, the seven-item review
  order from `docs/explanation/methodology.md` Section 12, the copyright paraphrase policy, and how
  to run the conformance gate and the generated-file regeneration step locally.
- `SECURITY.md`: an inventory of what the repository ships and what it executes, naming the bench
  harness's live-model call as the one network call anything here makes (opt-in, `workflow_dispatch`
  only, never on `push` or `pull_request`), the supply-chain posture (pinned GitHub Actions, zero
  third-party npm runtime dependencies, CI `npm audit` on every push and pull request), and the
  GitHub Private Vulnerability Reporting channel for reports.
- 29 ADRs under `docs/internal/decisions/` recording every material build-run decision, from the
  `critique-` prefix and full-slate scope through the measurement basis, the consistency floor, and
  the accessibility calibration.

### Changed
- `README.md` restructured to the family's badge-and-table-of-contents style: status and
  conformance-tier badges, a collapsible table of contents, a "What this is" comparison table,
  Mermaid flowcharts for "How a critique runs" and the Two-Part Gate, a generated release-history
  table, and a widened "The family" section that now also lists `writing-style-catalog`. The
  conformance-tier claim was updated to match the tree: `node scripts/check.mjs` reports tier
  Convergent, with 0 errors and 0 warnings at the declared tier, replacing the prior wording that
  the plugin "targets Universal tier... with `critique-critic` already at Convergent."
- Location-level rescoring added to `bench/results/` (results schema version 1.1.0): recall and
  precision now also compute on location match alone, criterion ID ignored, alongside the original
  criterion-level cut, because the criterion-level baseline comparison is pinned at zero by
  construction and cannot discriminate skill quality. See ADR 0026 (location-level re-examination of
  the baseline gates) in `docs/internal/decisions/`.
- `critique-accessibility` 0.1.1: findings now name the element they are about with its `id` (or a
  bounded CSS selector when it has none) instead of a bare line number, in both the scripted lane
  (`scripts/checks.py`) and the judged lane (`SKILL.md`, "Naming a location"). No criterion was
  added, removed, or weakened. This was the one pre-committed calibration iteration for a core skill
  that had lost its baseline comparison; location recall moved from 0.176/0.306 (haiku/sonnet) to
  0.988/0.965, beating the baseline on both tiers and both metrics, with the 0.1.0 failure published
  alongside the fix. See ADR 0027 (accessibility location-emission calibration) and ADR 0028
  (post-calibration verdict) in `docs/internal/decisions/`.
- `docs/explanation/methodology.md`: corrected two references to an unverified "40-candidate,
  13-domain survey" (Section 2's gate table and Section 13's open questions) to state plainly that
  the domain slate is a provisional working proposal and that a critique-framework survey is a
  tracked v0.2 deliverable, not a document that already exists. See ADR 0029 (methodology survey
  claim: correction, not a scope change) in `docs/internal/decisions/`.

### Fixed
- `release.yml`'s RELEASE-NOTES extraction moved from an inline shell/`awk` verdict computation
  (which the family CI rule forbids) to `scripts/extract-release-notes.mjs`, mirroring how the
  tag-version guard was already delegated to a script.
- `contract/validate_envelopes.py`'s envelope discovery now walks every `bench/results/runs*`
  directory instead of the single hardcoded `bench/results/runs/`, so the calibration run set under
  `bench/results/runs-cal1/` is no longer silently skipped.
- `bench/report.py`'s per-`(domain, model)` comparison cell now keys on `(skill, skill_version)`
  instead of skill name alone, so publishing a recalibrated skill version no longer silently drops
  the prior version's row from the generated comparison table.

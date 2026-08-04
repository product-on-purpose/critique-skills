# Security Policy

## What this repository ships

1. **Skills** (`skills/critique-<domain>/`) - a `SKILL.md` instruction file, a Python
   `scripts/checks.py` scripted lane, rubric `references/`, `evals/`, and `examples/`. `SKILL.md` is
   instructions an agent reads and follows when a skill is invoked; `scripts/checks.py` is real code
   that runs locally against whatever artifact path you pass it.
2. **Subagent** (`agents/critique-critic.md`) - the clean-context critic every `critique-<domain>`
   skill delegates to. Its declared tools are `Read` and `Bash` only; it has no `Write` or `Edit`, so
   it cannot modify the artifact it critiques or anything else on disk (see that file's "Tools"
   section).
3. **Contract** (`contract/`) - the JSON Schema (`critique-contract.schema.json`) and its Python
   validator and CLI (`validate.py`, `validate_envelopes.py`).
4. **Bench harness** (`bench/`) - a deterministic seeded-defect corpus generator, scoring metrics,
   and a harness (`run_bench.py`) that runs skills and a frozen baseline against pinned models. This
   is the one part of the repository that makes a network call, and only when run directly and
   explicitly; see below.
5. **Repo tooling** (`scripts/`) - Node generators and validators that run in this repository's own
   CI (see `AGENTS.md`, "Checks").
6. **Docs** (`docs/`, `README.md`, and similar).

## What runs, and where

Checking out this repository does not execute anything on its own. A skill's scripted lane and the
contract validator are local, stdlib-plus-one-dependency Python: each reads the artifact file (or
inline content) and the skill's own reference files, and writes only its own findings or validation
output to stdout. Neither imports `subprocess`, network modules, or `eval`/`exec`; `skills/` and
`contract/` contain none of those calls, verified directly against this checkout before writing this
page.

The `critique-critic` subagent runs with `Read` and `Bash` only, and its `Bash` use is exactly two
things: invoking a skill's own `scripts/checks.py` against the supplied artifact, and validating the
resulting envelope with `contract/validate.py`. No `Write`, no `Edit`: it reports, it never changes
the artifact or anything else.

## The one network call: the bench harness

`bench/run_bench.py` calls the Anthropic Messages API, via the `anthropic` SDK, to run a skill's
judged lane and the frozen baseline comparison against pinned model tiers
([ADR 0025](docs/internal/decisions/0025-anthropic-sdk-dependency.md)). This is opt-in and explicit:

- It requires `ANTHROPIC_API_KEY` in the environment. Without it, only `--dry-run` grid planning
  works, and that path makes no network call at all.
- `anthropic` is imported lazily, only on the live-run code path; `contract/validate.py`,
  `bench/generator/`, and `bench/metrics/` never import it (ADR 0025, "Implementation sites").
- `bench.yml`, the one GitHub Actions workflow that can run this harness live, is
  `workflow_dispatch` only. It never runs on `push` or `pull_request` (`AGENTS.md`, "Bench").

Nothing else in this repository makes a network call.

## Supply chain

- **`npm audit --audit-level=high`** runs in CI (the `audit` job, `.github/workflows/ci.yml`) on
  every push and pull request against `main`, on both Node versions in the matrix (`22.12.0`,
  `24`). A high-or-critical advisory in a dependency fails the build.
- **No third-party npm runtime dependencies exist today.** `package-lock.json`'s only package entry
  is this repository itself. The audit job still runs on every change, so a PR that introduces one
  gets it reviewed rather than waved through.
- **Every GitHub Action is pinned to a full commit SHA**, not a floating tag, in both `ci.yml` and
  `release.yml` (`actions/checkout@<sha> # v7.0.1`, `actions/setup-node@<sha> # v7.0.0`, and
  similarly for `actions/setup-python` and `softprops/action-gh-release`). `agent-skills-toolkit`,
  the toolkit this repository's conformance gate wraps rather than vendors
  ([ADR 0011](docs/internal/decisions/0011-gate-wiring-toolkit-wrapper.md)), is checked out at a
  pinned commit (`TOOLKIT_REF`), bumped deliberately rather than tracked against a moving branch.
- **Third-party runtime dependencies require their own ADR**
  ([ADR 0009](docs/internal/decisions/0009-python-node-toolchain-split.md): "any third-party
  dependency requiring its own ADR justification"). Python currently carries two:
  `jsonschema` (`contract/validate.py`'s schema validation) and `anthropic` (the bench harness's
  live-model calls, ADR 0025 above). Node carries zero. Adding one, in either language, needs a
  decision doc under `docs/internal/decisions/` before it lands.
- **Releases are tag-triggered and version-guarded.** Pushing a tag matching `v*` runs
  `release.yml`, which re-runs the full CI suite, then fails the build if the tag does not equal
  every version-bearing manifest listed in `scripts/lib/version-manifest.mjs`
  (`scripts/check-release-versions.mjs`), before extracting that version's section of
  `RELEASE-NOTES.md` for the GitHub Release body (`scripts/extract-release-notes.mjs`).

## Supported versions

Pre-1.0: only the version at the tip of `main` is supported. There is no version-support matrix yet
because there is only one shipped version, `v0.1.0`.

## Reporting a vulnerability

> [!IMPORTANT]
> **Pre-release: both links below 404 today.** This repository is currently private, so the security
> advisories link and the issues link that follow will not resolve for anyone outside this project
> until it is public. If you already have direct access to this private repository, use its own
> Security tab or Issues tab instead of the links below.

Report privately first.

Preferred channel: GitHub Private Vulnerability Reporting.

- <https://github.com/product-on-purpose/critique-skills/security/advisories/new>

Fallback channel: open a GitHub issue requesting a private follow-up. Do not include exploit details
or secrets in the issue itself.

- <https://github.com/product-on-purpose/critique-skills/issues/new>

What to include, where you can:

1. Affected file(s) or workflow(s)
2. Reproduction steps
3. Impact assessment
4. Suggested remediation, if you have one

Response targets: initial acknowledgement within 2 business days, ongoing status updates until
resolution.

## Scope

This policy covers:

1. Repository content (`skills/`, `agents/`, `contract/`, `docs/`)
2. The bench harness (`bench/`) and its opt-in network call
3. Build and release tooling, and GitHub Actions workflows
4. Published release artifacts (GitHub Releases created by `release.yml`)

## Out of scope

1. Vulnerabilities in third-party tools or clients not maintained here, including the agent runtime
   or editor a user invokes these skills from.
2. Security behavior of external AI platforms or agents that choose to run these skills.

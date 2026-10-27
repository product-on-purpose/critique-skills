# Frozen corpus copies

This directory holds byte-identical copies of corpus artifacts and manifests. The generator no
longer produces them in their original form. They are kept so that already-committed run envelopes
can still be scored.

## Why this exists

On 2026-10-27, `critique-accessibility` added five new WCAG 2.2 AA criteria
([E67 (accessibility expansion)](../../../docs/internal/backlog/enhancements.md)). A pre-work check
found two problems in the shared builder, `bench/generator/domains/accessibility.py`. The builder
built an email input and a phone input with no `autocomplete` attribute. It also built a status card
with no `role="status"`. The new WCAG-1.3.5 criterion covers autocomplete. The new WCAG-4.1.3
criterion covers status messages. Once those criteria existed, every artifact from that shared
builder would trip them, including the one artifact meant to be clean. An adversarial review after
the first fix found a third problem of the same WCAG-4.1.3 shape: the builder's promo-code error span
sits beside `aria-invalid="true"` with no live region either. The fix adds the missing attributes to
the builder itself, four in total: both `autocomplete` tokens, the status card's `role="status"`, and
the promo-code error span's `aria-live="polite"`. That fix changes the rendered bytes of
`accessibility-001.html` through `accessibility-004.html`, and therefore changes their
`artifact_sha256`.

Scoring joins a run envelope to its manifest by `artifact_sha256`. See `bench/metrics/__main__.py`,
`build_results`. `bench/variance.py` skips an envelope whose sha matches no manifest, rather than
raising an error. Every envelope already committed against the old bytes carries the old sha.
Changing the live artifacts' bytes would silently orphan each of those envelopes the next time
anyone scores them or re-derives variance. There would be no error, just quietly fewer matched
cells. Freezing the pre-change bytes, under a path the generator never touches again, keeps the old
sha discoverable and keeps those envelopes scorable.

## What is frozen, and why only this

`v1/accessibility/accessibility-001.html` through `accessibility-004.html` are byte-identical to
what was committed before the 2026-10-27 fix. So are their four `.manifest.json` files. Each frozen
manifest is identical to the original manifest except one field: `artifact`, which is repointed to
the frozen path. The `artifact_sha256` field is unchanged, because the bytes it describes are
unchanged.

No other domain is frozen here. Only accessibility's shared builder changed in a way that altered
already-shipped artifact bytes.

`bench/results/measurement-manifest.json`, the staging record for the p3-2026-07-31 run set, is left
unchanged on purpose: it is a historical record of what was staged and hashed at the time, not a live
pointer. Its `originalPath` entries for `accessibility-001.html` through `accessibility-004.html`
name `bench/corpus/accessibility/...`, the live path those bytes held when that record was written;
the same bytes are now kept here, under `v1/accessibility/`.

## Which committed run sets this binds

Three directories under `bench/results/` hold committed envelopes whose `run.artifact_sha256`
matches these frozen bytes. Each holds `critique-accessibility` envelopes, `baseline-generic`
envelopes scored against the accessibility domain, or both:

- `bench/results/runs/` (run set `p3-2026-07-31`): 80 envelopes, 40 `critique-accessibility` and 40
  `baseline-generic`.
- `bench/results/runs-cal1/` (run set `cal1-2026-08-01`): 40 envelopes, all `critique-accessibility`.
- `bench/results/runs-dispatch-38673834829/` (run set `bench-2026-10-15`): 40 envelopes, 20
  `critique-accessibility` and 20 `baseline-generic`, sonnet model only. This run set is committed
  evidence. It is not yet part of the pooled `bench/results/results.json` or
  `bench/results/variance.json`. It still binds to these frozen files by sha, because its envelopes
  were scored against the same pre-fix bytes.

`bench/results/runs-dispatch-37091134037/` (run set `bench-2026-10-03`) does not bind here. It holds
`critique-forms` and `baseline-generic`-on-forms envelopes, not accessibility.

## Why no flag or exclusion is needed to keep scoring working

`bench/metrics/__main__.py`'s `_discover_manifests` and `bench/variance.py`'s `_group_scores` both
call `corpus_dir.rglob("*.manifest.json")`. That call finds every manifest under `bench/corpus/`
recursively, this directory included. A frozen manifest's `artifact_sha256` matches an old envelope
the same way a live manifest's matches a new one. Neither module needs to know this directory
exists.

`bench/run_bench.py`'s `discover_skill_artifacts` decides what a live dispatch run sends to a model.
It globs `corpus_dir/<domain>` non-recursively. A frozen artifact, one directory level deeper than
that glob reaches, never matches it. Nothing here is ever dispatched to a model as live corpus
content.

## The rule

Files under `_frozen/` are never edited, never regenerated, and never extended with new artifacts.
A frozen artifact's one job is to keep its own bytes forever. A future change that needs its own
frozen baseline gets its own `v2/` (or later) directory, not a rewrite of `v1/`.

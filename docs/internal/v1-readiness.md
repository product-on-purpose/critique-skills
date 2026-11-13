# v1.0 readiness tracker

`ROADMAP.md`'s v1.0.0 section names four conditions that must all hold before v1.0 is declared.
This file holds one row per condition, so that the declaration can read the current state here
instead of re-deriving all four from scratch. It was created for
[E43 (v1.0 readiness tracker)](backlog/enhancements.md) on 2026-11-12.

This tracker records evidence. It does not decide whether a condition is met when the wording
leaves room for judgment; those calls stay with the maintainer, and each such row says so.

## Conditions

| # | Condition, as `ROADMAP.md` states it | State on 2026-11-12 | Evidence | What closes it |
|---|---|---|---|---|
| 1 | Every shipped skill has survived a public benchmark cycle and a disposition-telemetry pruning pass. | Not met. The benchmark half is done; the pruning half has not started. | All seven skills were measured in run set `bench-2026-10-28`, and their figures are published in `bench/results/results.json`. No disposition data exists anywhere, so no pruning pass can run. | [E48 (disposition telemetry)](backlog/enhancements.md), then one pruning pass per skill. |
| 2 | The survey-derived candidate slate is fully triaged: every candidate is shipped, deferred, or rejected with a recorded reason. | Not met. | The survey that defines the slate has not been run. `docs/internal/research/` does not exist. | [E44 (taxonomy survey and slate triage)](backlog/enhancements.md). |
| 3 | Convergent (Silver) conformance is stable across two consecutive minor releases. | Possibly met; the maintainer's reading is needed. | `library.json` declared `tier: convergent` at v0.1.0, and `v0.2.0` shipped at the same tier. `node scripts/check.mjs` graded `main` Convergent with no errors on 2026-11-12. The open question is whether v0.1 to v0.2 counts as the two consecutive minors, or whether the count starts after some later point. | A maintainer ruling on which two releases count, then a gate run at each of those tags. |
| 4 | At least one external consumer, a repository or workflow not owned by this project, gates in CI on a critique-skills finding contract. | Not met. | No external consumer is known. The cross-library composition item in v0.3.0 does not count, because this project owns both sides. | [E56 (external-consumer path)](backlog/enhancements.md), which records its outcome in this row. |

## How to update this file

Update a row when the item named in its last column closes, and change the date in the State column
header. A row moves to "Met" only with evidence a reader can check: a run set name, a tag, or a
repository URL.

---
title: Dispositions
description: Recording accept, reject, or defer per finding and what the disposition log is for
audience: both
level: intermediate
---

# Dispositions

A disposition is the human accountable for an artifact deciding, per finding, whether it stands:
`accept`, `reject`, or `defer`. Recording one produces a disposition log, JSON conforming to
`#/$defs/dispositionLog` in `critique-contract.schema.json`. This page shows the shape of that log,
how to author and validate one, and why the library requires it rather than treating disposition as
optional.

## Why the log exists

Critique never auto-applies fixes; this is a contract, not a default setting (see
[Methodology, section 10](../explanation/methodology.md#10-human-in-the-loop-by-contract)). The
disposition step exists for two reasons beyond keeping judgment with the person accountable for the
artifact.

**Pruning telemetry.** Acceptance rate per criterion, computed across disposition logs, is the
library's signal for which criteria are worth keeping. A criterion that consistently produces
rejected findings is either badly operationalized or not worth checking, and gets revised or
retired (see [Methodology, section 8](../explanation/methodology.md#8-evaluation)). Without logged
dispositions there is no signal, and a bad criterion runs forever on the strength of the skill's own
say-so.

**Auditability.** The revision loop this library supports, critique, disposition, revise,
re-critique, is bounded: it stops when zero findings remain at severity 3 or above, or after three
iterations, whichever comes first. A disposition log keyed to finding and criterion IDs is what
makes that loop reconstructable afterward, who decided what, and why, rather than a revision history
that only shows the artifact changed.

## The shape of a disposition log

| Field | Required | Shape | Notes |
|---|---|---|---|
| `contract_version` | yes | semver | Version of the contract the log was written against. |
| `envelope` | yes | object | Identifies the run being dispositioned; see below. |
| `dispositions` | yes | array, at least 1 entry | One entry per finding decided. |

`envelope` is the composite key `skill` plus `artifact_sha256` plus `timestamp`, required, plus
optional `skill_version`, `artifact`, `path`, and `envelope_sha256`. It exists because a finding ID
like `F-007` is unique only within its own envelope, not across the library, so a log without this
reference cannot say which run it is about.

Each entry in `dispositions`:

| Field | Required | Shape | Notes |
|---|---|---|---|
| `finding_id` | yes | `F-` plus digits | Must resolve in the referenced envelope. |
| `disposition` | yes | `accept`, `reject`, or `defer` | The decision. |
| `note` | no | prose, to 1000 chars | Why. Most valuable on reject. |
| `criterion` | no | criterion ID | Denormalized from the finding, so acceptance rate per criterion is computable from the log alone. When present it must match. |
| `decided_at` | no | RFC 3339 UTC timestamp | When the decision was recorded. |

A log need not cover every finding in its envelope; an undecided finding is simply absent.

## Recording a disposition

1. Read the run envelope's `findings[]` array and pick the finding IDs you are deciding on.
2. Author (or extend) a disposition log JSON file, referencing that envelope by `skill`,
   `artifact_sha256`, and `timestamp`.
3. Add one entry per finding decided, `accept`, `reject`, or `defer`, with a `note` on anything you
   reject.
4. Validate it.

Using the canonical worked example from
[Critique contract](../reference/critique-contract.md#envelope-walkthrough) (finding `F-007`,
criterion `WCAG-1.4.3`, from a `critique-clarity` run against `docs/prd.md`):

```json
{
  "contract_version": "1.0.0",
  "envelope": {
    "skill": "critique-clarity",
    "skill_version": "1.2.0",
    "artifact": "docs/prd.md",
    "artifact_sha256": "3f9a1c0000000000000000000000000000000000000000000000000000000000",
    "timestamp": "2026-07-17T14:22:03Z"
  },
  "dispositions": [
    {
      "finding_id": "F-007",
      "disposition": "accept",
      "note": "Confirmed against the rendered page.",
      "criterion": "WCAG-1.4.3",
      "decided_at": "2026-07-17T15:05:00Z"
    }
  ]
}
```

```
$ python -m contract.validate disposition-log.json
valid
$ echo $?
0
```

This exact document was validated against this repository's schema before writing this page.

## What the validator does and does not check

Running `python -m contract.validate <file>` on a disposition log checks the schema shape (required
fields, the `accept`/`reject`/`defer` enum, `F-` finding ID grammar), house style (no em dash, no en
dash anywhere, keys included), and that timestamps name real calendar instants. All of that is
checkable from the log alone.

**Resolving `finding_id` against the referenced envelope needs both documents**, and the CLI takes
only one file, so this check does not run through `python -m contract.validate` by itself. It runs
when you call the validator library directly, with the envelope loaded:

```python
from contract.validate import load_document, validate_document

log = load_document("disposition-log.json")
envelope = load_document("prd-envelope.json")
result = validate_document(log, referenced_envelope=envelope)
```

Given a `finding_id` that does not exist in the envelope, this reports it as an error rather than
letting a typo pass silently:

```
dispositions[0].finding_id: finding id 'F-999' does not exist in the referenced envelope
```

Both checks were run against this repository's validator before writing this page.

**Whether the decision itself is right is outside every check here.** Nothing in the schema or the
validator can tell you whether a rejected finding should really have been rejected; that judgment is
what the disposition step is for. See
[Critique contract, "Where enforcement stops"](../reference/critique-contract.md#where-enforcement-stops)
for the full boundary between what the machine checks and what the reviewer decides.

## See also

- [Critique contract](../reference/critique-contract.md), the full disposition log field reference.
- [Methodology](../explanation/methodology.md), sections 8 and 10, for the evaluation and
  human-in-the-loop design this log serves.
- [Gate in CI](gate-in-ci.md), for gating a build before a human ever reaches disposition.

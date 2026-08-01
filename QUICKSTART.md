# QUICKSTART

One path, no branches: install, run one critique against a file already in this repo, read what
comes back, record one decision on it. Five minutes, inside a single Claude Code session. No
separate API key: critique runs as a skill in the session you already have open.

## 1. Install

In Claude Code:

```
/plugin marketplace add product-on-purpose/agent-plugins
/plugin install critique-skills@product-on-purpose
```

## 2. Run one critique

The bundled example is
[`skills/critique-clarity/examples/clarity-golden-01-passive-and-nominalization.md`](skills/critique-clarity/examples/clarity-golden-01-passive-and-nominalization.md):
two short paragraphs, two passive-voice sentences and one nominalization planted on purpose so
`critique-clarity` has something concrete to find. It ships in the repo specifically to be the
first thing you critique.

Ask, in plain language:

> Critique `skills/critique-clarity/examples/clarity-golden-01-passive-and-nominalization.md` for
> clarity.

`critique-clarity`'s own description names "review," "feedback," "clarity," and "prose document,"
so a request like this triggers it without naming the skill directly. If nothing triggers, ask
explicitly: "Use critique-clarity on that file."

## 3. Read the envelope

What comes back is one contract-valid run envelope, not a paragraph of prose. It has exactly three
parts:

- **`run`** - which skill ran, which version, which model, the artifact's own `artifact_sha256`,
  and when.
- **`findings`** - one structured record per defect: a criterion ID, a `lane` (`scripted` or
  `judged`), a `severity` from 0 to 4, a `location` you can navigate to unaided, `evidence` quoted
  or measured from the artifact, the `violation`, a `fix`, and a `confidence`.
- **`summary`** - counts by severity, how many findings were suppressed below the output bound,
  and a `gate` verdict (`pass` or `fail`).

On this example, expect four findings, all severity 2, `gate: pass` (nothing reaches severity 3),
along the lines of:

| id | criterion | severity | location |
|---|---|---|---|
| F-001 | `PLAIN-ACTIVE` | 2 | Current Status, paragraph 1 |
| F-002 | `PLAIN-ACTIVE` | 2 | Current Status, paragraph 1 |
| F-003 | `PLAIN-NOMINALIZATION` | 2 | Current Status, paragraph 2 |
| F-004 | `PLAIN-TRANSITIONS` | 2 | Current Status, paragraph 2 |

One finding in full, so you can see every field at once:

```json
{
  "id": "F-001",
  "criterion": "PLAIN-ACTIVE",
  "lane": "scripted",
  "severity": 2,
  "location": "Current Status, paragraph 1",
  "evidence": "The vendor contract was reviewed by the finance team last quarter.",
  "violation": "The sentence uses a be-verb plus past-participle passive construction in a context where the actor is recoverable and worth naming directly.",
  "fix": "Rewrite the sentence in active voice, naming the actor that performs the action.",
  "confidence": "high"
}
```

Your run's exact wording may not match this one letter for letter (a fresh judged-lane pass can
phrase a violation or a fix slightly differently), but which criteria the four findings sit under,
and `gate: pass`, should not vary. If your result differs in kind rather than in wording, that
itself is worth noting: `bench/results/README.md` publishes exactly how much this skill's output
varies run to run, and it is not zero. The full committed reference is
[`skills/critique-clarity/examples/golden-01.json`](skills/critique-clarity/examples/golden-01.json).
The field contracts behind every one of these keys, what a schema can check and what only a human
reviewer can, are in `docs/reference/critique-contract.md`.

## 4. Record one disposition

Critique never edits your artifact. A human decides what happens to each finding: accept, reject,
or defer (`docs/explanation/methodology.md`, Section 10, "Human-in-the-loop by contract"). Pick
one finding, F-001 above, and record a decision on it. Full logging conventions, including where a
running log lives and how acceptance rate feeds back into the library, are in
`docs/how-to/dispositions.md`; the minimum a single decision needs is this shape, saved anywhere
convenient (`disposition.json` in your working directory is fine):

```json
{
  "contract_version": "1.0.0",
  "envelope": {
    "skill": "critique-clarity",
    "skill_version": "0.1.0",
    "artifact": "skills/critique-clarity/examples/clarity-golden-01-passive-and-nominalization.md",
    "artifact_sha256": "10e2c8bde7e7427efb74b6f306aa2f6630f8aef35cd145131ba5b6a5eaf3efa2",
    "timestamp": "2026-07-31T18:05:00Z"
  },
  "dispositions": [
    {
      "finding_id": "F-001",
      "criterion": "PLAIN-ACTIVE",
      "disposition": "accept",
      "note": "Confirmed passive construction with a recoverable actor; rewriting to active voice."
    }
  ]
}
```

If your own run's `artifact_sha256` or `timestamp` differ from the reference envelope above, use
your own run's values instead; the disposition log's `envelope` block has to name the actual run it
disposes findings from. Confirm the log itself is well-formed:

```
python -m contract.validate disposition.json
```

`valid` means the document holds together as a disposition log. It does not mean the disposition
you recorded was the right call; that judgment is yours, which is the whole point of Section 10.

That is the complete loop this library exists to support: critique, disposition. Nothing above
edited your document. Only you decided what changes.

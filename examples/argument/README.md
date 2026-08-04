---
title: Worked example - critique-argument
description: A full walkthrough of critiquing one argumentative memo with critique-argument, from the scripted lane through a filled-in disposition log
audience: both
level: beginner
---

# Worked example: critique-argument

This is a complete, self-contained walkthrough of running `critique-argument` against one real
artifact: the command you can re-run yourself, the full findings, and a human's actual decisions on
those findings. Everything in this folder is either something you can reproduce bit-for-bit on your
own machine, or content copied verbatim from this repository's validated golden fixtures and clearly
labeled as such. Nothing here is invented for the occasion.

## The artifact

[`artifact.md`](artifact.md) is a short internal memo, "Onboarding Checklist Pilot: Early Notes." An
onboarding team ran a two-month pilot of a redesigned new-hire checklist, saw time-to-productivity
drop from six weeks to two, and is writing up what that might mean for a wider rollout. It is
argumentative prose in the sense `critique-argument` cares about: it exists to get a reader to accept
some conclusion about what to do next, so it is fair game for a Toulmin-model critique (claim,
grounds, warrant, backing, qualifier, rebuttal).

It is copied verbatim, byte-for-byte, from this skill's own golden fixture at
`skills/critique-argument/examples/argument-golden-02-hedge-and-marker.md`. Both files hash to the
same `artifact_sha256`
(`f8df42e689f882da0e5d6910158466c48a03b1a02f93ae3d6b9df76d49aa9082`), confirmed below.

## Running the scripted lane yourself (bit-for-bit reproducible)

`critique-argument` implements two of its eight criteria as a deterministic script:
`TOULMIN-CLAIM-MARKER` (is the conclusion signposted) and `TOULMIN-HEDGE-DENSITY` (what fraction of
sentences carry a hedging word). From this repository's root, run:

```
python skills/critique-argument/scripts/checks.py examples/argument/artifact.md
```

That is the exact command this walkthrough was written against. Running it produces this (your own
`timestamp` field will differ, since it is wall-clock time at the moment you run it; everything else
should not):

```json
{
  "findings": [
    {
      "confidence": "high",
      "criterion": "TOULMIN-HEDGE-DENSITY",
      "evidence": "6 of 10 sentences (0.60) carry at least one hedging term.",
      "fix": "Remove the hedge from sentences whose claim the evidence actually supports, reserving qualification for the claims that genuinely need it.",
      "id": "F-001",
      "lane": "scripted",
      "location": "the whole document, under its \"Onboarding Checklist Pilot: Early Notes\" heading",
      "severity": 3,
      "violation": "More than 0.35 of the artifact's sentences carry a term from the hedging lexicon (may, might, could, possibly, perhaps, arguably, somewhat, relatively, it seems, appears to, tends to, to a degree), spread across the whole document rather than concentrated where the evidence actually underdetermines the claim."
    },
    {
      "confidence": "high",
      "criterion": "TOULMIN-CLAIM-MARKER",
      "evidence": "0 conclusion-marker phrases found across 286 words.",
      "fix": "Add an explicit conclusion-signalling phrase at the point the artifact states its central claim, for example \"therefore\" or \"we recommend\".",
      "id": "F-002",
      "lane": "scripted",
      "location": "the whole document, under its \"Onboarding Checklist Pilot: Early Notes\" heading",
      "severity": 2,
      "violation": "No phrase from the conclusion-marker lexicon (therefore, thus, hence, it follows that, we recommend, this paper argues, I argue that, the conclusion is, in conclusion, we should, the case for) appears anywhere in the artifact, so a reader scanning rather than reading straight through has no signpost to where the conclusion is asserted."
    }
  ],
  "run": {
    "artifact": "examples/argument/artifact.md",
    "artifact_sha256": "f8df42e689f882da0e5d6910158466c48a03b1a02f93ae3d6b9df76d49aa9082",
    "contract_version": "1.0.0",
    "model": "none",
    "rubrics": ["TOULMIN"],
    "skill": "critique-argument",
    "skill_version": "0.1.0",
    "timestamp": "2026-08-02T14:35:06Z"
  },
  "summary": {
    "by_severity": {"0": 0, "1": 0, "2": 1, "3": 1, "4": 0},
    "gate": "fail",
    "severity_3_threshold": 0,
    "suppressed_count": 0
  }
}
```

That command was actually run against this exact copy of the artifact while writing this page, and
the output above is what it printed. Re-run it yourself and you will get the same two findings, the
same evidence strings, the same severities. `model: "none"` is expected: the scripted lane does no
model reasoning at all, which is the whole point of it being deterministic.

**Note the finding IDs will not match `envelope.json`'s.** `envelope.json` (below) is the full,
mixed-lane run: one judged finding plus these same two scripted findings, ranked together, so the
scripted findings land as `F-002` and `F-003` there instead of `F-001` and `F-002`. The IDs are
positional, assigned after ranking the whole run's findings; the criterion, evidence, violation, fix,
and severity on each scripted finding are identical either way. That is what "bit-for-bit
reproducible" means here: the content, not the numbering, which depends on what else shares the run.

## Running the full critique (judged lane, in a Claude Code session)

The scripted lane above is only two of `critique-argument`'s eight criteria. The other six, including
whether there is a single stated claim at all, need judgment, which means running the skill itself,
normally through the `critique-critic` subagent so the critique runs in a fresh context that has not
seen the artifact being drafted or defended. In a Claude Code session with this plugin installed, the
plain-language way to ask for it is something like:

> Critique this with critique-argument: `examples/argument/artifact.md`

or, more generally, any request that reads as asking for a review, a second opinion, or a check on
whether an argument holds up. If nothing triggers automatically, ask explicitly: "Use
critique-argument on that file." Either way, what comes back is one contract-valid run envelope, the
same three-part shape (`run`, `findings`, `summary`) as the scripted lane's own output, just with the
six judged criteria swept as well.

**This is where honesty labeling matters.** A judged finding is a model's reasoned assessment, not a
deterministic computation. Two runs against the same artifact can phrase a violation or a fix
differently even when they agree on the substance, and this skill's own documentation says so
plainly. The judged finding this page walks through below did not come from re-running the critique
live for this page; it is copied verbatim from `skills/critique-argument/examples/golden-02.json`,
this skill's own validated golden fixture for this exact artifact, curated and checked by the skill's
authors before it shipped. Treat it as a faithful, representative illustration of what a judged sweep
against this artifact finds, not as a transcript of a live run.

## envelope.json

[`envelope.json`](envelope.json) is the full run envelope: the two scripted findings above plus one
judged finding, ranked together the way a real run would emit them. It is the `expected_envelope`
object copied verbatim from `skills/critique-argument/examples/golden-02.json`, this skill's own
validated golden fixture, so the judged content in it is curated illustration in the sense described
above, while the scripted content in it is exactly what the command above produces (modulo ID
numbering and timestamp, as noted).

It validates clean against the contract:

```
$ python -m contract.validate examples/argument/envelope.json
valid
$ echo $?
0
```

Run against this repository before writing this page.

## Findings tour

Three findings, one from each severity and lane combination this run produced. Full field detail is
in `envelope.json`; this section explains each in plain language.

### F-001, TOULMIN-CLAIM, severity 3, judged (curated illustration)

**What you would see:** paragraph 4 of the memo reads, "Rolling the checklist out more broadly is
something the team might want to consider, perhaps starting with one additional department next
quarter, though it may be worth waiting for a second cohort before treating the two-week figure as a
stable number rather than a pilot-window coincidence."

**Why it is a violation:** `TOULMIN-CLAIM` asks whether the artifact states one central conclusion,
specific enough to disagree with, outright rather than left for the reader to infer (`TOULMIN.md`,
`TOULMIN-CLAIM`). This paragraph floats two different next steps, rolling out further or waiting for
a second cohort, and never picks one. There is no single sentence, built only from the memo's own
wording, that says what it is asking the reader to do.

**What the fix means:** the author needs to pick one recommendation and say it plainly, for example
either "wait for a second pilot cohort before expanding" or "roll out to one additional department
next quarter," not both left open at once.

**What severity 3 signals:** per the shared 0-4 scale, severity 3 means "major, fix before release."
A reader genuinely cannot reconstruct what the memo is asking for, and that is exactly the kind of
gap the scale reserves level 3 for: something the reader cannot repair on their own from what the
artifact supplies.

### F-002, TOULMIN-HEDGE-DENSITY, severity 3, scripted (bit-for-bit reproducible)

**What you would see:** the scripted-lane output above, `"6 of 10 sentences (0.60) carry at least one
hedging term."`

**Why it is a violation:** `TOULMIN-HEDGE-DENSITY` flags a document where a hedging term (may, might,
could, possibly, and similar) shows up in more than 0.35 of its sentences, on the reasoning that past
that point a reader has no way to tell which claims the author actually stands behind (`TOULMIN.md`,
`TOULMIN-HEDGE-DENSITY`). This memo's 0.60 ratio clears both the 0.35 violation threshold and the
0.50 line that separates severity 2 from severity 3.

**What the fix means:** strip the hedge from sentences whose evidence actually supports a plain
claim, and keep qualification only where the evidence genuinely falls short.

**What severity 3 signals:** the same "major, fix before release" level as F-001, but note this
finding is a measurement, not a verdict; see the disposition on it below for why a human reviewer did
not simply accept it as written.

### F-003, TOULMIN-CLAIM-MARKER, severity 2, scripted (bit-for-bit reproducible)

**What you would see:** the scripted-lane output above, `"0 conclusion-marker phrases found across
286 words."`

**Why it is a violation:** `TOULMIN-CLAIM-MARKER` asks whether the artifact carries at least one
explicit conclusion-signalling phrase (therefore, we recommend, in conclusion, and similar) so a
reader scanning rather than reading straight through can find the ask without reconstructing it from
context (`TOULMIN.md`, `TOULMIN-CLAIM-MARKER`). This memo has zero.

**What the fix means:** add one such phrase at the point the memo actually lands on its
recommendation, for example "we recommend" or "therefore."

**What severity 2 signals:** "minor, backlog" on the shared scale. A missing signpost costs a
scanning reader something, but a reader who starts at the top and reads through still reaches the
memo's content; it does not block understanding the way F-001 and F-002 do.

## Disposition log

[`dispositions.json`](dispositions.json) is a human's actual decisions on these three findings,
schema-valid against `#/$defs/dispositionLog`, and checked against `envelope.json` itself so every
`finding_id` it references is confirmed to resolve:

```
$ python -m contract.validate examples/argument/dispositions.json
valid
$ echo $?
0
```

Both checks (schema shape, and resolution against the referenced envelope) were run against this
repository before writing this page.

| Finding | Criterion | Disposition | Reason |
|---|---|---|---|
| F-001 | `TOULMIN-CLAIM` | accept | Confirmed against the artifact: paragraph 4 really does leave two options open with no sentence choosing between them. Needs to be settled before anyone decides on a wider rollout. |
| F-002 | `TOULMIN-HEDGE-DENSITY` | reject | The 0.60 ratio is real, but nearly all of the hedging tracks limitations the memo itself names (small sample, an unrepresentative cohort, a manager-availability confound). Stripping those hedges to pass the ratio would overstate what one pilot actually supports, so the wording stands as written on this point. |
| F-003 | `TOULMIN-CLAIM-MARKER` | accept | Cheap, low-risk fix; adding a marker phrase where the memo lands on its recommendation costs nothing and helps a reader who is skimming. |

The F-002 reject is not this walkthrough being contrarian for effect. This skill's own reference
material says explicitly that a high hedge ratio is a measurement, not a verdict, and that whether
hedging is appropriate is a separate, judged question (`TOULMIN-HEDGE-DENSITY`'s own criterion text;
`references/severity-anchors.md`, "Calibration for the scripted lane"). Here the hedging tracks real,
named uncertainty rather than padding, which is exactly the case that reference material anticipates
and which the golden fixture's own curation notes confirm was deliberately not raised as a separate
`TOULMIN-QUALIFIER` violation. A reviewer who always accepted every finding without weighing it
against the artifact would not be doing review; this is what an honest disposition on a real,
defensible mechanical finding looks like.

## What is bit-for-bit versus curated, summarized

- **Bit-for-bit reproducible:** `artifact.md`'s content (verified by matching `artifact_sha256`); the
  `python skills/critique-argument/scripts/checks.py examples/argument/artifact.md` command and its
  two scripted findings (F-002 `TOULMIN-HEDGE-DENSITY`, F-003 `TOULMIN-CLAIM-MARKER` in
  `envelope.json`'s numbering); both `contract.validate` runs shown above.
- **Curated illustration from validated golden fixtures:** the judged finding (F-001
  `TOULMIN-CLAIM`) in `envelope.json`, copied verbatim from `skills/critique-argument/examples/golden-02.json`
  rather than produced live for this page; the disposition log's reasoning, which is authored for
  this walkthrough (a real disposition is always a human judgment call, never a reproducible
  computation) but grounded in the same golden fixture's own curation notes.

Nothing on this page is presented as a live run except the scripted-lane command and its two
validator checks, all three of which were actually executed against the files in this folder.

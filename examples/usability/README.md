---
title: critique-usability worked example
description: A walkthrough of critiquing one UI spec end to end, reproducing the scripted lane yourself and reading a curated judged-lane pass, through to a filled-in disposition log
audience: both
level: beginner
---

# critique-usability, worked example

This is one complete pass through `critique-usability`: an artifact, a critique of it, and the human
decisions that came after. If you are a PM, a designer, or a technical writer deciding whether to
trust this skill on your own work, this page is the place to see what it actually produces before
you point it at something real.

## What the artifact is

`artifact.md` in this folder is a markdown UI spec for a "Team workspace settings" screen. It
describes three things a designer or engineer would need to build: a member list with a row of
action buttons, a "Danger zone" section with a Delete workspace control, and a bulk-import feature
that can fail. It is a spec, not a live page. Nobody clicked anything to produce it; it is text a
critic can read and reason about, the same way it is the kind of file this skill is built to review
before a screen like it goes to engineering.

It is copied verbatim from
`skills/critique-usability/examples/artifacts/golden-02-workspace-danger-zone.md`, one of this
skill's own validated golden fixtures, so this folder is self-contained: everything you need to
reproduce what follows is here, with the file byte-for-byte identical to its source.

## Honesty labeling

Two different things are true about the findings below, and this page keeps them apart:

- **Scripted lane, bit-for-bit reproducible.** One finding comes from `scripts/checks.py`, a
  deterministic script. Run the exact command below yourself and you get the exact JSON below,
  every time, on any machine. This section was verified by actually running the command, not typed
  from memory.
- **Judged lane, curated from a validated golden fixture.** Two findings come from a model reading
  the spec against the rubric, the same four-pass protocol a live `critique-usability` run follows.
  These are not something this page ran live and pasted in; they are copied verbatim from this
  skill's own golden envelope (`skills/critique-usability/examples/golden-02.json`), a fixture that
  passed `python -m contract.validate` before it was accepted into the skill's test suite. A live
  judged-lane run against the same artifact should land on the same criteria and the same severities,
  but the exact wording of `violation` and `fix` can vary run to run, the way any model output does.

Nothing on this page is authored content presented as a live run. Where a claim is reproducible, the
command to reproduce it is given. Where it is curated, that is stated plainly, right next to it.

## Running the scripted lane yourself

From the repository root:

```
python skills/critique-usability/scripts/checks.py examples/usability/artifact.md
```

This is what that command actually printed when this example was built:

```json
{
  "findings": [
    {
      "confidence": "high",
      "criterion": "NNG-H6-LABELED",
      "evidence": "list entry \"Button\"",
      "fix": "Add the control's own label to this entry, alongside its role.",
      "id": "F-001",
      "lane": "scripted",
      "location": "the \"Controls\" list, item 3 (\"Button\")",
      "severity": 2,
      "violation": "This control list entry names the control only by its role, with no distinguishing label a user could read to tell it apart from another control of the same kind."
    }
  ],
  "run": {
    "artifact": "examples/usability/artifact.md",
    "artifact_sha256": "1d4fcad7631afb2897d6efc03302a07ad81096d055a3d98e4abf33f3137ff547",
    "contract_version": "1.0.0",
    "model": "none",
    "rubrics": ["NNG"],
    "skill": "critique-usability",
    "skill_version": "0.1.0",
    "timestamp": "2026-08-02T14:34:07Z"
  },
  "summary": {
    "by_severity": {"0": 0, "1": 0, "2": 1, "3": 0, "4": 0},
    "gate": "pass",
    "severity_3_threshold": 0,
    "suppressed_count": 0
  }
}
```

Only your `timestamp` will differ; everything else, including `artifact_sha256`, reproduces exactly
because the scripted lane is a deterministic pattern match over the file's structure, not a model
call. This is the same finding as `F-002` in the full envelope below (`envelope.json`), field for
field: same criterion, same location, same evidence, same violation, same fix. The ID differs only
because the scripted lane numbers findings within its own run, while the full envelope numbers all
findings, both lanes, together, in the skill's fixed sweep order. Content, not the label, is the
reproducible part.

The scripted lane only ever covers three of this skill's twenty criteria (`NNG-H3-DEADEND`,
`NNG-H4-CONTROL-NAMING`, `NNG-H6-LABELED`); that is why one command run produces one finding here,
not three.

## Running the full critique

Inside a Claude Code session with this plugin installed, the natural way to ask for the full
critique, both lanes, is to just say so:

> Critique this with critique-usability.

or, pointed at this file directly:

> Review `examples/usability/artifact.md` for usability.

Either phrasing matches this skill's own trigger description, so it fires without naming
`critique-critic` yourself. Under the hood, `critique-usability`'s `SKILL.md` hands the artifact to
the `critique-critic` subagent, which runs in a fresh context that has never seen this page or any
framing about the artifact, sweeps every criterion in fixed order, runs `scripts/checks.py` itself
for the scripted lane, and returns one contract-valid run envelope, the same shape as `envelope.json`
in this folder. Unlike the command above, this step calls a model, so it is not bit-for-bit
reproducible; expect the same criteria and severities, not always identical wording.

## Findings tour

`envelope.json` in this folder is the full, validated golden envelope for this artifact, both lanes
combined: three findings, one scripted, two judged. Here is what each one means in plain language.

### F-001, NNG-H5-CONFIRM, severity 3, judged

**What you would see:** the spec's "Danger zone" section describes a Delete workspace control. Per
the spec's own words, activating it removes the workspace, every document in it, and every member's
access, and the very next screen is the workspace list. Nothing sits between the click and that
outcome.

**Why it is a violation:** heuristic 5 (error prevention) asks that a costly or unrecoverable action
be gated behind a confirmation that names what is about to happen, rather than firing on a single
click. This is not a guess about how the built page might behave; the spec states the path itself,
control straight to workspace list, with nothing named in between.

**What the fix means:** add a confirmation step before the delete actually fires, one that names the
workspace by name and says plainly that the action cannot be undone.

**What severity 3 signals:** major, fix before release. This is not a nice-to-have. A single
mis-click destroys every document and every member's access for the whole team with no way back, so
it blocks shipping rather than going on a backlog.

### F-002, NNG-H6-LABELED, severity 2, scripted

**What you would see:** under "Members," a list titled "Controls" has three entries. The first two
read "Remove member button" and "Promote to admin button." The third just reads "Button."

**Why it is a violation:** heuristic 6 (recognition rather than recall) asks that every control the
spec defines carry a name a person can read, not one they have to infer from where it sits in a
list. This third entry is exactly a bare role noun with nothing distinguishing it, which is the
pattern this skill's scripted check exists to catch mechanically, no judgment required.

**What the fix means:** give the third control its own name alongside its role, whatever it is
actually meant to do, for example "Deactivate member button."

**What severity 2 signals:** minor, backlog. The two sibling entries are properly labeled, so a
reader has a partial cue about what this row probably does; it is confusing, not blocking.

### F-003, NNG-H9-IDENTIFY, severity 2, judged

**What you would see:** a bulk import that accepts up to 12 rows. When it fails, the screen shows
"Something went wrong. Try again," a Retry button, and the number of rows that were submitted.
Nothing shows which rows failed or why.

**Why it is a violation:** heuristic 9 (help users recognize and recover from errors) asks that
error text say in plain language what went wrong, specifically enough that the person can tell which
of their own entries caused it. This message reports only that the import failed as a whole.

**What the fix means:** report which rows failed and what condition failed on each one, for example
"row 4, missing email address," not just a count.

**What severity 2 signals:** minor, backlog rather than blocking. The batch is capped at 12 rows and
Retry is present, so a user still has a slow way to narrow the problem down by trial. That is what
keeps this a 2 rather than a 3.

## Disposition log

Critique never edits the artifact and never auto-applies a fix; a person decides what happens to
each finding. `dispositions.json` in this folder is that decision, recorded against `envelope.json`,
`accept`, `reject`, or `defer` with a one-line reason on each. Not every finding gets accepted here,
on purpose: always-accept is not what review actually looks like.

| Finding | Criterion | Severity | Disposition | Why |
|---|---|---|---|---|
| F-001 | NNG-H5-CONFIRM | 3 | accept | One click destroys the workspace with no confirmation and no undo. Fixing before this ships. |
| F-002 | NNG-H6-LABELED | 2 | accept | Cheap fix, bundled into the same pass as the confirmation copy. |
| F-003 | NNG-H9-IDENTIFY | 2 | defer | Real gap, agreed, but the import flow is already scheduled for a rework next quarter. Not worth polishing a screen about to be replaced; revisit if the rework slips. |

That defer is the honest kind: the reviewer is not disputing that F-003 names a real problem, they
are saying it loses to a competing priority right now, and the note says exactly that rather than
hiding a punt behind a vague "later."

## Validating the files in this example

Both JSON files here were checked against the contract before this page was written, not asserted
clean:

```
python -m contract.validate examples/usability/envelope.json
valid
python -m contract.validate examples/usability/envelope.json --gate
valid
(exit code 2, meaning "fail": one severity-3 finding above the default threshold of 0)

python -m contract.validate examples/usability/dispositions.json
valid
```

Resolving `dispositions.json`'s finding IDs against `envelope.json` needs both files loaded together
(the single-file CLI cannot do this on its own; see `docs/how-to/dispositions.md`), and that check
also ran clean before this page shipped, every `finding_id` in the log resolves in the envelope, and
every denormalized `criterion` matches.

## Files in this folder

| File | What it is |
|---|---|
| `artifact.md` | The UI spec being critiqued. Verbatim copy of `skills/critique-usability/examples/artifacts/golden-02-workspace-danger-zone.md`. |
| `envelope.json` | The full, validated run envelope for this artifact, both lanes. Verbatim copy of the `expected_envelope` in `skills/critique-usability/examples/golden-02.json`. |
| `dispositions.json` | This walkthrough's disposition log against `envelope.json`. |
| `README.md` | This page. |

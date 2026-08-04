---
title: critique-microcopy worked example - signup and checkout error copy
description: A walkthrough of critiquing an annotated error-message artifact with critique-microcopy, reading the findings, and recording dispositions on them.
audience: both
level: beginner
---

# critique-microcopy worked example

This is a walkthrough, not a tool. It shows one artifact going through
`critique-microcopy` end to end: run it, read what comes back, and decide what to
do with each finding. If you are a PM, designer, or writer deciding whether to trust
this skill, start here before reading `SKILL.md`.

## What is in this folder

| File | What it is | How it was produced |
|---|---|---|
| [`artifact.md`](artifact.md) | The thing being critiqued: three error messages on a signup and checkout flow, annotated with placement, container, timing, and behavior. Verbatim copy of `skills/critique-microcopy/examples/microcopy-golden-01-signup-checkout.md`, the skill's own richest golden fixture. | Copied byte for byte; see "Reproducing this" below. |
| [`envelope.json`](envelope.json) | The full run result: every finding, at every severity, from both lanes. Verbatim copy of the `expected_envelope` in `skills/critique-microcopy/examples/golden-01.json`, this library's validated golden reference for this artifact. | Curated: authored and validated by the skill's own team, not generated fresh by this walkthrough. |
| [`dispositions.json`](dispositions.json) | A human's accept, reject, and defer decisions against every finding in `envelope.json`. | Authored for this walkthrough; see "Disposition log" below. |

## What is bit-for-bit reproducible here, and what is not

This example mixes two honestly-different kinds of content, and the difference
matters:

- **Scripted-lane findings are bit-for-bit reproducible.** They come from
  `scripts/checks.py`, a deterministic script with no model in the loop. Run the
  exact command below on `artifact.md` and you get the same eight findings, the
  same severities, the same evidence strings, every time, on any machine.
- **Judged-lane findings are curated illustration**, taken from this skill's
  validated golden fixture, not generated live by this walkthrough. They show
  what a careful judged-lane pass looks like on this artifact, following the same
  four-pass protocol `SKILL.md` defines, but a fresh judged pass can phrase a
  violation or a fix slightly differently even when it lands on the same
  criterion and severity (this is stated plainly in `QUICKSTART.md` too: wording
  varies, gate and criteria should not).

`envelope.json` carries both lanes together, and each finding's `lane` field
says which is which. Nothing in this walkthrough is presented as a live run
except the scripted-lane command below, which really was run against the copy
of the artifact in this folder before this README was written.

## Run the scripted lane yourself

From a repo checkout, at the repo root:

```
python skills/critique-microcopy/scripts/checks.py examples/microcopy/artifact.md
```

This reproduces 8 of the 10 findings in `envelope.json`: the six scripted
criteria this skill implements (`NNG-EM-CONSTRUCTIVE` three times,
`NNG-EM-TIMING`, `NNG-EM-NEUTRAL-TONE`, `NNG-EM-NOT-COLOR-ONLY`,
`NNG-EM-PLAIN-LANGUAGE`, `NNG-EM-PRESERVE-INPUT`) at identical criteria,
severities, locations, evidence, violations, and fixes. Finding IDs differ
(`F-001` through `F-008` here, interleaved with the two judged findings as
`F-001` through `F-010` in `envelope.json`), because the scripted lane run
alone has no judged findings to interleave with; that is a numbering artifact
of running one lane in isolation, not a content difference. The two judged
findings, `NNG-EM-SPECIFIC` and `NNG-EM-EXPLAIN`, do not appear from this
command: they need a model reading the screen context, which is exactly what
the judged lane is for.

**Reproduce note.** This command was run against the copy of `artifact.md` in
this folder as part of building this example, and its `run.artifact_sha256`
matched the golden fixture's `f8df984e8ac086ed...cc283` exactly, confirming
the copy is byte-identical to the source. The scripted findings it produced
matched `envelope.json`'s eight scripted-lane findings field for field. See
"Full envelope" below for the two additional judged findings that only a full
critique run adds.

## Run the full critique

The scripted lane alone only ever covers 6 of this skill's 14 criteria; the
other 8, including two of the five findings in the tour below, need a judged
pass. In a Claude Code session with this plugin installed, ask in plain
language:

> Critique `examples/microcopy/artifact.md` with critique-microcopy.

or more generally, without naming the skill:

> Give me a second opinion on this error copy before it ships.

Either phrasing triggers `critique-microcopy` on its own description. Where
the subagent tool is available, the skill delegates the run to `critique-critic`
so it critiques in a fresh context that has never seen this artifact being
discussed, drafted, or defended, the same clean-context guarantee that made
`envelope.json` trustworthy when it was first authored. What comes back is one
contract-valid run envelope, the same three top-level keys `envelope.json`
has: `run`, `findings`, `summary`.

## Findings tour

`envelope.json` has 10 findings. These five are the most instructive: they
show a scripted and a judged finding landing on the exact same sentence, a
timing defect a script alone can catch, and the tone/severity range a reader
should expect to see day to day. Rubric: NN/g's Error-Message Guidelines
(`NNG-EM`, `skills/critique-microcopy/references/NNG-EM.md`).

### F-001, `NNG-EM-CONSTRUCTIVE`, severity 3, scripted

**What you would see.** The checkout submit banner reads: "Something went
wrong. Try again."

**Why it is a violation.** `NNG-EM-CONSTRUCTIVE` asks a message to name a
concrete next step, not just announce that a problem exists. "Try again"
names no action for the reader to take, which is exactly why the scripted
check's own instruction-verb list leaves "try" out on purpose.

**What the fix means.** Replace the generic line with one that tells the
reader what to actually do, for example, check the card details and resubmit.

**What severity 3 signals.** Major: fix before release. The reader cannot
finish the task from what the message tells them, and nothing else on the
screen (`Suggested fix: none`) offers a way forward either.

### F-004, `NNG-EM-SPECIFIC`, severity 3, judged

**What you would see.** The same banner: "Something went wrong. Try again."

**Why it is a violation.** `NNG-EM-SPECIFIC` asks a different question than
F-001 above: not whether the message gives an instruction, but whether it
names the actual cause. A checkout submission is exactly the kind of screen
where a real cause, a declined card, a network timeout, an expired session,
is normally knowable, and this message names none of it.

**What the fix means.** Say what actually failed, not just that something
did.

**What severity 3 signals.** Major, same as F-001. Worth noticing: one
sentence breaching two criteria produces two findings, not one finding
promoted higher. `references/severity-anchors.md` calls this out directly:
criteria do not stack into severity.

### F-005, `NNG-EM-TIMING`, severity 3, scripted

**What you would see.** The password field's annotation: `Fires:
mid-keystroke`.

**Why it is a violation.** `NNG-EM-TIMING` asks a message to wait until the
reader has had a fair chance to finish typing. Firing mid-keystroke means the
reader can be told they are wrong before they could possibly be right.

**What the fix means.** Move validation to on-blur or on-submit, not while
the field still has focus and characters are still being typed.

**What severity 3 signals.** Major. The scripted rule ties this to whether
the message itself reads as an error while firing prematurely, which this one
does ("must be").

### F-007, `NNG-EM-NEUTRAL-TONE`, severity 2, scripted

**What you would see.** The confirm-password message: "You failed to match
the passwords. Error code: 004."

**Why it is a violation.** `NNG-EM-NEUTRAL-TONE` asks copy to stay neutral
rather than frame a routine mistake as something the reader personally did
wrong. "You failed to" is a listed accusatory phrase.

**What the fix means.** Restate the same fact without blame, for example, the
passwords do not match.

**What severity 2 signals.** Minor: backlog. This is friction, not a dead
end; a reader who rereads the sentence still understands what to fix. It
would have been severity 3 had the blame been paired with a repetition word
like "again" or "keep", which it is not here.

### F-006, `NNG-EM-EXPLAIN`, severity 2, judged

**What you would see.** The password-length message: "Password must be at
least 8 characters."

**Why it is a violation.** `NNG-EM-EXPLAIN` asks a message that states a
recurring rule to also say why the rule exists, when knowing the reason would
help the reader avoid the same problem again. This message states the
eight-character minimum with no reason attached.

**What the fix means.** Add a short clause naming the reason, for example, a
brief note that this is a security minimum.

**What severity 2 signals.** Minor: the reader can still comply and move on,
which is exactly why this is the finding a real reviewer pushed back on
below.

## Disposition log

A run never edits the artifact. A human decides what happens to each
finding: accept, reject, or defer (`docs/how-to/dispositions.md`). Nine of
the ten findings in `envelope.json` are accepted below at face value; two are
not, on purpose, because always-accept is not how real review works. The full
machine-readable log is [`dispositions.json`](dispositions.json), validated
against `contract/critique-contract.schema.json` and resolved against
`envelope.json`'s own finding IDs.

| Finding | Criterion | Disposition | Reason |
|---|---|---|---|
| F-001 | `NNG-EM-CONSTRUCTIVE` | accept | Confirmed dead end for the reader; rewriting before ship. |
| F-002 | `NNG-EM-CONSTRUCTIVE` | accept | Needs an instruction regardless of the tone and jargon fixes below. |
| F-003 | `NNG-EM-CONSTRUCTIVE` | accept | Small copy fix: add the concrete length instruction. |
| F-004 | `NNG-EM-SPECIFIC` | accept | Naming the real cause is the same rewrite as F-001, doing both together. |
| F-005 | `NNG-EM-TIMING` | accept | Confirmed in the live component; moving validation to on-blur. |
| F-006 | `NNG-EM-EXPLAIN` | **reject** | Eight characters is an industry-standard minimum most readers already expect; a reason clause here reads as filler, not help. |
| F-007 | `NNG-EM-NEUTRAL-TONE` | accept | Blame phrasing goes regardless of the error-code fix. |
| F-008 | `NNG-EM-NOT-COLOR-ONLY` | accept | Design system already has the icon; just needs wiring to this state. |
| F-009 | `NNG-EM-PLAIN-LANGUAGE` | accept | Error code means nothing to a user; moving it to a support-ticket log instead. |
| F-010 | `NNG-EM-PRESERVE-INPUT` | **defer** | Right fix, but needs a session-storage change on the backend; filed for next sprint rather than blocking this release. |

The reject on F-006 is a genuine disagreement with a judged-lane call, not a
process failure: `docs/reference/critique-contract.md` is explicit that
"whether the decision itself is right is outside every check here," and a
reviewer who thinks the eight-character minimum needs no explanation is
allowed to say so, in writing, with a reason. The defer on F-010 is the
opposite kind of case: the reviewer agrees the finding is correct but the fix
costs more than this release can absorb right now, so it goes to the backlog
instead of being waved through or silently dropped.

## Validate any of this yourself

```
python -m contract.validate examples/microcopy/envelope.json
python -m contract.validate examples/microcopy/dispositions.json
```

Both print `valid`. The disposition log's finding IDs were additionally
resolved against `envelope.json` directly (`docs/how-to/dispositions.md`,
"Recording a disposition"), since that check needs both documents loaded
together and does not run through the single-file CLI above.

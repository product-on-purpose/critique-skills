---
title: critique-clarity worked example
description: A full walkthrough of one critique-clarity run, from the scripted command to a filled-in disposition log
audience: both
level: beginner
---

# critique-clarity worked example

This folder is a self-contained example of `critique-clarity` reviewing a short prose document: the
artifact, the run's findings, and a human's decisions on those findings, all in one place. It exists
so you can decide whether to trust this skill before you point it at your own document.

**What's here:**

- `artifact.md` - the document under review.
- `envelope.json` - the critique run's findings, in the library's standard contract format.
- `dispositions.json` - a human's accept, reject, or defer decision on each finding.
- `README.md` - this walkthrough.

**What's bit-for-bit reproducible versus curated.** `critique-clarity` runs two lanes: a scripted
lane (fixed, deterministic pattern checks) and a judged lane (a model reading the artifact's
meaning). Everything below labeled `lane: scripted` is exactly what the printed command in
"Run the scripted lane yourself" produces; run it and compare your own output. The one finding
labeled `lane: judged` cannot come from that command; it is curated from this skill's validated
golden fixture (a run recorded and checked into the skill's own test suite), shown here as an
illustration of what the judged lane looks like, not as something the printed command reproduces.
A fresh judged-lane pass can phrase a violation or a fix slightly differently in its own wording;
only which criteria fire, and the severity, are expected to hold steady.

## The artifact

`artifact.md` is a verbatim copy of
`skills/critique-clarity/examples/clarity-golden-03-parallelism-and-cohesion.md`, one of this
skill's validated golden fixtures, copied byte for byte so this example is self-contained. It is a
short onboarding task list, two headings and three sentences total:

```
# Onboarding Task List

## Week One Checklist

The manual covers filing the report, to review the log, and closing the ticket.

## Notification Flow

The system routes new tickets to the queue. Slack sends a notification to the on-call engineer. The engineer confirms receipt within the hour.
```

Small on purpose. A three-sentence document is enough to show two rubrics catching different
problems on the identical sentence, and two lanes catching different problems in the identical
paragraph, without asking you to read a long document first.

## Run the scripted lane yourself

From a checkout of this repository:

```
python skills/critique-clarity/scripts/checks.py examples/clarity/artifact.md
```

This produces three findings (`PLAIN-PARAGRAPH`, `PLAIN-LISTS`, `WILLIAMS-PARALLELISM`), the same
criteria, severities, locations, evidence, violations, and fixes as the three `lane: scripted`
findings in `envelope.json`. One thing will differ: the command numbers its own findings `F-001`
through `F-003`, while `envelope.json` numbers the same three findings `F-001`, `F-002`, and `F-004`,
because `envelope.json` also carries the judged-lane finding at position `F-003`. Findings get their
IDs after every criterion in both lanes has been swept and ranked together, not from the scripted
lane alone, so a scripted-only run and the full run number differently even when their scripted
content matches exactly. This example was run against the command above before this page was
written, and the scripted content matched.

## Run the full critique

The scripted command above only covers 15 of this skill's 23 criteria; the other 8, including the
judged finding below, need a model reading the artifact. Inside a Claude Code session with this
plugin installed, plain language triggers it, no need to name the skill:

> Critique `examples/clarity/artifact.md` for clarity.

or, to be explicit about delegating to the clean-context critic subagent this skill uses:

> Use critique-critic on `examples/clarity/artifact.md` for critique-clarity.

What comes back is one contract-valid run envelope with the same shape as `envelope.json`. Your
run's exact wording on the judged finding may differ from the curated one below; that is expected
and is not itself a problem.

## Findings tour

Four findings came back on this three-sentence document, which is a lot for something this short.
That is intentional: two different rubrics (`PLAIN` and `WILLIAMS`) fire on the identical
checklist sentence, and two different lanes (scripted and judged) fire on the identical
notification paragraph, for genuinely different reasons. Walking all four is more instructive than
picking a "representative" one or two.

### F-001, PLAIN-PARAGRAPH, severity 3, scripted

**What you'd see:** under "Notification Flow," the paragraph opens with "The system routes new
tickets to the queue," then spends its remaining two sentences on Slack, a notification, and an
engineer confirming receipt, none of which shares any wording with the opening sentence.

**Why it's a violation:** `PLAIN-PARAGRAPH` (Federal Plain Language Guidelines, Sec. III.c.1,
III.c.3-4) expects a paragraph's opening sentence to preview what the rest of the paragraph
actually covers. Here it does not; a reader who trusts the opening sentence gets the wrong idea of
what follows.

**What the fix means:** rewrite the opener to name what the paragraph is actually about, for
example an actor or event that recurs across all three sentences, so the first sentence functions
as a real preview.

**What severity 3 signals:** major, fix before release. This is the paragraph's entry point; a
reader misled at the door is worse than a reader who trips once mid-paragraph, which is why this
outranks the other three findings here (all severity 2).

### F-002, PLAIN-LISTS, severity 2, scripted

**What you'd see:** "The manual covers filing the report, to review the log, and closing the
ticket." Three separate tasks folded into one sentence with commas.

**Why it's a violation:** `PLAIN-LISTS` (Federal Plain Language Guidelines, Sec. III.d.2-3) expects
parallel items like these to be presented as a visible list, not folded into a run-on sentence.

**What the fix means:** reformat the three tasks as a bulleted or numbered list so a reader can
scan them instead of parsing a sentence to find them.

**What severity 2 signals:** minor, backlog. Nothing here blocks a reader: filing, reviewing, and
closing are all still recoverable from the sentence; it is just harder to scan than it needs to be.

### F-003, WILLIAMS-COHESION, severity 2, judged, curated from the golden fixture

**What you'd see:** the same three "Notification Flow" sentences as F-001, read as connected
discourse rather than checked for opener-to-body vocabulary overlap: "The system routes new tickets
to the queue. Slack sends a notification to the on-call engineer. The engineer confirms receipt
within the hour." Each sentence's subject changes (the system, then Slack, then the engineer), and
nothing in the first sentence gives the reader a basis for Slack showing up in the second.

**Why it's a violation:** `WILLIAMS-COHESION` (*Style: Lessons in Clarity and Grace*, ch. 5) expects
each sentence to open with something the reader already has, and successive subjects to track one
running topic rather than jump between unrelated ones. This is a judged criterion; deciding whether
a subject shift breaks the reader's thread takes reading the passage's meaning, not a fixed pattern,
which is why the scripted command above cannot produce this finding on its own.

**What the fix means:** open the paragraph with the actor that actually connects all three
sentences, for example the ticket itself, so each sentence's subject picks up where the one before
it left off.

**What severity 2 signals:** minor, backlog, not 3. The disruption is partial, not total: the third
sentence's "the engineer" does pick up "the on-call engineer" from the second sentence, so the
paragraph partly recovers its own thread. A paragraph that changed subject in every sentence with
nothing ever picked back up would be the severity 3 version of this same criterion.

Worth noticing: F-001 and F-003 are two different lanes reading the identical paragraph and
reporting two different, genuinely separate problems, a word-overlap gap at the opener (scripted)
and a subject-tracking gap across all three sentences (judged). Neither lane is doing the other's
job worse; they are answering different questions about the same passage.

### F-004, WILLIAMS-PARALLELISM, severity 2, scripted

**What you'd see:** the same checklist sentence as F-002: "filing the report" (a gerund), "to
review the log" (an infinitive), and "closing the ticket" (a gerund again) mix grammatical forms in
one series.

**Why it's a violation:** `WILLIAMS-PARALLELISM` (*Style: Lessons in Clarity and Grace*, ch. 11)
expects items in a series to share one grammatical form so a reader processes them as one pattern
instead of three unrelated fragments.

**What the fix means:** restate every item in the same form, for example filing, reviewing, and
closing, all gerunds.

**What severity 2 signals:** minor, backlog. The mismatch slows reading rhythm; it does not block
understanding which three tasks are meant.

Worth noticing here too: F-002 and F-004 fire on the exact same sentence from two different
rubrics, one flagging that the items should be a list at all, the other flagging that the items
inside it do not match grammatically. Both are true of the same six words at once.

## Disposition log

`dispositions.json` records one human's decision on each of the four findings above. Always-accept
is not how real review works, so this log includes one reject and one defer, each with its
reasoning, alongside two accepts.

| Finding | Criterion | Decision | Why |
|---|---|---|---|
| F-001 | `PLAIN-PARAGRAPH` | accept | The opener genuinely misleads about what follows; worth the one-line rewrite before this ships. |
| F-002 | `PLAIN-LISTS` | reject | Technically correct, but this is a one-sentence checklist intro, not a customer-facing procedure. Fixing the parallelism (F-004) already makes it read fine; a bulleted list for three two-word tasks is more structure than the passage needs. |
| F-003 | `WILLIAMS-COHESION` | defer | Real finding, but the F-001 rewrite may resolve it on its own by naming a connecting actor. Re-check after that edit lands before doing separate work. |
| F-004 | `WILLIAMS-PARALLELISM` | accept | Cheap fix, do it alongside F-001. |

Validated:

```
$ python -m contract.validate examples/clarity/envelope.json
valid
$ python -m contract.validate examples/clarity/dispositions.json
valid
```

Both commands were run against this repository's validator before this page was written.

## See also

- [Severity scale](../../docs/reference/severity-scale.md), the 0-4 scale every finding's severity
  comes from.
- [Dispositions](../../docs/how-to/dispositions.md), the full shape and purpose of the disposition
  log format used above.
- [Critique contract](../../docs/reference/critique-contract.md), the field-by-field envelope
  reference.

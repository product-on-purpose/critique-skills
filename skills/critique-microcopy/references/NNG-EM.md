# NNG-EM rubric source

The criterion registry for `critique-microcopy`. Every row below operationalizes one NN/g
error-message guideline in this library's own wording; no source text is reproduced
([ADR 0006, copyright paraphrase policy](../../../docs/internal/decisions/0006-copyright-paraphrase-policy.md),
[methodology section 11](../../../docs/explanation/methodology.md)).

## Source

- **`rubric_sources.id`:** `NNG-EM`
- **Citation:** Neusesser, T. and Sunwall, E. (2023). Error-Message Guidelines. Nielsen Norman Group.
  Published May 14, 2023.
- **`url`:** https://www.nngroup.com/articles/error-message-guidelines/
- **`accessed`:** 2026-07-31
- **`operationalization`:** `paraphrased`

The article organizes its 13 numbered guidelines into four groups, in this order: Visibility
(guidelines 1 to 4, where and how prominently a message appears), Communication (guidelines 5 to 8,
what the message says), Efficiency (guidelines 9 to 12, how much work the message leaves the reader),
and Special Situations (guideline 13, total and unrecoverable failure). The 14 criteria below preserve
that grouping, splitting guideline 2 into two independently checkable IDs, sufficient visual salience
and a non-color cue for colorblind readers, per
[criterion-ids.md](../../../docs/reference/criterion-ids.md)'s one-criterion-one-ID rule. Every other
guideline maps one to one.

A note on namespace: this skill's criterion namespace is `NNG`, the same source letter
`critique-usability`'s Nielsen-heuristics rubric uses
([criterion-ids.md](../../../docs/reference/criterion-ids.md), "Namespace registry"). The two rubrics
are unrelated NN/g publications that happen to share a source letter by convention; no individual ID
collides, because every criterion below is prefixed `NNG-EM-` rather than bare `NNG-`.

## Artifact format

Resolved by [ADR 0018 (microcopy artifact format)](../../../docs/internal/decisions/0018-microcopy-artifact-format-annotated-context.md):
annotated context, encoded as the `bench` artifact type `markdown-prose`, not a bare string list. An
artifact is one or more screens, each a `##` heading naming the screen or state, and under each
heading one labeled block per message:

- `Message`: the exact user-facing string.
- `Placement`: where the message sits relative to the control it concerns, free text.
- `Container`: `inline`, `toast`, or `modal`.
- `Signal`: the message's visual-weight description, plus a non-color-cue token drawn from `none`,
  `icon`, `text-label`, `shape-change`, `bold`, `underline`.
- `Fires`: when the message appears, drawn from `on-blur`, `on-submit`, `after-field-complete`,
  `mid-keystroke`, `on-load-before-input`, `on-focus`.
- `Predictable mistake`: `yes` or `no`.
- `Input on resubmission`: `preserved`, `cleared`, or `not-applicable`.
- `Suggested fix`: `none`, `described`, or `selectable`, plus a one-line note on what it recommends.

`Message` is the only field that is literally the artifact's own user-facing content; every other
field is reviewer-supplied screen context, standing in for what a screenshot or a live render would
otherwise show. Each message block addresses through `markdown-prose`'s existing anchors, heading path
and paragraph index, so the shared location-tolerance rule in
[ADR 0015](../../../docs/internal/decisions/0015-location-tolerance-per-artifact-type.md) applies with
no change.

Six criteria read the `Message` text alone: `NNG-EM-CONSTRUCTIVE`, `NNG-EM-EXPLAIN`, `NNG-EM-GRACE`,
`NNG-EM-NEUTRAL-TONE`, `NNG-EM-PLAIN-LANGUAGE`, `NNG-EM-SPECIFIC`. The other eight each read at least
one annotation field, which is the coverage argument
[ADR 0018](../../../docs/internal/decisions/0018-microcopy-artifact-format-annotated-context.md)
turns on. That 6-and-8 split is what decides which criteria have anything to evaluate when a caller
supplies a bare list of strings instead of annotated screens; see `SKILL.md`, pass 2.

The controlled-vocabulary tokens above are v0.1 defaults, not yet measured against a real
corpus; a downstream corpus-module or `scripts/checks.py` author who needs a token this list lacks
extends it additively and records the addition here, rather than repurposing an existing token.

## Registry

Fourteen criteria, ascending ID order, the order `SKILL.md`'s pass 2 sweeps them in.

| ID | Operationalization | Operational test | Severity 2 anchor | Severity 3 anchor | Lane | Lane rationale |
|---|---|---|---|---|---|---|
| NNG-EM-CONSTRUCTIVE | The message tells the reader what to do next to resolve the problem, not only that a problem exists. | Read the `Message` text for an instruction naming a concrete action the reader can take: enter, choose, remove, contact, upload, and the rest of the closed verb list `scripts/checks.py` carries as `INSTRUCTION_MARKERS`. A bare retry exhortation (trying again, having another go) is not an instruction, because it names no change for the reader to make; it is deliberately absent from that list. Flag a violation when no such clause appears anywhere in the message text. Severity 2 when the block's `Suggested fix` field is described or selectable, so the screen offers a next step somewhere even though the message does not; severity 3 when it is none. | An upload message states only that the upload did not complete, with no instruction in its own text, on a block whose `Suggested fix` field already describes what to do, so the reader has somewhere else on the screen to look. | A form submission reports submission failed with no instruction anywhere in the message and a `Suggested fix` of none, so nothing on the screen tells the reader what to change before trying again. | scripted | Membership of a closed verb list in the message text is a fixed lexical pattern the text either matches or does not, and the severity split reads one further closed-vocabulary field. |
| NNG-EM-EXPLAIN | The message briefly explains why the system behaves this way when that reason would help the reader avoid the same problem again, without expanding into a lecture that outweighs the instruction itself. | Where the message reports a restriction the reader will meet again, a policy, a security rule, or a limit the product itself sets, flag a violation when it states the restriction with no reason attached **and** knowing the reason would change what the reader does next time. A bare format fact that a reader simply complies with (a code is six digits, a date needs a year) is not this criterion's business, and neither is a one-off failure with no rule behind it. Separately, flag a violation when a stated reason takes more sentences than the instruction it supports, so the reader has to read past the explanation to reach what to do. | A password-length error states the requirement without saying why an eight-character minimum exists: a missing but low-stakes explanation the reader can shrug off and just comply with. | An account-lockout message states only that the account is locked, with no explanation of why or how the lockout was triggered, leaving a reader who did nothing unusual with no way to understand or avoid a repeat. | judged | Judging whether an explanation would genuinely help, versus whether it has tipped into an unhelpful lecture, requires reading the message's balance, not counting words against a fixed rule. |
| NNG-EM-GRACE | When a failure is total and the reader has no way to recover in the moment, the message still leaves them with some goodwill, a sincere-sounding acknowledgment or a small human touch, rather than a bare technical notice. | Treat a failure as total and unrecoverable in the moment when all three hold: the block's `Suggested fix` field is none, no other message block under the same screen heading offers a way forward, and the `Message` itself reports a completed loss or an outage the reader cannot act on. Under those conditions, and only those, flag a violation when the message is a bare technical notice with no acknowledgment of the reader's situation anywhere in it. | A scheduled-maintenance page states the service is unavailable with a return time: brief and technical but not cold, and gives the reader something concrete to plan around. | An unrecoverable data-loss notice reads sync failed, changes not saved, with nothing acknowledging what that means for the reader and no avenue offered to ask for help, on the one occasion where the stakes are highest. | judged | Whether wording reads as sincere acknowledgment rather than a rote formula the reader sees through is a tone judgment no fixed phrase list can certify. |
| NNG-EM-NEUTRAL-TONE | The wording stays neutral to encouraging and never frames the problem as something the reader personally did wrong or should have known better than to do. | Scan the `Message` text for a blame phrase from the closed second-person accusatory list `scripts/checks.py` carries as `BLAME_PHRASES`: you failed to, you forgot, your mistake, you should have, you keep, and the rest of that list. Flag a violation on any match, and on no other construction: an accusatory reading that no listed phrase produces belongs to the judged criteria, not to this one. Severity 3 when the blame is paired with a repetition marker (keep, again, repeatedly, every time, still), 2 otherwise. | A form error reads you did not enter a valid email: mildly accusatory phrasing on an otherwise ordinary validation message. | A repeated-failed-login message reads you keep entering the wrong password, framing a routine mistake as a personal failing on a message the reader may see under stress. | scripted | The blame lexicon is a fixed phrase list; matching it against the message text needs no interpretation. |
| NNG-EM-NOT-COLOR-ONLY | The message is signaled by at least one cue beyond color or hue alone, an icon, a text label, a shape change, bold or underline styling, so a reader who cannot distinguish the color still perceives that something needs attention. | Read the `Signal` field's non-color-cue token, the last comma-separated token in that field. Flag a violation when it is none, meaning color or highlight is the only stated cue. Severity 3 when the block's `Container` is a self-clearing toast, because a reader who misses the color cue gets no second chance at the message; severity 2 for `inline` or `modal`, which stay on screen to be read. | A required field is outlined in red with no icon or label change, in an inline container that stays on screen, so a reader who does not perceive the color still has the message itself in front of them. | A validation problem is signaled by color alone in a toast that clears itself after a few seconds, so a colorblind reader gets no cue that anything needs attention and no second chance to notice it. | scripted | The `Signal` field's non-color-cue token is a fixed, closed vocabulary; checking whether it equals none is a direct lookup with no interpretation required. |
| NNG-EM-PLAIN-LANGUAGE | The message is worded in everyday language a reader outside the engineering team would understand, with no internal error code, stack detail, or technical abbreviation standing in for an explanation. | Scan the `Message` text for a fixed jargon pattern: a bare error code, a code-style token, a stack-trace fragment, or a term from a fixed engineering-jargon list. Flag a violation on any match. | A form error reads please correct the highlighted fields, followed by a bracketed internal code: plain language carrying one code a reader can simply ignore. | A checkout failure reads only a raw server status code, with no plain-language sentence anywhere in the message, leaving a non-technical reader nothing to act on. | scripted | The jargon and error-code patterns are a fixed lexicon and a fixed pattern set; the same message text produces the same match on any machine. |
| NNG-EM-PRESERVE-INPUT | A failed submission keeps whatever the reader already entered, so they can correct the specific problem in place rather than re-entering an entire form from a blank state. | Read the `Input on resubmission` field's token. Flag a violation when it is cleared, and only then: preserved is the compliant value, and not-applicable is the annotator stating that no reader-entered input was at stake on this screen at all. Severity 3 when three or more message blocks sit under the same screen heading, the deterministic stand-in for a long form that costs a lot to redo; severity 2 for one or two. | A screen carrying two message blocks clears both fields after a failed submission: a minor inconvenience given how little there was to re-enter. | A screen carrying three or more message blocks, standing in for a long multi-section registration form, clears every field after one failed submission on a single field, forcing the reader to re-enter everything they had already completed. | scripted | The field's token is a fixed, closed vocabulary; checking it against cleared is a direct lookup with no interpretation required. |
| NNG-EM-PREVENT | Where a mistake is common and foreseeable, the system warns before the reader commits it, rather than only reporting it afterward. | Where the `Predictable mistake` field is yes and the `Fires` field is on-submit, with nothing earlier in the flow warning the reader, decide whether this particular mistake is one the product could plausibly have caught during entry rather than at commitment: a format, a length, or a limit the product already knows, rather than a fact only the server can settle when the form is sent. Flag a violation only where it could have. The annotation field states that the mistake is common; it does not settle whether a pre-emptive warning was available, which is the judgment this criterion turns on. | A password field accepts a common but weak pattern with no warning until after the reader submits the whole form: a foreseeable miss caught only on the reader's second attempt. | A payment form accepts an obviously malformed card number with no warning during entry, and reports the failure only after the reader has completed and submitted the entire multi-step checkout flow. | judged | Whether a given mistake is common and foreseeable enough to warrant a pre-emptive warning is a judgment call about the mistake itself, not a fixed property the fields alone settle. |
| NNG-EM-PROXIMITY | A message appears directly beside the control or field it concerns, on the same screen and within the same view, so a reader can connect message to cause without searching elsewhere on the page or navigating away. | Using the `Placement` field, flag a violation when the message sits on a different screen, in a separate log, or at a page location requiring scrolling or navigation away from the control it concerns, rather than immediately beside or below that control. | A field-level validation message appears at the top of a long form instead of beside the field it concerns, but the field itself is still visible on screen, so the reader can find it by scanning upward. | A required-field error is reported only in a separate error-summary screen reached by leaving the form, so the reader loses sight of the field entirely and must navigate back and forth to reconcile the two. | judged | Whether a stated placement counts as close enough to the control is a spatial-relationship judgment the `Placement` field's free text cannot reduce to a fixed pattern. |
| NNG-EM-SALIENT | The message and the element carrying it are visually prominent enough, through size, contrast, weight, or position, that a reader scanning the screen at normal reading speed notices them without hunting. | Using the `Signal` field's visual-weight description, flag a violation when the message is described as indistinguishable from surrounding body text, same size, same weight, no highlight, at the point a reader would first encounter the screen. | An inline field error uses the same font weight as the surrounding labels; only a color change sets it apart, so an attentive reader still catches it on a normal pass. | A form-submission failure is reported in a banner styled identically to informational banners elsewhere on the same page, so a reader has no visual cue that this one demands action. | judged | Sufficiency of visual weight is a design judgment about the whole screen, not a property a fixed keyword or pattern can certify. |
| NNG-EM-SELECTABLE-FIX | Where the correct fix is unambiguous, the message offers it as something the reader can pick directly, rather than only describing it in words and leaving the reader to re-type or re-navigate to apply it themselves. | Where the `Suggested fix` field's token is described rather than selectable, and the described fix names a single, unambiguous option, flag a violation: an unambiguous single fix described in prose but not offered as a selectable action. | A duplicate-username message names the exact suggested alternative in its text but requires the reader to manually type that suggestion into the field themselves. | A file-type error names the one accepted format and could offer a one-click convert-and-retry action, but instead only tells the reader to convert the file themselves outside the product and re-upload it. | judged | Deciding whether a described fix is genuinely unambiguous enough to deserve a selectable affordance, rather than one option among several reasonable ones, requires weighing the situation, not a fixed lookup. |
| NNG-EM-SEVERITY-CONTAINER | The presentation container, an inline note beside a field, a toast that appears and clears on its own, or a modal dialog that halts the flow, matches how much the underlying problem actually blocks the reader from continuing. | Compare the `Container` field against the blocking severity implied by the rest of the screen context, whether the reader can proceed without resolving it. Flag a violation when a fully blocking failure uses a self-clearing toast, or a minor, recoverable issue uses a flow-halting modal. | A non-blocking autosave failure that the reader can safely retry later is shown as a modal dialog the reader must dismiss before continuing: more interruption than the problem warrants. | A payment failure that prevents order completion is shown as a toast that clears itself after a few seconds, so a reader who looks away misses the one message explaining why checkout will not proceed. | judged | Deciding whether a container choice matches the problem's actual blocking severity means weighing the situation as a whole, not matching a fixed value. |
| NNG-EM-SPECIFIC | The message names the actual problem, which field, which rule, which item, rather than a generic statement that could describe any failure in the same spot. | Read the `Message` text. Flag a violation when it names no field, value, or rule, a bare something-went-wrong statement with nothing else added, where the screen context shows a specific, nameable cause was available. | A multi-field form reports that a field is required without naming which of several required fields is empty, when only one field is actually unfilled. | A file-upload failure reads upload failed with no named reason, when the actual cause, file too large, wrong file type, or a network error, was available to state. | judged | Deciding whether a message names the real cause, rather than a plausible-sounding but still generic restatement, requires reading the message against its situation. |
| NNG-EM-TIMING | The message appears only once the reader has had a fair chance to finish entering information, not while they are still typing and not before they have entered anything at all. | Read the `Fires` field's token. Flag a violation when that token is mid-keystroke or on-load-before-input, meaning the message can appear before the reader has had a chance to complete the relevant input. | A password-strength note updates on every keystroke but stays informational rather than an error, so it is premature without blocking or alarming the reader. | An email-format error appears mid-keystroke, before the reader has finished typing the address, so the reader is told they are wrong before they could possibly be right. | scripted | The `Fires` field's token is a fixed, closed vocabulary; checking membership in the disallowed set is a direct lookup with no interpretation required. |

## Lane split

Six scripted, eight judged. This is the mixed split
[S-05 (skills slate)](../../../docs/internal/release-plans/plan_v0.1.0/S-05_skills-slate/spec.md)
expects for this skill, constructive-tone lexical checks scripted and helpfulness judged, extended to
cover the annotation-field checks the artifact format in [ADR 0018](../../../docs/internal/decisions/0018-microcopy-artifact-format-annotated-context.md)
makes possible:

- **Scripted (6):** `NNG-EM-CONSTRUCTIVE`, `NNG-EM-NEUTRAL-TONE`, `NNG-EM-NOT-COLOR-ONLY`,
  `NNG-EM-PLAIN-LANGUAGE`, `NNG-EM-PRESERVE-INPUT`, `NNG-EM-TIMING`. Three of these,
  `NNG-EM-CONSTRUCTIVE`, `NNG-EM-NEUTRAL-TONE`, `NNG-EM-PLAIN-LANGUAGE`, are lexical checks on the
  `Message` text itself, the tone and jargon patterns the skill parameters name directly. The other
  three, `NNG-EM-NOT-COLOR-ONLY`, `NNG-EM-PRESERVE-INPUT`, `NNG-EM-TIMING`, are fixed-token lookups on
  a single annotation field, deterministic for the same reason, no interpretation of the token is
  required, but only possible because the artifact format carries that field at all.
- **Judged (8):** `NNG-EM-EXPLAIN`, `NNG-EM-GRACE`, `NNG-EM-PREVENT`, `NNG-EM-PROXIMITY`,
  `NNG-EM-SALIENT`, `NNG-EM-SELECTABLE-FIX`, `NNG-EM-SEVERITY-CONTAINER`, `NNG-EM-SPECIFIC`. Each
  requires weighing the message or the screen context as a whole, whether a cause is really named,
  whether a container matches a severity, whether an explanation helps rather than lectures, rather
  than matching a fixed pattern.

No criterion sits in both lanes. Reading a scripted result as a verdict on how helpful a message is
overstates what it checks: `NNG-EM-PLAIN-LANGUAGE` firing clean does not mean the message names the
right problem, that is `NNG-EM-SPECIFIC`'s judged question, and `NNG-EM-TIMING` firing clean does not
mean the container matches the failure's severity, that is `NNG-EM-SEVERITY-CONTAINER`'s judged
question.

## See also

- [`docs/internal/skill-template.md`](../../../docs/internal/skill-template.md), "Criterion tables",
  the seven-column format this file implements.
- [`docs/reference/criterion-ids.md`](../../../docs/reference/criterion-ids.md), the ID grammar and
  the namespace registry entry explaining the shared `NNG` letter.
- [`docs/reference/severity-scale.md`](../../../docs/reference/severity-scale.md), "Microcopy
  (critique-microcopy)", the pre-existing domain anchors this file's per-criterion anchors calibrate
  against, not this skill's own authoritative registry.
- [ADR 0006 (copyright paraphrase policy)](../../../docs/internal/decisions/0006-copyright-paraphrase-policy.md),
  why every operationalization above is original wording rather than source text.
- [ADR 0018 (microcopy artifact format)](../../../docs/internal/decisions/0018-microcopy-artifact-format-annotated-context.md),
  why the registry can check all 14 criteria rather than 6, and the exact annotation grammar.
- [`docs/internal/release-plans/plan_v0.1.0/S-05_skills-slate/spec.md`](../../../docs/internal/release-plans/plan_v0.1.0/S-05_skills-slate/spec.md),
  AC-2 (the eight-criteria floor this registry clears at 14) and OQ-2 (resolved by ADR 0018).

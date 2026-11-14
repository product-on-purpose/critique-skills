# TOULMIN rubric source

The criterion registry for `critique-argument`. Every row below operationalizes one part of the
Toulmin model of argument, in this library's own wording, and no source text is reproduced
([ADR 0006 (copyright paraphrase policy)](../../../docs/internal/decisions/0006-copyright-paraphrase-policy.md),
[methodology section 11](../../../docs/explanation/methodology.md)).

## Source

- **`rubric_sources.id`:** `TOULMIN`
- **Citation:** Toulmin, S. E. (2003). *The Uses of Argument*, updated edition. Cambridge University
  Press. ISBN 978-0521534333, ch. 3, The Layout of Arguments.
- **`url`:** `null` (a book has no stable canonical URL; the ISBN is the citable identifier, per
  [`docs/internal/skill-template.md`](../../../docs/internal/skill-template.md), `rubric_sources`).
- **`accessed`:** 2026-07-31
- **`operationalization`:** `paraphrased`

The book was first published in 1958; the 2003 updated edition is cited because its chapter numbering
is the one most secondary discussion of the model references. Chapter 3 is where the six-part schema
(claim, data or grounds, warrant, backing, qualifier, rebuttal) is laid out, and all eight criteria
below trace to it. Every row's rubric source is `TOULMIN`; the column contract's source citation is
carried by this section rather than repeated in each cell.

## Registry

Eight criteria: the six Toulmin elements, each judged, plus the two scripted assists
[S-05 (skills slate)](../../../docs/internal/release-plans/plan_v0.1.0/S-05_skills-slate/spec.md)
names for this skill (claim-marker detection, hedging density), each carrying its own permanent ID
rather than being folded into an element criterion. Why the two assists are separate IDs and not a
second lane on an existing criterion is
[ADR 0017 (argument lane split)](../../../docs/internal/decisions/0017-argument-lane-split-scripted-assists-as-criteria.md).

Rows are in ascending ID order, which is also the order `SKILL.md`'s pass 2 sweeps them in.

### The target reader

Three rows below (`TOULMIN-BACKING`, `TOULMIN-REBUTTAL`, `TOULMIN-WARRANT`) turn on what a reader
already grants without being told. That reader is one construct, defined once here so two reviewers
sweeping the same artifact answer the same question rather than each imagining their own audience.

**The target reader** is the audience the artifact itself names or addresses: a memo addressed to a
board, a proposal whose opening states who approves it, an op-ed written for a general readership.
Where the artifact names no audience, and most do not, the default is a competent non-specialist
from outside the author's organization and discipline, reading the artifact cold. The default is
deliberately the harder reader: a criterion that lets a sweep imagine a maximally informed audience
never fires, and an argument that only persuades people who already agree has not been tested.

Two consequences the rows depend on:

- Common ground is what the target reader would supply unprompted, not what the author treats as
  obvious. An author's confidence in a principle is not evidence about the reader.
- A stated audience narrows the reader and never widens the artifact's scope. A document that names
  its audience as the compliance team is swept against a compliance reader, so a principle that team
  genuinely holds needs no backing; a document that names nobody is swept against the default, not
  against whichever reader would be most sympathetic to it.

| ID | Operationalization | Operational test | Severity 2 anchor | Severity 3 anchor | Lane | Lane rationale |
|---|---|---|---|---|---|---|
| TOULMIN-BACKING | A general principle the argument relies on, where the target reader defined above would not grant it on sight, is itself supported: the study, standard, regulation, precedent, or documented body of practice that establishes it is named. A contestable principle is not presented as self-evident. | For each general principle the artifact advances, whether it states the principle outright or leans on it implicitly, ask whether the target reader would accept it without further support. Flag a violation when that reader would not and the artifact offers nothing beyond restating the principle more forcefully or asserting that everyone already knows it. A principle the target reader would grant unprompted is not a violation. Where the artifact advances no general principle anywhere, the gap belongs to TOULMIN-WARRANT and this criterion reports nothing separately; backing is only assessable against a principle the artifact actually puts forward. | A market-sizing memo leans on an industry rule of thumb about conversion rates that is plausible but never sourced, weakening one of its four supporting points while the rest stay checkable. | A policy proposal's entire case rests on the principle that a named intervention lowers incident rates, offered with no study, no internal data, and no precedent, so a reader who does not already hold that belief has nothing to test the proposal against. | judged | Whether a principle needs backing depends on what the artifact's stated audience already grants, which no fixed pattern can determine. |
| TOULMIN-CLAIM | The artifact states one central conclusion it asks the reader to accept, specific enough that a reader could disagree with it, and states it outright rather than leaving it to be inferred from the surrounding discussion. | During this criterion's own turn in the pass-2 sweep, write the artifact's conclusion as a single sentence using only wording the artifact supplies. Flag a violation when that sentence cannot be assembled: no passage states a conclusion, several passages state conclusions that do not reduce to one, or the stated conclusion is so general (improve things, optimize the process) that no reader could disagree with it. Where the artifact states its conclusion more than once, assemble from the passage the artifact itself presents as its specification of the ask; a conclusion stated crisply in one place and dissolved into a vacuous restatement in another is a violation on the same terms, because a reader cannot tell which version is the ask. | A proposal states its recommendation crisply in the executive summary, then restates it in the closing section as a vaguer aspiration, so a reader who reads only the ending cannot tell which version is the ask. | A five-page position document surveys four options at length and never says which one it recommends, so a reader finishes it unable to state what they are being asked to accept. | judged | Deciding whether a stated sentence is genuinely the conclusion the rest of the artifact supports requires reading the artifact as a whole. |
| TOULMIN-CLAIM-MARKER | The artifact carries at least one explicit conclusion-signalling phrase, so a reader scanning rather than reading straight through can locate where the conclusion is asserted instead of reconstructing it from context. | Count occurrences of a fixed conclusion-marker lexicon (therefore, thus, hence, it follows that, we recommend, this paper argues, I argue that, the conclusion is, in conclusion, we should, the case for). Flag one document-level violation when the count across the whole artifact is zero. Severity 2 when the artifact is under 300 words, severity 3 at 300 words or more, where a word is a whitespace-separated token carrying at least one letter or digit, counted over heading and paragraph text; a bare markdown token such as a list bullet or a table pipe is not a word. A marker being present is not evidence the conclusion is well formed; TOULMIN-CLAIM decides that separately. | A memo of roughly 200 words carries no conclusion marker, but a reader who starts at the top reaches the ask within a few lines, so the missing signpost costs little. | A 1,200-word position document carries no conclusion marker anywhere, so a reader scanning for the ask has no anchor and must read the whole artifact to discover what is being argued. | scripted | A closed lexicon match plus a word count; the same artifact yields the same counts on any machine and no judgment enters the detection. |
| TOULMIN-GROUNDS | Each claim the argument advances is attached to evidence a reader could check: data, documented observation, cited authority, or a worked example, rather than assertion, restatement, or an appeal to how obvious the point is. | For the central claim and each supporting claim, locate the passage offering evidence for it. Flag a violation when a claim carries no evidence, or when what is offered restates the claim in different words instead of supporting it. Evidence a reader could in principle verify counts even if the artifact does not verify it; unverifiable assertion does not. | One of a proposal's four supporting points cites a figure with no source while the other three are sourced, so a reader can still check most of the case. | A recommendation memo supports its central claim only by restating it in progressively stronger language across three paragraphs, so a reader who is not already persuaded is given nothing to examine. | judged | Telling support from restatement requires reading claim and evidence together and weighing the relationship between them. |
| TOULMIN-HEDGE-DENSITY | Hedging is concentrated rather than uniform: a document carrying a qualifying term in most of its sentences gives a reader no way to tell which of its claims its author stands behind and which are being floated. This criterion measures that distribution over the whole artifact and nothing else; whether any individual hedge is the right call for the evidence behind it is TOULMIN-QUALIFIER, not this row. | Count sentences containing at least one term from a fixed hedging lexicon (may, might, could, possibly, perhaps, arguably, somewhat, relatively, it seems, appears to, tends to, to a degree) and divide by total sentence count, both taken over paragraph text only, since a heading is not a sentence. Flag one document-level violation when the ratio exceeds 0.35. Severity 2 while the ratio stays at or below 0.50, severity 3 above it. The finding reports a distribution and never a verdict: a sweep must not raise, lower, or withhold a TOULMIN-QUALIFIER finding on the strength of this ratio. | Roughly two in five of a position paper's sentences carry a hedge, so a reader meets a qualification every few sentences while most statements are still made plainly. | More than half of an artifact's sentences carry a hedge, so a reader has no way anywhere in the document to separate the positions its author holds from the ones being floated. | scripted | A lexicon match and an arithmetic ratio over the whole artifact; both operands are counted rather than judged. |
| TOULMIN-QUALIFIER | The strength with which the central claim is asserted matches the strength of the grounds behind it: a claim resting on partial or contested evidence carries a limiting term, and a claim resting on solid evidence is not weakened by a qualification its evidence does not call for. | Compare the modal force of the claim as stated (must, will, always, certainly against may, often, in most cases) with what the grounds identified under TOULMIN-GROUNDS actually establish. Flag a violation in either direction: an unqualified claim on grounds that support only a qualified one, or a claim hedged well below what its own grounds support. A claim whose stated strength matches its grounds is not a violation whichever way it leans. The two directions do not calibrate alike, and the anchors in this row cover overreach only: a reader acting on an overstated claim is acting on evidence that is not there, while a reader who discounts a well-supported claim can recover it by reading the grounds, so an under-claiming finding caps at severity 2. | A supporting point is asserted as always holding where its cited data covers a single quarter, an overreach on one point in an otherwise calibrated document. | A proposal's central recommendation is stated as a certainty on the strength of one internal pilot, so a decision-maker acting on it gets no signal that the result might not generalize. | judged | Matching asserted strength to what the evidence supports means weighing the grounds, which counting hedge words cannot stand in for. |
| TOULMIN-REBUTTAL | The argument names the circumstances that would set its claim aside, the exceptions under which its grounds would stop supporting its conclusion, and addresses them, rather than presenting the claim as though no condition could defeat it. | Working only from what the artifact supplies, name the conditions its own grounds leave open: the scope the evidence does not reach, the cost or risk the recommendation creates, and the alternative the grounds do not rule out. Flag a violation when the artifact raises none of them, or when it raises one and then moves on without answering it. Where the artifact does raise an objection, judge it against the ones its own grounds expose rather than against outside knowledge of the subject: answering an objection its evidence already covered while never touching one its own scope leaves open is a violation, and failing to anticipate an objection nothing in the artifact points to is not. | A proposal answers the cost objection but never raises the sequencing objection a reviewer would come to second, leaving one of two foreseeable challenges unaddressed. | An essay advancing a contested claim raises no counterargument at all and answers none, so the first question a skeptical reader asks is one the argument has not prepared for. | judged | Recovering the conditions an artifact's own grounds leave open, and telling an answered objection from an abandoned one, means reading claim, grounds, and scope against each other rather than matching a pattern. |
| TOULMIN-WARRANT | The argument makes explicit the general principle that licenses moving from its grounds to its claim, so a reader who accepts the evidence can see why that evidence bears on this conclusion rather than some other one. | For the central claim and its grounds, state the general principle that would have to hold for those grounds to support that claim. Flag a violation when the artifact never states that principle and it is not common ground the target reader would supply unprompted, or when the principle the artifact does state would license a different conclusion than the one drawn. | A memo leaves the connecting principle implicit on one supporting step while stating it on the others, a gap a careful reader can bridge from surrounding context. | A recommendation memo argues for one option using grounds that establish only a fact about a different option, never stating the principle connecting the two, so a skeptical reader cannot reconstruct why the conclusion follows. | judged | Recovering an unstated general principle and testing whether it licenses this particular conclusion is inference over the whole argument, not a surface feature. |

## Lane split

Six judged, two scripted. The split follows
[S-05 (skills slate)](../../../docs/internal/release-plans/plan_v0.1.0/S-05_skills-slate/spec.md)'s
expectation for this skill (judged-heavy, with claim-marker detection and hedging density as the
scripted assists) and the skill template's scripted-lane discipline: a criterion belongs in the
scripted lane only when a deterministic script decides it with no judgment call.

None of Toulmin's six elements qualifies. Whether a passage is the claim, whether evidence supports
rather than restates, whether an unstated principle is common ground for this audience: each needs the
argument read as a whole. The two scripted criteria are deliberately narrower than the elements they
sit next to, and neither substitutes for one:

- `TOULMIN-CLAIM-MARKER` firing does not mean the claim is missing, and staying silent does not mean
  the claim is good. It reports one measurable property, whether the conclusion is signposted.
- `TOULMIN-HEDGE-DENSITY` reports a distribution over the artifact. It says nothing about whether any
  individual claim is qualified correctly, which is `TOULMIN-QUALIFIER`'s judged question.

Reading either scripted result as a verdict on the element criterion beside it is the specific
misreading [ADR 0017 (argument lane split)](../../../docs/internal/decisions/0017-argument-lane-split-scripted-assists-as-criteria.md)
exists to prevent.

## Thresholds

Two numbers in the table above are v0.1 defaults, not measured values: the hedged-sentence ratio
bands (0.35 and 0.50) and the claim-marker word-count boundary (300 words). Both are set so the
scripted lane is deterministic and reproducible, which is the property the library claims for it;
neither is calibrated against the corpus yet. P3 measurement is where they get their first evidence,
and moving a threshold there is a revision to this file, not a contract change.

## See also

- [`docs/reference/criterion-ids.md`](../../../docs/reference/criterion-ids.md) - the ID grammar and
  the namespace registry that assigns `TOULMIN` to this skill.
- [`docs/reference/severity-scale.md`](../../../docs/reference/severity-scale.md) - the shared 0-4
  scale the anchors above calibrate against, including its own Argument domain anchors.
- [`references/severity-anchors.md`](severity-anchors.md) - this skill's additional domain
  calibration, beyond the per-criterion anchors above.
- [ADR 0006 (copyright paraphrase policy)](../../../docs/internal/decisions/0006-copyright-paraphrase-policy.md) -
  why every operationalization above is original wording rather than source text.
- [ADR 0017 (argument lane split)](../../../docs/internal/decisions/0017-argument-lane-split-scripted-assists-as-criteria.md) -
  why the registry has eight criteria rather than six.

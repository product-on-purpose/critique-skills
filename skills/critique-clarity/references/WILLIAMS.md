# WILLIAMS rubric source - criterion registry

**Status:** Operationalized. Every criterion below carries a paraphrased operationalization, an
operational test, severity 2 and 3 anchors, and a lane assignment with rationale, per
`docs/internal/skill-template.md`'s seven-column format. Zero quotation marks appear in the
Operationalization column, and no source text is reproduced, per the paraphrase policy
([ADR 0006](../../../docs/internal/decisions/0006-copyright-paraphrase-policy.md)): this is copyrighted
material (`rubric_sources.operationalization: paraphrased`), so every operationalization is this
skill's own original wording, not a quotation. Cross-criterion severity calibration lives in
[`severity-anchors.md`](severity-anchors.md); the two scripted rows below name the actual constants
`scripts/checks.py` implements, for the same reason every scripted row in `PLAIN.md` does.

**Source:** Williams, J. M., & Bizup, J. (2016). *Style: Lessons in Clarity and Grace* (12th ed.).
Pearson. ISBN 978-0-13-408041-3 (ISBN-10 0134080416). No stable canonical URL; `rubric_sources.url` is
`null` for this source. Chapter numbers and titles below were verified against the 12th edition's
published table of contents. An earlier, Williams-solo-authored 11th edition (2014) also circulates;
the 12th edition (Williams & Bizup) is cited here because its chapter numbering was the one directly
verified during research. Two of the eight chapters this skill draws on, ch. 3 ("Actions") and ch. 9
("Concision"), are operationalized in `PLAIN.md` rather than here; see "Resolution of S-05 OQ-1" below.

## Registry

| ID | Operationalization | Operational test | Severity 2 anchor | Severity 3 anchor | Lane | Lane rationale |
|---|---|---|---|---|---|---|
| WILLIAMS-CHARACTER-ACTION | A sentence's grammatical subject names the real-world actor performing the sentence's action, rather than an abstraction, a process, or a condition standing in for that actor, even when the sentence is already grammatically active (WILLIAMS ch. 4). | Flag a sentence as a violation when its grammatical subject is an abstract noun, such as a decision, a process, or a determination, that stands in for an identifiable person or organization who could instead be named as the subject, regardless of whether the verb itself is active or passive. | One sentence in an otherwise character-driven paragraph names an abstract decision as its subject instead of the committee that made it, a single abstract-subject lapse. | A five-sentence explanation of a policy change never once names the people who made it, instead running every sentence through an abstraction such as the process or the determination as subject, so a reader cannot tell who is actually responsible for anything described. | judged | Deciding whether a subject genuinely stands in for a real actor, as opposed to legitimately naming a concept, requires reading the sentence's meaning; this is a broader semantic test than PLAIN-ACTIVE's grammatical passive-voice pattern and is not reducible to a fixed part-of-speech rule. |
| WILLIAMS-COHESION | Each sentence in a passage opens with information the reader already has, from the sentence before it or from shared context, before introducing new information, and successive sentences' subjects track the same running topic rather than jumping between unrelated ones (WILLIAMS ch. 5). | Flag a passage as a violation when a sentence opens with wholly new information the prior sentence gave the reader no basis for, or when consecutive sentences' subjects shift topic with no signal connecting the new subject back to what came before. | One sentence in an otherwise cohesive paragraph opens with a new proper noun the prior sentence never mentioned, a brief disruption the reader recovers from within the sentence. | A four-sentence paragraph changes its subject in every sentence, with no sentence picking up the topic the one before it just established, so the reader has to re-orient at every sentence boundary. | judged | Judging whether a sentence's opening information is genuinely already known to the reader, and whether a subject shift breaks the topic thread, requires reading the passage as connected discourse. |
| WILLIAMS-COHERENCE | Across a passage or section, a reader is able to name a consistent, limited set of themes the whole passage is about, rather than being able to follow only each sentence in isolation with no larger throughline (WILLIAMS ch. 8). | Flag a section as a violation when a reader who has read only its first and last sentences cannot state what the section as a whole was about, or when the section's sentences pursue three or more unrelated themes with no signal connecting them. | One section covers two related sub-themes with only a light signal connecting them, still recoverable as a coherent unit on a careful read. | A section titled Requirements moves through eligibility, an unrelated history of the program, and a tangential staffing note with nothing connecting the three, so a reader finishing the section could not state what it was actually about. | judged | Naming a passage's themes and judging whether they cohere into a limited, consistent set requires reading and synthesizing the whole passage, not a local pattern. |
| WILLIAMS-STRESS | The newest, most complex, or most important information in a sentence lands at its end, the position a reader weighs most heavily, rather than in the middle where it gets passed over (WILLIAMS ch. 6). | Name the sentence's newest element first: the one piece of content the preceding sentence and the surrounding section have not already given the reader. Flag the sentence when that element is followed, before the sentence ends, by material the reader already had or by a detail the section never returns to, so the final position is occupied by something other than the new element. Record the named element in the finding's evidence, so a second reviewer can agree or disagree with the identification rather than with a verdict. | One sentence buries a secondary detail at its end instead of its most important point, a minor ordering choice that does not obscure the sentence's meaning. | A sentence stating a filing deadline opens with the deadline itself, buries the one exception that changes it in the middle, and ends on an unrelated contact-information clause, so the reader's attention lands on the least important part of the sentence. | judged | Judging which piece of a sentence's content is newest or most important, and whether it lands at the end, requires reading the sentence's meaning against its surrounding context. |
| WILLIAMS-SHAPE | A long sentence is built so a reader can hold its main clause in mind while working through subordinate clauses and modifiers, rather than stacking interruptions between the sentence's own subject and verb (WILLIAMS ch. 10). | Flag a sentence of 40 words or more that also carries either two or more comma-set-off asides after a subject candidate of eight words or fewer, or two or more subordinate-clause markers from the same fixed list PLAIN-SENTENCE-LENGTH uses. Severity is 3 at 60 words or more, and 2 otherwise. A sentence whose commas form a coordinated series of three or more items belongs to PLAIN-LISTS and is not flagged here. A sentence of 40 or more words with only one aside and one marker is not a violation of this criterion; length alone is PLAIN-SENTENCE-LENGTH's concern, and this criterion is about the pile-up. | A forty-five-word sentence carries two comma-set-off asides between its subject and its verb, interrupted but still followable on one pass. | A sentence of well over sixty words stacks three separate subordinate clauses between its subject and its main verb, each set off by commas, so the reader has lost track of the subject by the time the verb finally arrives. | scripted | Sentence-length threshold combined with a count of subordinate-clause markers between subject and verb is a fixed, reproducible measurement, extending the same heuristic PLAIN-SUBJECT-VERB-OBJECT uses at a longer-sentence threshold. |
| WILLIAMS-PARALLELISM | Elements joined by a coordinator or presented as a series share the same grammatical form, so the reader processes them as one structural pattern rather than as unrelated fragments (WILLIAMS ch. 11). | Split the sentence into its coordinated series exactly as PLAIN-LISTS does, then classify each item's head word into one of three classes: infinitive (to followed by another word), gerund (a lowercase word ending in -ing), or other. The first item's head is read after any list-introducing verb such as covers, includes, requires, involves, lists, comprises, or needs, since that item still carries the clause that introduces the series. Flag a series of two or more items whose head words fall into two or more classes. Severity is 3 when the series has four or more items falling into three or more classes, and 2 otherwise. | A two-item series pairs a gerund with a noun phrase instead of two gerunds, a small mismatch in an otherwise parallel document. | A four-item requirements list mixes an infinitive, a gerund, a bare noun, and a full clause as its four items, so the reader has to re-parse the grammatical form of each item individually instead of reading the series as one pattern. | scripted | Comparing the part-of-speech form of each coordinated item's head word against a fixed tag set is a direct, reproducible pattern match. |

**6 criteria** shipping under the WILLIAMS namespace. Two additional Williams chapters this skill draws
on, ch. 3 ("Actions") and ch. 9 ("Concision"), are operationalized as well, but their surviving IDs are
PLAIN-NOMINALIZATION and PLAIN-CONCISE in `PLAIN.md`, per
[ADR 0019](../../../docs/internal/decisions/0019-clarity-two-namespaces-merged-duplicate-criteria.md).
Williams' own criterion count this skill draws on is therefore 8, of which 6 ship as WILLIAMS-* IDs.

Lane split within this file: 2 scripted, 4 judged.

## Chapters surveyed and not carried forward

Ch. 1 ("Understanding Style") and ch. 2 ("Correctness") are framing and grammar-correctness material,
not independently checkable clarity criteria in their own right; ch. 2 in particular concerns usage
controversies (e.g., "which" versus "that") that are a different, narrower rubric than this skill's
clarity claim. Ch. 7 ("Motivation") was surveyed and left out as a standalone ID: its guidance, that a
passage should give the reader a reason to keep reading before piling on technical detail, substantially
overlaps PLAIN-ORGANIZE and PLAIN-MAIN-IDEA-FIRST on the PLAIN side. Ch. 12 ("The Ethics of Style") is a
normative essay on the ethics of clear writing, not a criterion a finding could cite against a specific
passage.

## Resolution of S-05 OQ-1

[ADR 0019](../../../docs/internal/decisions/0019-clarity-two-namespaces-merged-duplicate-criteria.md)
resolves S-05 (skills-slate spec) OQ-1: this skill keeps two namespaces, PLAIN and WILLIAMS, rather than
folding every WILLIAMS-* criterion into PLAIN-*. The six rows above (character-as-subject, cohesion,
coherence, stress, sentence shape, parallelism) have no PLAIN equivalent and would be misattributed to
an open-standard source if renamed into it, so they keep the WILLIAMS namespace and citation. The two
pairs that tested the literal same construction across both sources, nominalization and concision,
merge into one ID each rather than shipping as two: PLAIN-NOMINALIZATION and PLAIN-CONCISE in
`PLAIN.md`, which is why WILLIAMS-NOMINALIZATION and WILLIAMS-CONCISION do not appear as rows in this
file. Neither was ever published as an ID, so no deprecation entry applies (criterion-ids.md's
"deprecate, never delete" rule governs IDs already shipped, not draft candidates resolved within the
same operationalization pass).

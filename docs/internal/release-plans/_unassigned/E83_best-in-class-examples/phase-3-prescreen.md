---
id: E83
title: "E83 phases 3 and 3b: flagship candidates and the free scripted pre-screen"
type: record
created: 2026-11-16
linked-plan: plan.md
---

# E83 phases 3 and 3b: flagship candidates and the free pre-screen

This record covers the plan's phase 3 (choose one realistic artifact per skill) and phase 3b (run
each skill's scripted lane on its candidate, free, and read every finding for misfires). No model
was called. The pre-screen found four scripted-lane defects, filed below as E84 to E86, plus new
evidence for E82. Following the plan's rule, a misfire becomes a backlog item, not a reason to swap
the artifact. The microcopy candidate is still open, but for a different reason: that document is
outside the skill's artifact claim.

## The candidates

Decision D2 ruled that a flagship artifact comes from a sibling library when one produces that
artifact type. Six skills have a sibling source. Both source repositories are public and licensed
Apache-2.0, the same licence as this repository. Every hash below is of the file's bytes at the
named tag, so phase 4 can extract exactly the same input.

| Skill | Source (repository, tag, path) | Lines | sha256 of the bytes at the tag |
|---|---|---|---|
| `critique-accessibility` | pm-skills `v2.35.1`, `library/skill-output-samples/foundation-lean-canvas/sample_foundation-lean-canvas_brainshelf_resurface.html` | 376 | `7997d5118e20293faa63b20cd615964a02dec98d1743f6dbcf6d92e969862a78` |
| `critique-argument` | pm-skills `v2.35.1`, `library/skill-output-samples/develop-adr/sample_develop-adr_workbench_blueprints.md` | 119 | `e78f4f835ae958962e9f0b4b39a137c8c3d110592f2b0290598932c7d6feb9db` |
| `critique-clarity` | pm-skills `v2.35.1`, `library/skill-output-samples/foundation-stakeholder-update/sample_foundation-stakeholder-update_brainshelf_resurface-email-beta-users.md`, lines 68 to 92 (the "Shareable update" email, without the sample's wrapper) | 25 of 139 | whole file: `727514a79eb1eeac20275777d68e8babf7abc13bcb7ef654b73d0b609c11c916` |
| `critique-docs` | pm-skills `v2.35.1`, `site/src/content/docs/getting-started/quickstart.md` | 139 | `d0468d709d77c1bf5c15e0fbbd03b61834a4995b17cf4dcac4384565220d4061` |
| `critique-forms` | writing-style-catalog `v0.15.0`, `docs/internal/ui-mockups/04-brand-voice-builder.html` | 936 | `0aac9d6063bbf49a287f3624df11522623ea2dc359dc6609b3b2428d2a1cf350` |
| `critique-microcopy` | **Open.** The pre-screened candidate was pm-skills `v2.35.1`, `library/skill-output-samples/deliver-edge-cases/sample_deliver-edge-cases_storevine_campaigns.md` (200 lines, `ab1fa9aab1764474f856910e0c2db548eeace3bfa1947995367909607aaaa7ab`) | | |
| `critique-usability` | writing-style-catalog `v0.15.0`, `docs/internal/ui-mockups/01-composer.html` | 594 | `4fe99169b83480876c66e4fedd608a28cbacdfe553a7d3b08b07ef9c72ec906c` |

**The clarity extract.** E54 took only its PRD's Output section. For the same reason, the clarity
flagship takes only the email that the stakeholder-update sample produces. The sample wraps its
output in a fenced code block that also holds YAML metadata and the sample's internal notes, and no
reader would send those as the document. The extract is 25 lines, which is a realistic length for
an email. Phase 4 records the extract's own hash, as E54 did, because it is a new file.

**Two notes on the sources.**

- pm-skills labels its samples as written worked examples, not transcripts of real runs, and the
  E54 recipe already says so. The flagship walkthroughs will say the same.
- The writing-style-catalog mockups are internal design mockups. Their repository is public and
  licensed Apache-2.0, so copying them here is permitted, but they are design drafts, not a shipped
  product's pages.

## What the scripted lane found

Each command was `python skills/critique-<domain>/scripts/checks.py --repo-root <dir> <file>`, run
on 2026-11-16 from this repository's root at `110225d`.

| Skill | Found | At severity 3 | What the findings are |
|---|---|---|---|
| accessibility | 9 | 9 | Every one is WCAG-1.4.3 on a confidence badge, with false evidence (E85) |
| argument | 1 | 1 | TOULMIN-CLAIM-MARKER: no conclusion-marker phrase in 1381 words. The ADR states its claim under `## Decision` as an imperative ("Adopt Yjs..."), which the lexicon does not include. This is the lexicon's documented limitation, not a parser fault, and the judged lane should weigh it |
| clarity (email extract) | 15 | 11 | 10 of the 11 at severity 3 are PLAIN-TRANSITIONS on a salutation, three bold labels, list items and a sign-off (E82) |
| clarity (whole sample, for comparison) | 34 shown, 6 suppressed | 29 | It reads the YAML metadata inside the code fence and treats each `---` rule as a paragraph (E82). The run first crashed on Windows (E84) |
| docs | 0 | 0 | The page declares no `mode:`, so DIATAXIS-MODE is silent by design, and no other scripted criterion fired |
| forms | 0 | 0 | Five labelled text inputs, two textareas and three buttons, none of a kind the scripted criteria test |
| microcopy | 37 | 32 | 31 are NNG-EM-CONSTRUCTIVE on headings, document lists, a code fence and a table row, none of which is a message (E86) |
| usability | 0 | 0 | The mockup does not use the `<section id=...>` state convention, so the dead-end sweep has nothing to read, which is by design. Every control is labelled |

## Defects found

Each defect below was reproduced with no model call. The two lane defects were confirmed on a
minimal file of a few lines.

- **E84 (scripted lanes crash on Windows output encoding).** Confidence: high.
  - `skills/_shared/runner.py` prints the envelope with `ensure_ascii=False`.
  - When stdout is a pipe on Windows, Python encodes with the locale code page, which is cp1252.
  - A finding that quotes a character outside cp1252, such as "→", raises `UnicodeEncodeError`, and the skill gets a traceback instead of an envelope.
  - Claude Code's Bash tool on this machine sets neither `PYTHONUTF8` nor `PYTHONIOENCODING`, and the crash reproduced through that tool.
  - The smoke and unit jobs run on Linux, which is why CI never saw it.
- **E85 (accessibility reads a `background:` shorthand holding `var()` as no background).** Confidence: high.
  - `checks.py` documents that an unparseable colour, such as a CSS variable, skips the check for that element.
  - `background-color: var(--x)` is skipped correctly.
  - `background: var(--x)` is not skipped. The resolver walks past it to the page default and reports white text on white at 1.00:1.
  - On the lean-canvas badges the true ratios are 2.15:1 on amber and 3.76:1 on red, so the verdict "fails AA" happens to be right, but the evidence printed is wrong.
- **E86 (microcopy has no check that the input is in its format).** Confidence: high.
  - ADR 0018 sets the artifact format: annotated screens, with a bare string list accepted as degraded input.
  - An edge-cases document is neither of those, yet the scripted lane treats every paragraph as a message and reports 31 severity-3 "not constructive" findings.
  - A document outside the claim should be refused or reported as unreadable, not graded.
- **E82, new evidence (non-prose markdown read as prose).** Confidence: high. The defect class is wider than tables. On a 25-line email of ordinary prose, `critique-clarity` produced these misfires:
  - Bold label lines, a salutation, a sign-off and list items each got PLAIN-TRANSITIONS at severity 3.
  - List items were joined into one "43-word sentence".
  - On the unextracted sample, YAML inside a code fence and `---` horizontal rules were read as paragraphs.

## Open decisions for the maintainer

1. **The microcopy flagship's source.** No sibling library produces annotated screens, and the
   edge-cases document is outside the claim, so the candidate does not meet criterion 3. Three ways
   forward:
   - **A.** A verbatim extract of the edge-cases document's quoted error strings, as a bare list.
     It is honest and in the claim, but it is degraded input, so 8 of the 14 criteria have nothing
     to read.
   - **B.** The same strings, restructured into ADR 0018's annotation format using only the
     document's own words for placement and trigger. It is in the measured format, but the
     restructuring is authored, and the walkthrough must say so.
   - **C.** A public licensed source of real product error messages. None has been found yet, and
     finding one means a licence check per source.

   Recommendation: B, medium confidence. The words stay real and only the layout is authored.
2. **Criterion 4 for zero-scripted flagships.** Docs, forms and usability produced no scripted
   finding on realistic inputs, and each for a documented reason. Criterion 4 asks a walkthrough to
   show at least one scripted finding and one judged finding.
   - **Recommendation, medium confidence:** the skill's existing walkthrough satisfies criterion 4,
     and the flagship reports its zero scripted findings and says why.
   - **Why not swap:** choosing inputs until the scripted lane fires would be selecting evidence,
     which D1 rules out.

## Not verified

- **Whether E84 broke a live skill run.** The E54 run on Windows succeeded, so either its findings
  happened to fit cp1252 or that run's environment differed. A Windows skill run on a document with
  such a character has not been tried, because that would be a paid run.
- **What the judged lane does on these candidates.** Only phase 4 can show that.

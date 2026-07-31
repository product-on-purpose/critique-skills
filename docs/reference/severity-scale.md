---
title: Severity scale
description: The shared 0-4 severity scale, its weighing order, and per-domain anchor examples
audience: both
level: intermediate
---

# Severity scale

Every critique-skills finding carries one severity value on one 0-4 scale, defined as `$defs/severity` in [`contract/critique-contract.schema.json`](../../contract/critique-contract.schema.json). The scale does not vary by domain: the six launch skills share it so a severity 3 in a clarity critique and a severity 3 in an accessibility critique carry the same weight. Severity must be a JSON integer literal (`3`, not `3.0`); the contract rejects the float form even though JSON Schema's `integer` type would otherwise accept it.

## The scale

| Level | Meaning | Disposition |
|---|---|---|
| 0 | Not a problem | Ignore |
| 1 | Cosmetic | Optional, fix only if time permits |
| 2 | Minor | Backlog |
| 3 | Major | Fix before release |
| 4 | Catastrophic | Blocking |

The gate reads only levels 3 and 4: a run fails when `summary.by_severity["4"]` is above zero, or when `summary.by_severity["3"]` is above the run's `severity_3_threshold` (default 0). See [Critique contract](critique-contract.md) for the full gate walkthrough.

## Weighing order

Assign severity by weighing three factors, always in this order:

1. **Impact.** How badly does this obstruct the reader or user, and can they recover on their own?
2. **Frequency.** Does it happen once, or does it recur across the artifact?
3. **Persistence.** Does its effect end where it occurs, or does it compound as the reader continues past it?

Impact sets the level first. A single occurrence of something that blocks recovery outranks something merely repeated, and a defect whose effect compounds as the reader continues outranks one that resolves the moment they move past it. Frequency and persistence pull a borderline finding up or down within the range impact already set; they do not override it. A finding that is a 2 on impact alone does not become a 4 by occurring often. Inflation defeats the scale's purpose: a run where everything is severe is a run nobody can gate on.

## Domain anchors

The examples below are original, illustrative anchors, not the six skills' criterion catalogs. Each skill's own `references/` directory, once built, carries the authoritative criterion registry and its own anchor examples per criterion; these anchors exist to calibrate levels 2 and 3 consistently across domains before any skill ships. Level 2 and level 3 are anchored here because they are where reviewers most often disagree; 0, 1, and 4 rarely need debate.

### Usability (critique-usability)

Artifact: HTML or markdown UI specs and page mockups, not live applications.

| Severity | Example |
|---|---|
| 2 | A settings panel labels the same commit action "Save" on the profile tab and "Apply changes" on the notifications tab, with no other signal the two mean the same thing. |
| 2 | A four-step signup form shows a step-progress indicator on steps 1 and 2, then drops it on step 3, which is inconsistent but does not block completion. |
| 3 | A "Delete account" control fires immediately on click, with no confirmation step and no undo, so one accidental click is unrecoverable. |
| 3 | A checkout form's "Continue" button stays disabled with no visible reason after every required field is filled in correctly, blocking anyone who reaches that state until they guess the cause. |

### Accessibility (critique-accessibility)

Artifact: HTML pages and fragments, markdown where mappable.

| Severity | Example |
|---|---|
| 2 | A decorative "New" badge icon carries alt text "icon" instead of being marked decorative, adding screen-reader noise without blocking comprehension of the surrounding text. |
| 2 | A footer link's focus outline is present but renders at 1px against a dark background, technically detectable but easy to miss. |
| 3 | Body copy across an entire article page renders at 2.9:1 contrast against its background, below the 4.5:1 AA minimum, making the page's primary reading task hard to complete for low-vision readers. |
| 3 | A modal dialog captures keyboard focus on open with no keyboard path to close it, trapping keyboard-only users inside it. |

### Clarity (critique-clarity)

Artifact: markdown or plain-text prose documents.

| Severity | Example |
|---|---|
| 2 | One paragraph mid-document shifts from active to passive voice for three consecutive sentences, forcing the reader to re-identify who is doing what, then the prose recovers. |
| 2 | A single section heading uses unexplained jargon where every other heading in the document uses plain terms. |
| 3 | The opening paragraph, the part most readers actually finish, buries the recommendation inside a 50-plus-word sentence with several subordinate clauses, so a reader cannot state the ask after one pass. |
| 3 | Every step in a five-step setup procedure is written in passive voice ("the file should be renamed"), so the reader must guess who performs each action, and the ambiguity compounds across the whole procedure. |

### Docs (critique-docs)

Artifact: technical documentation pages and trees in markdown.

| Severity | Example |
|---|---|
| 2 | A how-to page opens with two paragraphs of conceptual background before its first step, a small explanation-mode lapse in an otherwise task-focused page. |
| 2 | A reference page for one API method includes a single aside recommending a design pattern, a minor mode mix in an otherwise clean entry. |
| 3 | A getting-started tutorial interleaves step-by-step instructions with "why this matters" tangents at every step, so a first-time reader cannot follow the procedure without also weighing unrelated design arguments along the way. |
| 3 | A required environment variable is documented only on one reference page, with no tutorial, how-to, or explanation page linking to it, so a reader who needs it can only find it by guessing to open that page. |

### Microcopy (critique-microcopy)

Artifact: error messages, empty states, and microcopy strings.

| Severity | Example |
|---|---|
| 2 | An inline email-format error reads "Invalid input" instead of naming the field or the expected format, adding friction the user can still resolve by trial and error. |
| 2 | An empty search-results state reads "No data" instead of naming what was searched. |
| 3 | A payment-failure message reads "Something went wrong. Try again." with no indication of what to change, so a user whose card was actually declined has no way to know a retry will fail the same way. |
| 3 | A file-upload error reports a raw status code with no plain-language explanation, leaving a non-technical user with no path to resolve the failure. |

### Argument (critique-argument)

Artifact: argumentative prose, essays, proposals, position documents.

| Severity | Example |
|---|---|
| 2 | A proposal states its claim and grounds clearly but leaves one supporting statistic uncited, weakening that single point without undermining the proposal's overall structure. |
| 2 | A position paper's closing section restates its main claim in different words without adding new grounds, a redundant but harmless passage. |
| 3 | A recommendation memo asserts "adopt Option B" with grounds that only describe Option A's cost, never stating the warrant connecting Option A's cost to choosing Option B, so a skeptical reader cannot reconstruct why the conclusion follows. |
| 3 | An essay's central claim has no stated rebuttal to the most obvious counterargument, leaving the argument unable to survive the first question a skeptical reader would ask. |

## See also

- [Critique contract](critique-contract.md), the finding schema this scale plugs into.
- [Criterion IDs](criterion-ids.md), the identifiers each finding cites alongside its severity.
- [Methodology, section 6](../explanation/methodology.md#6-severity), the rationale for one shared scale across every domain.

---
title: Skill template
description: The instantiation guide for every critique-<domain> skill, the anti-drift mechanism for parallel skill construction
audience: agent
level: intermediate
---

# Skill template

This is the pattern every `critique-<domain>` skill instantiates. It exists so six skill pipelines
working in parallel produce structurally identical, contract-conformant skills that differ only in
domain content ([S-04 skill-template spec](release-plans/plan_v0.1.0/S-04_skill-template/spec.md),
`docs/internal/release-plans/plan_v0.1.0/S-04_skill-template/spec.md`).

**Read this document fully before writing a skill.** It is written so a pipeline agent can build a
`critique-<domain>` skill from this file alone, without reading another skill's source (S-04 AC-1).
Where this document and its normative dependencies disagree, the dependency wins:

- [`contract/critique-contract.schema.json`](../../contract/critique-contract.schema.json) and
  [`contract/README.md`](../../contract/README.md) for the finding and envelope shape. Frozen; never
  edit these to fit a skill.
- [`docs/explanation/methodology.md`](../explanation/methodology.md) for the four-pass protocol,
  lanes, severity, determinism, and provenance. Frozen; the constitution.
- [`docs/reference/criterion-ids.md`](../reference/criterion-ids.md) for the criterion ID grammar and
  namespace registry.
- [`docs/reference/severity-scale.md`](../reference/severity-scale.md) for the shared 0-4 scale.
- [`bench/generator/README.md`](../../bench/generator/README.md) for the corpus domain-plugin API a
  skill's bench module implements.

Domain content itself (which criteria, what they say, the corpus vocabulary) is out of scope here;
that is [S-05 (skills slate)](release-plans/plan_v0.1.0/S-05_skills-slate/spec.md)'s job, per its own
per-skill table. This document is the shape every one of those six skills pours its content into.

## Directory shape

Fixed, per the S-04 spec. A skill's directory is `skills/critique-<domain>/`:

```
skills/critique-<domain>/
  SKILL.md
  references/<source-id>.md          one per rubric source: criterion table with IDs, anchors, operationalizations
  references/severity-anchors.md     domain anchor examples, extends docs/reference/severity-scale.md
  scripts/checks.py                  scripted lane; CLI: artifact path in, contract run envelope out
  scripts/tests/__init__.py          empty package marker
  scripts/tests/test_checks_<domain>.py   pytest for every scripted check; the domain suffix is required
  evals/triggers.eval.json           >=20 {query, should_trigger} cases, >=3 cross-domain negatives
  examples/                          >=3 golden runs, >=1 anti-example
```

Nothing outside this shape. A pipeline that needs somewhere to put working notes uses `_local/`
(gitignored), never a stray file inside the skill directory itself; the family conformance gate and
`scripts/skill-selftest.py` both assume this shape exactly.

A committed, self-test-passing instance of this whole shape lives at
[`skills/_template-fixture/critique-toy/`](../../skills/_template-fixture/critique-toy/); read it
alongside this document when a section here is easier to see than to describe. It is a fixture, not a
seventh skill: "Where a skill directory may live", below, explains why it sits under a wrapper
directory.

The skill's bench corpus module lives outside this tree, at
`bench/generator/domains/<domain>.py`, registered in `bench/generator/registry.py`. See "Corpus
module obligation" below.

## Naming

`name` in frontmatter is `critique-<domain>`, matching the directory name exactly
([ADR 0001](decisions/0001-critique-prefix-naming.md), prefix rule D1). `<domain>` is lowercase,
hyphen-separated, no `critique-` inside it a second time. The prefix carries zero triggering weight
by design; every triggering signal has to come from `description`, never from the name.

**This rule has no exceptions, including for fixtures and experiments.** It is enforced twice, by two
independent implementations: `scripts/skill-selftest.py` (`frontmatter-name-mismatch`,
`frontmatter-name-invalid`) and the family conformance gate's own U4 `name-matches-dir` and S2
`prefix` checks. The family gate's U4 finding is a hard error that blocks the Universal tier outright,
so a directory named anything else does not merely warn: it fails `npm run check`, and with it the CI
`conformance` job.

### Where a skill directory may live

The family gate and the plugin manifest both treat exactly `skills/<dir>/SKILL.md` as the set of
skills this plugin ships. That single fact settles two questions:

- **A shipped skill** lives at `skills/critique-<domain>/` and is registered in `library.json`'s
  `components.skills`. On disk but unregistered is a delivery failure the gate reports (U13); the
  scan is what makes registration meaningful.
- **A skill-shaped directory that must not ship** - a fixture, a reference build, an experiment -
  goes one level deeper, under an underscore-prefixed wrapper: `skills/_fixture-wrapper/critique-<domain>/`.
  The wrapper has no `SKILL.md` of its own, so the scan never reaches the skill inside it, while the
  skill directory itself still satisfies the naming rule exactly. Do not try to solve this by naming
  the directory something outside the `critique-<domain>` pattern; that is the case the gate rejects.

The template's own committed reference build uses the second form:
[`skills/_template-fixture/critique-toy/`](../../skills/_template-fixture/critique-toy/), a complete
skill built from this document end to end against the `toy` domain (S-04 spec, Behavior/Examples). It
is the one place to look for what a finished instantiation of every section below looks like together,
and `python scripts/skill-selftest.py skills/_template-fixture/critique-toy` exits 0 against it. Its
one unrepresentative feature is an empty judged lane; see "Lane manifest".

## SKILL.md frontmatter

### Format

Frontmatter is YAML delimited by `---` on the first and closing lines, but written in a
**deliberately restricted block subset**: mappings, sequences of scalars, and sequences of flat
mappings only. No flow style (`{a: 1}`, `[1, 2]`) beyond the bare `[]` empty-sequence token, no
multi-line scalars, no anchors or tags, no
nested sequences inside a sequence item. `scripts/skill-selftest.py` implements exactly this subset
(not general YAML) so it needs no dependency beyond the Python stdlib; writing outside it is a parse
failure, not a warning.

Every scalar value is one line. Quote a value in double quotes only if it needs escaping (a literal
`:` followed by a space, for instance); otherwise leave it bare. `null` (or an empty value) means
absent.

Two consequences of "one line" catch people out, because both are ordinary YAML habits:

**Block scalars are not supported.** `description: >-` (folded) and `description: |` (literal),
followed by an indented block, are how most YAML front matter in the wild wraps a long value. This
dialect cannot read either one: a `description` that runs to four printed lines is still written as a
single physical line, in double quotes.

```yaml
# WRONG - the parser stops here, and skill-selftest.py reports
# [frontmatter-block-scalar-unsupported]
description: >-
  Reviews markdown or plain-text prose for clarity. Use when the user asks
  for a review, feedback, or a second opinion on a memo.

# RIGHT - one physical line, however long it gets
description: "Reviews markdown or plain-text prose for clarity. Use when the user asks for a review, feedback, or a second opinion on a memo."
```

**An empty sequence is written `[]`, or as a key with nothing after it.** Block style has no way to
express an empty sequence, so `[]` is the single flow-style token this dialect accepts; a key with an
empty value parses to `null` and is treated as empty wherever a list is expected. Both forms below are
valid and mean the same thing. A *non-empty* flow sequence stays unsupported: `judged: [A, B]` parses
as the literal string `"[A, B]"` and then fails the criterion-ID grammar.

```yaml
checks:
  scripted:
    - TOY-ACTIVE
  judged: []      # preferred: says "deliberately empty" out loud

checks:
  scripted:
    - TOY-ACTIVE
  judged:         # also valid, and easier to misread as unfinished
```

### Required fields

| Field | Shape | Rule |
|---|---|---|
| `name` | string | `critique-<domain>`, equals the directory name exactly. |
| `description` | string, >=40 chars | Pushy trigger surface. See "Writing the description" below. |
| `version` | string | Semantic version, no leading `v` (`0.1.0`). |
| `license` | string | `Apache-2.0`, matching the repository license ([ADR 0005](decisions/0005-licensing-apache-and-cc-by.md)). Skills are code and documentation, not bench-corpus content, so the CC-BY-4.0 corpus license does not apply here. |
| `rubric_sources` | sequence of mappings | One entry per source. See "rubric_sources" below. |
| `checks` | mapping | `scripted` and `judged`, each a sequence of criterion IDs. See "Lane manifest" below. |

`scripts/skill-selftest.py` fails distinctly (its own `rule` name) on a missing required field, an
unparseable frontmatter block, a `name` that does not match the directory, an invalid `version`, and
every failure mode named below; see "Self-test" for the full list.

### Writing the description

The description is the entire triggering surface (methodology has no opinion on triggering; this is
the family's own convention, [S-02 strategy doc sec 3.3-3.5](
release-plans/plan_v0.1.0/S-02_critique-contract/spec.md)). It must be **pushy**: name the artifact
types the skill critiques and the everyday phrasings a requester actually uses, not the rubric's
vocabulary and never the skill's own name. Aim for language a person would type, drawn from at least
several of: review, feedback, second opinion, red-line, quality check, critique. A description that
only restates `critique-<domain>` in prose will not trigger on the language people actually use, and
`scripts/skill-selftest.py`'s advisory checks (warnings, not hard failures; see "Self-test") flag a
description that uses none of them.

The family's U5 description-quality rubric is what actually scores this (S-04 spec AC-6, threshold
0.7); it lives in the sibling `agent-skills-toolkit` repository and runs as part of the family
conformance gate (`node scripts/check.mjs`, `AGENTS.md` "Checks"). `scripts/skill-selftest.py` does
not implement U5 itself; see "Self-test" for exactly what it checks instead and why.

### The four rules that decide the score

U5 is a deterministic scorer, not a judge, and a description that reads beautifully can still land
under 0.7. Four rules cover it. Follow all four and the margin is comfortable; miss the second one
and the ceiling is 0.65, below threshold, no matter how good the prose is.

1. **Open with a present-tense action verb**, describing what the skill does to the artifact.
   `Reviews`, `Checks`, `Audits`, `Evaluates`, `Assesses`, `Analyzes`, `Reports` all count.
2. **Include an explicit use-when clause.** This is the one that gets missed. The scorer recognises
   `Use when ...`, `Use this when ...`, `Use this skill when ...`, the `whenever` variants of each,
   `when the user ...`, `whenever the user ...`, `when you need ...`, `for when ...`, and
   `if the user asks / mentions / wants / needs ...`. It does **not** recognise `Use for ...`, which
   is the natural thing to write and is worth zero. `Use when the user asks for a review, ...` is the
   house form.
3. **Write at least eight words of ordinary lowercase prose**, which any real description clears.
4. **Stay in the third person.** No `I `, no `we `, no `you can`, no `you should`. Addressing the
   reader costs credit; describing the artifact and the request does not. (`before you send it` is
   fine: `you should` and `you can` are the penalized forms.)

Two smaller traps: angle brackets anywhere in the description cost a fixed penalty, so never write the
literal `critique-<domain>` in it (you should not be naming the skill in its own description anyway);
and an unfinished-placeholder token (`TODO`, `TBD`, `FIXME`) is a heavy penalty, which matters if a
draft description ever survives to commit.

### Two worked examples

Drawn from [S-05's skill table](release-plans/plan_v0.1.0/S-05_skills-slate/spec.md). Both score 1.00
on U5. Note the single physical line: block scalars are not available here (see "Format" above).

```yaml
description: "Reviews markdown or plain-text prose for clarity against the Federal Plain Language Guidelines and Williams' Style: readability, passive voice, sentence length, and nominalization density. Use when the user asks for feedback, a second opinion, a red-line pass, or a quality check on a memo, PRD, proposal, or any prose document before it goes out."
```

```yaml
description: "Reviews HTML pages and fragments (markdown where mappable) against WCAG 2.2 AA: contrast, alt text, heading structure, link text, and keyboard and screen-reader access. Use when the user asks for an accessibility review, an a11y audit, or a pre-launch quality check on a page or component."
```

Each opens with `Reviews` (rule 1), names its artifact types and its rubric, and closes with
`Use when the user asks for ...` followed by the everyday phrasings (rule 2). Swapping that closing
clause to `Use for feedback, a second opinion, ...` - which reads no worse to a human - drops both to
0.65 and fails AC-6.

### `rubric_sources`

One entry per rubric the skill operationalizes, in the methodology's own shape (section 11):

```yaml
rubric_sources:
  - id: PLAIN
    citation: "US Federal Plain Language Guidelines"
    url: https://www.plainlanguage.gov/guidelines/
    accessed: 2026-07-31
    operationalization: open-standard
  - id: WILLIAMS
    citation: "Williams, J. M. (2014). Style: Lessons in Clarity and Grace, 11th ed. ISBN 978-0321953304, ch. 2-4."
    url: null
    accessed: 2026-07-31
    operationalization: paraphrased
```

- `id` is the rubric's own short handle; it is usually, but need not be, the criterion namespace
  (see [criterion-ids.md](../reference/criterion-ids.md)).
- `citation` is enough for a reader to find the source. Book sources cite ISBN and a page or chapter
  range ([S-05 Non-Functional Requirements](release-plans/plan_v0.1.0/S-05_skills-slate/spec.md)); a
  web standard cites its canonical URL as the citation too if that reads more naturally.
- `url` is the canonical link; `null` for a source with no stable one (most books).
- `accessed` is the date the pipeline agent actually read the source, `YYYY-MM-DD`.
- `operationalization` is one of three values, and it is policy, not documentation ([ADR 0006](
  decisions/0006-copyright-paraphrase-policy.md), methodology section 11):
  - `paraphrased` - copyrighted material (Nielsen, Williams, Toulmin, NN/g). The skill's own
    operationalization is original wording with citation; the source text itself is never
    reproduced beyond a short anchor quote in `references/`.
  - `open-standard` - openly licensed and citable directly (WCAG, Diátaxis).
  - `byor` - the rubric was supplied by the user at run time (v0.2; not used by any v0.1 skill).

### Lane manifest

```yaml
checks:
  scripted:
    - PLAIN-ACTIVE
    - PLAIN-NOMINAL
  judged:
    - WILLIAMS-COHESION
    - WILLIAMS-AUDIENCE-FIT
```

Both `scripted` and `judged` must be present, each a sequence of criterion IDs matching the grammar
in [criterion-ids.md](../reference/criterion-ids.md)
(`^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+(?:\.[A-Z0-9]+)*)+$`). **No criterion ID appears in both lists.** A
criterion is either deterministically checkable (scripted) or it is not (judged); a criterion that is
sometimes one and sometimes the other is two criteria, not one.

A lane may be legitimately empty, written `judged: []` (see "Format"); the key still has to be
present, because an absent lane and a deliberately empty one are different claims. For a v0.1 skill,
though, an empty judged lane is almost certainly wrong: "Corpus-module obligation" below requires
injector and recipe coverage for at least three judged-lane criteria, and a rubric with nothing a
reader has to weigh is not a rubric this family has a use for. The template fixture's own
`judged: []` is a property of the `toy` grammar (every TOY-* criterion is a fixed pattern by
construction), not a model to copy.

`scripts/skill-selftest.py` cross-checks this manifest against `scripts/checks.py` itself (see
"Lane-manifest consistency" below): every criterion `checks.py` actually implements must be declared
in `checks.scripted`, and every criterion declared in `checks.scripted` must actually be implemented.
A skill's judged-lane criteria are not independently machine-checked against anything in code; the
critic subagent or inline protocol is what exercises them (S-06, out of this document's scope).

## SKILL.md body

The body is instructions to whatever is executing the skill: the `critique-critic` subagent (S-06)
where available, or a host agent following the protocol inline. It is not documentation for a human
reader first; write it as an instruction sequence.

### Required structure, in order

1. **Title and one-paragraph purpose.** What this skill critiques and against what standard, in one
   or two sentences.
2. **Contract reference.** State that every finding conforms to
   `contract/critique-contract.schema.json` and point at `docs/reference/critique-contract.md` for
   the field contracts a schema cannot check (location navigable unaided, evidence quoted or
   measured, violation names the breach, fix actionable). Do not restate the schema; reference it.
3. **The four-pass protocol**, in this fixed order (methodology section 7). Copy this block, adapted
   only to name the skill's own criteria:

   ```markdown
   ## Protocol

   Follow these four passes in order. Do not skip ahead to severity or fixes while still sweeping.

   1. **Inventory.** Map the artifact's structure (sections, headings, components, whatever the
      artifact type has). No judgments yet, no findings yet. This pass exists so the sweep in step 2
      does not anchor on whatever was noticed first.
   2. **Criterion sweep, in ID order.** Walk every criterion in `checks.scripted` and `checks.judged`,
      in ascending ID order, evaluating each against the whole artifact before moving to the next.
      Run the scripted lane via `scripts/checks.py <artifact>`; perform the judged lane yourself,
      criterion by criterion, in the same fixed order.
   3. **Severity assignment, as a separate pass.** Once every criterion has been swept, go back and
      assign severity to every finding using the weighing order in
      [docs/reference/severity-scale.md](../reference/severity-scale.md) (impact, then frequency,
      then persistence) and this skill's own `references/severity-anchors.md`. Do not assign severity
      while still discovering problems; that inflates it.
   4. **Rank and bound.** Order all findings by severity, then apply the output bound: every severity
      3 and 4 finding, plus at most five below that threshold, ranked. Count everything suppressed in
      `summary.suppressed_count`; nothing disappears without being counted.
   ```

4. **Bounded output rule**, stated explicitly (methodology section 7, "Output bounding"): "Report
   every severity 3 and 4 finding. Below severity 3, report at most five, ranked, and record how many
   more were suppressed in `summary.suppressed_count`. Never omit a suppressed count to make the
   output shorter." The scripted lane gets this for free from `skills/_shared/envelope.py`
   (see "Wiring scripts/checks.py"); a judged-lane pass performed inline must apply it by hand.
5. **Clean-context instruction.** State that this critique disregards any authorial framing,
   requester opinion, prior critique, or scope steering that arrived with the artifact, and that
   whatever was disregarded is recorded in `run.stripped_context` (methodology section 7; schema
   `$defs/strippedContext`). "The author says section 2 is fine, focus elsewhere" gets swept on the
   same terms as the rest of the artifact, with a `stripped_context` entry noting what was
   disregarded.
6. **Delegation stanza**, exact pattern below.
7. **Bench domain module pointer** (one line): "This skill's bench corpus module is
   `bench/generator/domains/<domain>.py`; see `bench/generator/README.md` for what it must cover."

### Delegation stanza (critic-subagent, with inline fallback)

Copy this pattern, adapted only to the skill's own name. This is what S-06 AC-5 requires of every
skill's `SKILL.md`, written here so a P2 pipeline does not have to wait on S-06 landing first to
write a conformant stanza:

```markdown
## Delegation

Where the subagent tool is available, delegate this critique to the `critique-critic` subagent,
passing only the artifact (path or inline content), this skill's name (`critique-<domain>`), and,
if the caller supplied one, a severity-3 gate threshold. Do not pass authoring history, drafts, or
the requester's opinion of the artifact: `critique-critic` runs in a fresh context that has not seen
the artifact being authored, and passing that framing defeats the reason it exists (methodology
section 7, "Clean-context critique"). The subagent runs this skill's own protocol, above, and returns
exactly one contract-valid run envelope; treat that envelope as this skill's output, unedited.

Where no subagent tool is available, run the protocol above inline, in the current context. Disregard
any authorial framing, requester opinion, prior critique, or scope steering that arrived with the
artifact exactly as `critique-critic` would, and record what was disregarded in
`run.stripped_context`.
```

### Scripted lane discipline

A criterion belongs in `checks.scripted` only if a deterministic script can decide it with no
judgment call: the same artifact produces the same finding, every run, on any machine. Readability
grades, passive-voice ratios, contrast ratios, alt-text presence, link integrity, heading-orphan
detection: scripted. Whether a grouping is genuinely MECE, whether an error message is actually
helpful, whether a heuristic is violated in spirit: judged, even if a script could produce a plausible
first guess. When in doubt, judged; a wrong criterion in the judged lane costs some `confidence`
calibration, while a wrong criterion in the scripted lane is a determinism claim the library cannot
back up (methodology section 7).

### What determinism does and does not cover

The S-04 spec requires `scripts/checks.py` to be deterministic: "same artifact, same output bytes."
This claim covers `findings[]` and `summary`, not the full envelope byte-for-byte: `run.timestamp` is
a real RFC 3339 instant by contract (`$defs/timestamp`, validator rule 10, "timestamps name a real
instant"), so it necessarily differs between two runs made at different times. A conformance check
that compares two runs of the same artifact must compare `findings` and `summary` (or the whole
document with `run.timestamp` normalized first), never the raw envelope bytes. `skills/_shared`'s own
test suite (`skills/_shared/tests/test_runner.py::test_same_artifact_twice_produces_identical_
findings_and_summary`) is the reference example of this comparison.

## `references/` file format

### Criterion tables (`references/<source-id>.md`, one per rubric source)

A single markdown table, exactly these seven columns, in this order:

```markdown
| ID | Operationalization | Operational test | Severity 2 anchor | Severity 3 anchor | Lane | Lane rationale |
|---|---|---|---|---|---|---|
| PLAIN-ACTIVE | Sentences default to active voice; passive constructions appear only when the actor is unknown, irrelevant, or the object is genuinely the point. | Flag a sentence as a violation when it is passive and the actor is both known and relevant. | One paragraph mid-document lapses into passive voice for a few consecutive sentences, then recovers. | A multi-step procedure is written entirely in passive voice, so the reader must guess who performs every action. | scripted | POS-taggable via a fixed be-plus-participle pattern; no judgment call is needed to detect the construction. |
```

Column contracts:

- **ID** - the criterion's permanent identifier (see [criterion-ids.md](../reference/criterion-ids.md)).
  Every ID declared anywhere in `checks.scripted` or `checks.judged` must have exactly one row here
  (across this skill's `references/*.md` files); no ID appears in two skills' tables except an
  upstream WCAG ID, which appears only in `critique-accessibility` (S-05 AC-3).
- **Operationalization** - the skill's own original-wording test for this criterion, citing the
  source by `rubric_sources.id`. **This column must contain zero quotation marks, of any kind.** It
  is paraphrase by definition ([ADR 0006](decisions/0006-copyright-paraphrase-policy.md)); a
  quotation mark here means source text leaked into the operationalization, and
  `scripts/skill-selftest.py` fails on it directly (`paraphrase-operationalization-quoted`).
- **Operational test** - the concrete decision procedure a finding must satisfy to cite this
  criterion: what to look for, stated so two independent reviewers reach the same verdict.
- **Severity 2 anchor / Severity 3 anchor** - one domain-specific worked example each, calibrated
  against [docs/reference/severity-scale.md](../reference/severity-scale.md)'s weighing order. These
  two levels are anchored per-criterion (not just per-domain) because they are where reviewers most
  often disagree.
- **Lane** - `scripted` or `judged`, matching this criterion's entry in `SKILL.md`'s `checks`.
- **Lane rationale** - one sentence on why this criterion sits in that lane. "Detectable by a fixed
  pattern, no judgment call" for scripted; "requires reading X as a whole" for judged.

**Short anchor quotes** (a phrase, not a passage) may appear elsewhere in the file, e.g. a "source
text" aside used to orient a reader, but never inside the Operationalization column and never as the
criterion text itself. `scripts/skill-selftest.py` flags any quoted span longer than 25 words anywhere
in a `references/*.md` file (`paraphrase-quote-too-long`); this is a documented approximation, not a
copyright detector, and staying well under the threshold is the actual goal, not clearing it exactly.

### `references/severity-anchors.md`

Free prose, not a table: this skill's own domain-anchor examples, extending
[docs/reference/severity-scale.md](../reference/severity-scale.md)'s "Domain anchors" section with
whatever additional calibration this skill's criterion table doesn't already carry. The paraphrase
heuristic's quote-length check still applies to this file; its operationalization-column check does
not, since this file is not a criterion table.

## Wiring `scripts/checks.py`

Every skill's scripted lane is: import `skills/_shared`, write one check function, call
`run_scripted_lane`. Gate exit-code semantics, envelope assembly, and output bounding live in
`skills/_shared` exactly once (S-04 AC-4); a skill's `checks.py` never reimplements any of them.

### The bootstrap

`scripts/checks.py` is conventionally invoked directly
(`python skills/critique-clarity/scripts/checks.py <artifact>`), not via `python -m`, so nothing puts
the repository root on `sys.path` automatically. Every skill's `checks.py` opens with this exact
bootstrap, which finds the repository root by walking up to the directory holding `library.json`
(the repository's own canonical marker file, per `AGENTS.md`) rather than assuming a fixed depth, so
it keeps working if a skill is ever relocated:

```python
import sys
from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "library.json").is_file():
            return candidate
    raise RuntimeError("could not locate the repository root (no library.json found above this file)")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve())
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from skills._shared.runner import run_scripted_lane
from skills._shared.findings import RawFinding
```

### The whole file, worked example

This is the entire pattern, shown against the `TOY-ACTIVE` and `TOY-HEDGE` criteria from the toy
domain ([`bench/generator/README.md`](../../bench/generator/README.md), "Worked example: the `toy`
domain") a pipeline agent adapts by replacing the bootstrap's nothing, the two module-level constants,
and the body of `check`:

```python
import re
import sys
from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "library.json").is_file():
            return candidate
    raise RuntimeError("could not locate the repository root (no library.json found above this file)")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve())
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from skills._shared.runner import run_scripted_lane
from skills._shared.findings import RawFinding

# Every criterion this scripted lane checks. Cross-checked against
# SKILL.md's checks.scripted by scripts/skill-selftest.py; the two must
# name exactly the same set.
IMPLEMENTED_CRITERIA = frozenset({"TOY-ACTIVE", "TOY-HEDGE"})

HEDGES = ("it may possibly be the case that", "it could perhaps be argued that")


def check(artifact):
    """artifact: skills._shared.artifact.Artifact (artifact.path,
    artifact.text, artifact.sha256). Returns RawFindings, unranked and
    unbounded; run_scripted_lane does the rest."""
    findings = []
    for line_number, line in enumerate(artifact.text.splitlines(), start=1):
        lowered = line.strip().lower()
        if any(lowered.startswith(hedge) for hedge in HEDGES):
            findings.append(
                RawFinding(
                    criterion="TOY-HEDGE",
                    severity=2,
                    location=f"line {line_number}",
                    evidence=line.strip(),
                    violation="A stacked hedge placed ahead of an otherwise direct statement.",
                    fix="Delete the hedge and state the sentence directly.",
                )
            )
    return findings


def main(argv=None):
    return run_scripted_lane(
        skill_name="critique-toy",
        skill_version="0.1.0",
        rubrics=["TOY"],
        check_fn=check,
        argv=argv,
    )


if __name__ == "__main__":
    sys.exit(main())
```

The block above is trimmed to the pattern; the fixture's own
[`scripts/checks.py`](../../skills/_template-fixture/critique-toy/scripts/checks.py) is the same
pattern carried through to all three TOY criteria, including a structural one, and is worth reading
next to this.

Run it: `python skills/_template-fixture/critique-toy/scripts/checks.py bench/corpus/toy/toy-001.md
--gate`. It prints one contract-valid run envelope to stdout and exits with the S-02 gate code
([`contract/README.md`](../../contract/README.md), "Gate exit codes"): 0 clean, 1 any severity 4,
2 severity-3 above threshold, 3 the envelope `checks.py` itself produced is invalid (a bug in `check`,
not a usage error), 4 a usage error (bad arguments, unreadable artifact).

### `skills/_shared` API surface

| Module | What it gives `checks.py` |
|---|---|
| `skills._shared.artifact.load_artifact(path, repo_root=None)` | Reads the file, hashes the raw bytes, and returns an `Artifact(path, text, sha256, disk_path)` with a contract-valid relative POSIX `path`. `run_scripted_lane` calls this; a check function only ever receives the result. |
| `skills._shared.findings.RawFinding` | The dataclass a check function returns instances of: `criterion`, `severity`, `location`, `evidence`, `violation`, `fix`, plus optional `instances`, `rubric_source`, `selector`. `lane` and `confidence` default to `"scripted"` / `"high"`; a scripted check never sets them. |
| `skills._shared.envelope.assemble_envelope(...)` | Pass 4 (rank and bound) plus the run record and summary. `run_scripted_lane` calls this; a skill's `checks.py` does not call it directly unless it is doing something `run_scripted_lane` does not cover. |
| `skills._shared.gate.gate_exit_code`, `.validate_document` | Re-exported from `contract/validate.py` verbatim. Never reimplemented; this is the whole point of S-04 AC-4. |
| `skills._shared.runner.run_scripted_lane(*, skill_name, skill_version, rubrics, check_fn, argv=None)` | The entire body of `checks.py`'s `main()`. Parses arguments, loads the artifact, calls `check_fn`, assembles and validates the envelope, prints it, and returns the process exit code. |

### `scripts/tests/`

Pytest for every scripted check, one test module minimum, exercising `check()` (or whatever internal
functions it calls) directly against small in-memory or fixture artifacts: a clean case (no finding),
a triggering case (finding with the expected criterion, severity, and location), and any edge case the
check's own logic has (an empty artifact, a boundary condition). `scripts/skill-selftest.py` runs this
suite as part of its own checks (`checks-py-pytest-failed` on a failure, `checks-py-tests-missing` if
the directory is absent or empty) and treats a failing suite as a self-test failure, not a suggestion.

**Every test module's filename ends with the skill's own domain**: `test_checks_clarity.py`, not
`test_checks.py`. This is not a style preference. Under pytest's default import mode, two skills both
shipping `scripts/tests/test_checks.py` collide the moment anyone runs `python -m pytest` from the
repository root:

```
import file mismatch:
imported module 'test_checks' has this __file__ attribute:
  .../skills/critique-clarity/scripts/tests/test_checks.py
which is not the same as the test file we want to collect:
  .../skills/critique-usability/scripts/tests/test_checks.py
```

That is a **collection error**, not a test failure: the entire repository suite aborts, including
every test unrelated to either skill, and the CI `unit-python` job fails for all six skills because
two of them picked the same filename. `__init__.py` files do not fix it (a directory named
`critique-clarity` cannot be a Python package, so the package path never disambiguates the two), and
neither does anything a single pipeline can do after the fact. A domain-suffixed basename is the fix,
and `scripts/skill-selftest.py` enforces it (`checks-py-test-module-name`) from inside one skill
directory, which is all it can see.

Also add an empty `scripts/tests/__init__.py`. It is not what prevents the collision above, but it
keeps the directory a package rather than something pytest injects onto `sys.path`.

`pytest.ini`'s `testpaths` already carries the glob `skills/*/scripts/tests`, so a new skill's suite is
collected with no edit there.

## `evals/triggers.eval.json`

```json
{
  "skill": "critique-clarity",
  "cases": [
    {"query": "Can you review this PRD for clarity before I send it?", "should_trigger": true},
    {"query": "Give me a second opinion on this memo.", "should_trigger": true},
    {"query": "Check the color contrast on this landing page.", "should_trigger": false, "cross_domain": "critique-accessibility"},
    {"query": "What's the weather like today?", "should_trigger": false}
  ]
}
```

- `cases` has **at least 20** entries, each `{"query": string, "should_trigger": bool}`.
- **At least 3** cases have `should_trigger: false` (negatives).
- **At least 3** of those negatives carry a `cross_domain` field naming another `critique-*` skill,
  the query a real trigger-confusion case for that other skill rather than an obviously unrelated
  request ([S-05 spec, Behavior/Examples](release-plans/plan_v0.1.0/S-05_skills-slate/spec.md):
  "Cross-skill trigger confusion cases MUST appear in each skill's eval set"). A plain negative with
  no `cross_domain` field (an unrelated request, a weather query) still counts toward the 3-negative
  minimum but not toward the cross-domain minimum; both minimums must be met independently.
- At least one case has `should_trigger: true` (`scripts/skill-selftest.py` checks this as a sanity
  floor, not because the spec numbers it separately).

## `examples/`

Two kinds of file, both plain JSON, distinguished by a `kind` field. **At least 3 golden**, **at
least 1 anti-example**.

### Golden (`examples/golden-NN.json`)

```json
{
  "kind": "golden",
  "artifact": "bench/corpus/clarity/clarity-004.md",
  "expected_envelope": {
    "run": { "...": "a full run object, matching contract/critique-contract.schema.json" },
    "findings": [ "...": "at least one finding" ],
    "summary": { "...": "a reconciled summary" }
  },
  "note": "Paragraph two's lead sentence is passive with the actor deleted, which is exactly what PLAIN-ACTIVE's operational test flags; severity 2 because it recovers after one sentence rather than persisting."
}
```

`artifact` names the artifact critiqued (a corpus path is the common case, since the corpus already
carries known ground truth). `expected_envelope` is a complete, contract-valid run envelope
(`scripts/skill-selftest.py` validates it with `contract.validate.validate_document`, the same
validator everything else in the library uses). `note` is prose, at least 40 characters, explaining
*why* the findings are correct, not just restating that they exist. `expected_envelope.run.skill`
must equal this skill's `name`.

### Anti-example (`examples/anti-NN.json`)

```json
{
  "kind": "anti",
  "query": "Can you check whether this database schema is in third normal form?",
  "note": "Data-modeling correctness is not an artifact-and-rubric claim this skill's PLAIN/WILLIAMS criteria evaluate."
}
```

A query that must **not** trigger this skill, with a one-sentence note on why. This is the same shape
of case as a cross-domain negative in `evals/triggers.eval.json`, kept here as well because it is
documentation for a human reader, not just an eval fixture; the two are allowed to overlap in content.

## Corpus-module obligation

Every skill contributes `bench/generator/domains/<domain>.py`, implementing the domain-plugin API
frozen in [`bench/generator/README.md`](../../bench/generator/README.md). That document, not this
one, is the specification: vocabulary, `compose`, injectors, `address`, and recipes, exactly as its
"Worked example: the `toy` domain" section walks the `bench/generator/domains/toy.py` module that
already ships with the harness (S-03).

This template adds one coverage rule on top of that API (S-04 spec Requirements; also
[S-05 spec Requirements](release-plans/plan_v0.1.0/S-05_skills-slate/spec.md)): a skill's domain
module needs an injector, and at least one recipe planting it, for **every scripted-lane criterion**
and **at least three judged-lane criteria**, across at least three recipes of which at least one has
`plants=()` (a clean artifact). Minimum seeding coverage is what makes recall a meaningful number
later; a domain with untested criteria cannot report recall for them at all.

Steps:

1. Copy `bench/generator/domains/toy.py`'s shape, not its content: the six sections (vocabulary,
   composition, parsing helper if needed, injectors, addressing, recipes) in that order.
2. Declare `namespaces` matching this skill's criterion namespace(s) from
   [criterion-ids.md](../reference/criterion-ids.md)'s registry.
3. Write one injector per criterion the checklist above requires, each returning an
   `InjectionResult` with a meta-language `description` (never a quote of the planted text; the leak
   rule in `bench/generator/README.md` enforces this at build time).
4. Write `address` for this artifact type's anchor kinds.
5. Write at least three recipes.
6. Add the module to `bench/generator/registry.py`'s `DOMAIN_MODULES` tuple.
7. `python -m bench.generator validate --domain <domain>`, then `build`, then `verify`, then
   `leak-check`, in that order, from the repository root.

## Self-test

`scripts/skill-selftest.py` validates one skill directory before it leaves its pipeline:

```
python scripts/skill-selftest.py skills/critique-<domain>
```

It takes the skill directory as an argument and never guesses at it, so it validates a fixture build
under a wrapper directory just as readily:
`python scripts/skill-selftest.py skills/_template-fixture/critique-toy`.

Exit 0, "PASS", when every check passes. Exit 1 otherwise, with every failing check printed as
`[rule] path: message`, one line per issue, so a failure is never ambiguous about which check raised
it (S-04 spec AC-2: each of the five named failure modes below fails distinctly, not as one generic
message).

### What it checks

| Check | What it verifies | Failure `rule`(s), representative |
|---|---|---|
| Frontmatter parses | The block is readable in this document's restricted dialect. A block-scalar indicator (`>-`, `\|`) is reported separately, because the generic parse error names the continuation line rather than the indicator that caused it. | `frontmatter-block-scalar-unsupported`, `frontmatter-unparseable` |
| Frontmatter contract | Every required field present and shaped correctly; `name` matches the directory and the `critique-<domain>` pattern; `rubric_sources` entries complete with a valid `operationalization`. | `frontmatter-missing-field`, `frontmatter-name-mismatch`, `frontmatter-name-invalid`, `frontmatter-version-invalid`, `frontmatter-rubric-source-invalid` |
| Lane declaration | `checks.scripted` and `checks.judged` are both present. | `frontmatter-checks-lane-missing` (AC-2: "missing lane declaration") |
| Lane shape | A declared lane holds a list of criterion IDs, or is empty. A lane holding a scalar is a different defect from an absent lane and reports separately. | `frontmatter-checks-lane-invalid`, `frontmatter-criterion-id-invalid` |
| Lane overlap | No criterion ID appears in both lanes. | `lane-overlap` (AC-2: "criterion in both lanes") |
| Lane-manifest consistency | `scripts/checks.py`'s `IMPLEMENTED_CRITERIA` and `checks.scripted` name exactly the same set. | `scripted-check-undeclared` (AC-2: "undeclared scripted check"), `scripted-check-unimplemented` |
| Example envelopes | Every golden example's `expected_envelope` is contract-valid (`contract.validate.validate_document`) and names this skill. | `example-schema-invalid` (AC-2: "schema-invalid example"), `example-skill-mismatch`, `example-missing-field` |
| Example counts | >=3 golden, >=1 anti-example. | `examples-too-few-golden`, `examples-too-few-anti` |
| Trigger evals | Well-formed cases, >=20 total. | `trigger-case-malformed`, `trigger-evals-too-few` (AC-2: "under-20 trigger evals") |
| Trigger eval negatives | >=3 negatives, >=3 of those cross-domain. | `trigger-evals-too-few-negatives`, `trigger-evals-too-few-cross-domain-negatives` |
| Paraphrase heuristic | No quoted span over 25 words anywhere in `references/*.md`; zero quotation marks in any criterion table's Operationalization column. | `paraphrase-quote-too-long`, `paraphrase-operationalization-quoted`, `references-criterion-table-missing` |
| SKILL.md length | Under 500 lines. | `skill-md-too-long` |
| Test module names | Every `scripts/tests/test_*.py` basename ends with the skill's domain, so two skills cannot collide at pytest collection. | `checks-py-test-module-name` |
| `scripts/tests/` | Exists, has at least one test module, and passes under `python -m pytest`. | `checks-py-tests-missing`, `checks-py-pytest-failed` |

Two description checks are reported as **warnings** and do not fail the run:

- `description-quality-advisory` - the description uses none of the everyday trigger phrasings
  (review, feedback, second opinion, red-line, quality check, critique).
- `description-missing-use-when-advisory` - the description has no explicit use-when clause, which
  caps its U5 score at 0.65, below the 0.7 AC-6 requires. See "The four rules that decide the score".

Both are cheap, template-local sanity checks, explicitly **not** the family's U5 description-quality
scorer that S-04 spec AC-6 measures against (that scorer lives in the sibling `agent-skills-toolkit`
repository and runs as part of `node scripts/check.mjs`, per `AGENTS.md`, "Checks"; wrapping the
toolkit rather than vendoring its checks is [ADR 0011](decisions/0011-gate-wiring-toolkit-wrapper.md)).
A skill that passes `skill-selftest.py` cleanly has not yet been scored on U5; run the family gate for
that. Clearing the second warning is necessary for a passing U5 score and nowhere near sufficient.

### What it does not check

Body-content conformance to the "Required structure" list above (four-pass protocol present, contract
referenced, delegation stanza present) is a structural requirement of this document, not a mechanical
check `skill-selftest.py` runs: verifying that prose actually says the right thing needs judgment, not
a keyword grep that would produce more false confidence than it removes. A pipeline agent is
responsible for following the "Required structure" section directly; a P2/P3 review pass is where a
missing or garbled protocol section actually gets caught. See "Ambiguities" in the S-04 build report
for the reasoning behind drawing this line here.

`skill-selftest.py` also does not run `scripts/checks.py` against a real artifact end to end (only its
own `scripts/tests/` suite, via pytest). Determinism across two live runs, and gate exit codes against
a real corpus artifact, are proven once in `skills/_shared/tests/test_runner.py` for the shared
runner every skill uses, and are exercised per-skill at P3 measurement time against the full corpus,
not by this self-test.

## Building a skill end to end

1. Create `skills/critique-<domain>/` with the six required paths (empty files are fine to start).
2. Write `SKILL.md`: frontmatter first (name, description, version, license, rubric_sources, checks),
   then the body in the required order, copying the four-pass and delegation blocks above verbatim
   and adapting only the criteria and domain nouns.
3. Write `references/<source-id>.md` per rubric source: the seven-column criterion table, one row per
   criterion in `checks.scripted` plus `checks.judged`, zero quotes in the Operationalization column.
4. Write `references/severity-anchors.md`.
5. Write `scripts/checks.py`: the bootstrap, `IMPLEMENTED_CRITERIA`, one `check_*` helper per
   scripted criterion (or one `check` folding them together), wired through `run_scripted_lane`.
6. Write `scripts/tests/test_checks_<domain>.py` (or one file per criterion, each domain-suffixed)
   covering every scripted check, plus an empty `scripts/tests/__init__.py`.
7. Write `evals/triggers.eval.json`: >=20 cases, >=3 negatives, >=3 cross-domain negatives.
8. Write >=3 `examples/golden-NN.json` and >=1 `examples/anti-NN.json`.
9. Write `bench/generator/domains/<domain>.py` per "Corpus module obligation" and register it.
10. Run `python scripts/skill-selftest.py skills/critique-<domain>` until it exits 0, warnings
    included. A warning does not fail the run, but `description-missing-use-when-advisory` predicts an
    AC-6 failure at step 13, so clear it here rather than there.
11. Run `python -m bench.generator validate --domain <domain>`, `build`, `verify`, `leak-check`.
12. Run `python -m pytest` from the repository root. `pytest.ini`'s `testpaths` already globs
    `skills/*/scripts/tests`, so no edit is needed there; what this step actually catches is a test
    module basename colliding with another skill's.
13. Run the family conformance gate, `npm run check` (`AGENTS.md`, "Checks"). This is where U4
    (`name-matches-dir`), U5 (description score, AC-6's 0.7 threshold), and U13 (skill registered in
    `library.json`) are decided; `skill-selftest.py` checks none of them the way the gate does.

## See also

- [`skills/_template-fixture/critique-toy/`](../../skills/_template-fixture/critique-toy/) - this
  document's own committed reference build, and
  [`skills/_shared/README.md`](../../skills/_shared/README.md) for the library it wires into.
- [`contract/README.md`](../../contract/README.md) - the frozen contract this template's output must
  satisfy.
- [`docs/explanation/methodology.md`](../explanation/methodology.md) - the constitution: gate, lanes,
  four-pass protocol, determinism, provenance.
- [`docs/reference/criterion-ids.md`](../reference/criterion-ids.md) - the criterion ID grammar and
  namespace registry.
- [`docs/reference/severity-scale.md`](../reference/severity-scale.md) - the shared severity scale.
- [`bench/generator/README.md`](../../bench/generator/README.md) - the corpus domain-plugin API.
- [S-04 spec](release-plans/plan_v0.1.0/S-04_skill-template/spec.md),
  [S-05 spec](release-plans/plan_v0.1.0/S-05_skills-slate/spec.md),
  [S-06 spec](release-plans/plan_v0.1.0/S-06_critic-subagent/spec.md) - the effort specs this
  document implements or feeds.

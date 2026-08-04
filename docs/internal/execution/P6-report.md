# P6 report: pre-merge completeness critique

**Pass:** P6, the last automated gate before a human merges `build/v0.1.0`, tags `v0.1.0`, and
pushes.
**Date:** 2026-08-03.
**Branch:** `build/v0.1.0` (verified with `git branch --show-current`).
**Head at review time:** `44c2826` ("P6 docs and hygiene: family README, diagrams, governance,
release notes").
**Scope of writes:** this file only, plus one commit. No source file, generated file, or FROZEN file
was edited by this pass. One byproduct (`RELEASE_BODY.md`, written by the notes extractor while
testing it) was deleted after verification; the tree was clean before and after.

## Summary

**Merge-ready: yes, with three fix-before-tag items.** Every release-readiness check passes, and the
honesty sweep, the check that matters most for this repository, comes back clean at the level it was
asked about: the retracted survey claim is gone from every live claim, and every numeric claim I
spot-checked in `README.md` and `RELEASE-NOTES.md` resolves to `bench/results/results.json` or to a
source that names itself as a derived cut.

What does not hold up is a narrower band of claims about the repository's own machinery. Three
findings, none of which touch a measured number, all of which a hostile reader can falsify with one
command or one click:

1. `INDEX.md` ships seven links to paths that do not exist in this repository.
2. The `unit-node` CI job runs zero tests and cannot fail.
3. The most prominent Mermaid diagram in `README.md` has no plain-text alternative, in a repository
   that ships a WCAG skill, and the commit that added it says otherwise.

None of the three is a reason to hold v0.1.0. Two of the three are one-line fixes; the third needs a
paragraph. All three are cheaper to fix before the tag than to explain after it.

## Verdicts with evidence

Every command below was run from `E:/Projects/product-on-purpose/critique-skills` on branch
`build/v0.1.0` during this pass. Nothing in this section is quoted from a prior report.

### 1. Release readiness: PASS

| Check | Command | Result |
|---|---|---|
| Version agreement | `node scripts/check-release-versions.mjs v0.1.0` | **passed**; `package.json`, `library.json`, `.claude-plugin/plugin.json` all `0.1.0` |
| Notes extractor | `node scripts/extract-release-notes.mjs v0.1.0` | **ok: wrote 75 line(s) for 0.1.0**; content matches `RELEASE-NOTES.md`'s `## 0.1.0` section exactly |
| Conformance gate | `node scripts/check.mjs` | **0 error(s), 0 warning(s)**; Tier: Convergent (Advanced blocked: 4 issues) |
| Python suite | `python -m pytest -q` | **784 passed** in 9.42s, matching the `Tests: 784` badge line in `README.md` |
| Envelope validation | `npm run validate:envelopes` | **502 file(s) valid** |
| Bench table drift | `python -m bench.report table --results bench/results/results.json --check` | **no drift** |
| Skill catalog drift | `node scripts/gen-readme-catalog.mjs --check` | **matches** `library.json` + `SKILL.md` frontmatter |
| INDEX drift | `node scripts/gen-index.mjs --check` | **matches** `library.json` + component frontmatter |
| Manifest drift (aggregate) | `node scripts/gen-plugin-manifest.mjs --check` | **matches**; `AGENTS.md` documents all 7 `ci.yml` commands |
| Dash sweep | codepoint scan over `git ls-files` | **1,100 tracked files, zero U+2014 / U+2013** |

`CHANGELOG.md` carries a dated `## [0.1.0] - 2026-08-01` section with Added / Changed / Fixed
subsections. `RELEASE-NOTES.md` carries a distinct, curated `## 0.1.0 - 2026-08-01` entry that is
narrative rather than a changelog restatement; the two do not duplicate each other.

The four remaining above-tier gate issues are exactly what the integrator reported, and I confirmed
the diagnosis rather than taking it: `../agent-skills-toolkit/scripts/lib/fs-utils.mjs` line 14
defines `SKIP_DIRS` as `["node_modules", ".git", ".memsearch", "_local", "_LOCAL",
"_agent-context", "dist", ".astro"]`, with no `__pycache__` and no `.pytest_cache`. Three of the
four issues follow directly from that omission and recur on every `pytest` run. The fourth is the
Gold-tier architecture doc pair, correctly out of scope. All four are informational and cannot
affect the exit code.

### 2. Honesty sweep: PASS, with one named traceability nuance

**The retracted survey claim.** A grep across every tracked file for `40[ -]+framework(s)`,
`13[ -]+domain(s)`, and `survey` returns **zero live claims**. The five remaining hits are all
retrospective, and each names the claim as retracted: `CHANGELOG.md` line 110 (recording the
correction), ADR 0029 (methodology survey claim correction) lines 7 and 45, and the P4 and P5
execution reports. `docs/explanation/methodology.md`, the FROZEN file where the claim used to live,
now reads at line 62 "No completed candidate survey exists yet to reconcile it against; a
critique-framework survey is a tracked v0.2 deliverable, not a document already in hand", and
repeats the point at line 370. Correct, and correctly not re-edited by this pass.

**Numeric spot-checks.** I loaded `bench/results/results.json` (26 entries, run set
`p3-2026-07-31-plus-cal1-2026-08-01`) and checked each claim against the entry it names. Eleven
checked, ten exact:

| Claim | Where | Source entry | Verdict |
|---|---|---|---|
| accessibility 0.1.1 location recall 0.988 / 0.965 vs baseline 0.376 / 0.776 | `RELEASE-NOTES.md` 24-25 | `recall_location` for 0.1.1 haiku/sonnet and `baseline-generic` | exact |
| accessibility 0.1.1 precision 0.875 / 0.672 vs 0.258 / 0.293 | `RELEASE-NOTES.md` 25 | `precision_location` | exact |
| docs "32 claims at 0.875 precision versus the baseline's 102 at 0.275" | `RELEASE-NOTES.md` 33-35 | `precision_location` numerator/denominator: skill 28/32, baseline 28/102 | exact, including both denominators |
| usability Sonnet "recall +0.028 at a small precision cost" | `RELEASE-NOTES.md` 32 | 0.857 vs 0.829 recall; 0.169 vs 0.181 precision | exact |
| argument "0.371 against the 0.309 stretch-gate floor", margin 0.062 | `RELEASE-NOTES.md` 39, 66-67 | `consistency` argument/haiku 0.371, clarity/haiku 0.309 | exact |
| microcopy 0.920 / 0.960 against 0.813 / 0.840 | `RELEASE-NOTES.md` 36-37 | `recall_location` | exact |
| accessibility 0.1.0 failure 0.176 / 0.306 vs 0.376 / 0.776 | `README.md` 213 | `recall_location` | exact |
| precision floor 0.155 | `README.md` 209 | accessibility 0.1.0 sonnet `precision` | exact |
| 502 run envelopes | `README.md` 18, 413, 455 | 462 files under `runs/` + 40 under `runs-cal1/` | exact |
| 96 criteria (42 scripted, 54 judged) | `README.md` 17, 207, 410 | summed from all six `SKILL.md` `checks:` blocks (13+9, 2+6, 15+8, 3+6, 6+8, 3+17) | exact |
| 23-artifact corpus | `README.md` 413 | `bench/results/measurement-manifest.json` `artifact_count` | exact |

**The one orphan, named as instructed.** `README.md` line 209 cites "judged-lane consistency to
**0.150**". That figure is **not in `results.json`** and cannot be, because `results.json` carries no
lane-level breakdown (`grep` for `lane` and `judged` in the file: absent). It traces instead to
`bench/results/README.md` line 227 and line 379, where the source table is explicitly captioned
"**Derived cut, not carried in `results.json`**" with its own anchor. So the number is real, sourced,
and honestly labeled at its origin; what `README.md` does not say is that this particular figure
comes from a derived cut rather than the results file every other number on the page comes from.
That is a nuance, not a defect, and it is the only one of eleven checks that did not resolve directly
to `results.json`.

**Both required failures are still visible in the published narrative.** The consistency floor 0.309
appears three times in `README.md`: in the top NOTE callout at line 25 ("the consistency floor
calibrated to **0.309**, well below the 0.7 that was proposed before any data existed"), in the
narrative at line 209, and in the generated table at line 160. The accessibility 0.1.0 failure
appears as two rows in the generated baseline-comparison table (lines 129 and 131, both reading
`below baseline`) and as a full section, "The most instructive number is a failure", at lines
211-217, with both versions kept side by side. `RELEASE-NOTES.md` carries the same failure as its own
paragraph at lines 42-47. Neither was quietly softened.

**One internal inconsistency in that failure story.** `README.md` line 215 gives the post-fix Haiku
recall as **0.976**; `RELEASE-NOTES.md` lines 24 and 45 give it as **0.988**. Both are true: 0.976 is
criterion-level recall, 0.988 is location-level. But line 213 states the "before" at location level
(0.176 / 0.306) and line 215 states the "after" at criterion level, so a single before-and-after
comparison switches metrics mid-paragraph, and the two published documents disagree on the headline
number of the same story. The direction is under-claiming, which is the right direction to fail, and
`RELEASE-NOTES.md`'s own known-limitations bullet at line 69 calls it "the 0.176-to-0.988 gain". Not
a blocker; worth one word of qualification in `README.md` line 215.

### 3. New-content quality

**The five Mermaid diagrams.** Four earn their place; one earns it and then undercuts itself.

- `bench/README.md`, the benchmark pipeline. **Earns it, most clearly of the five.** The dotted
  `corpus -. "ground truth" .-> metrics` edge shows the thing prose keeps having to re-explain: the
  corpus is simultaneously the input to the runs and the ground truth those runs are scored against.
  No adjacent list states that. Followed by an "In text:" restatement.
- `docs/reference/critique-contract.md`, the two lanes merged into one envelope. **Earns it.**
  Readers routinely assume two lanes means two outputs; the diagram's join into a single `findings[]`
  array, with `lane` as the only discriminator, corrects that faster than the paragraph above it
  does. Followed by an "In text:" restatement.
- `examples/recipes/revision-loop.md`, the revision loop. **Earns it.** A loop with two distinct
  stop conditions (converged, or the three-iteration bound) is genuinely hard to hold in prose.
  Followed by an "In text:" restatement.
- `README.md`, the Two-Part Gate decision tree. **Earns it, marginally.** The bold sentence above it
  frames the gate as binary; the diagram is what surfaces BYOR as a third path. The "In text:"
  paragraph immediately below is close to a literal restatement, which reads as redundant until you
  notice it is the diagram's text alternative, and then it reads as correct practice.
- `README.md`, "How a critique runs". **Earns its place and then fails its own library's rubric.**
  The topology is real content: two lanes fanning out from one critic and converging into one
  envelope, which then forks to a human and to a CI gate. The five bold paragraphs beneath it state
  none of that shape. But this is the only one of the five diagrams with **no plain-text
  restatement**, in the front section of the most-read file, in a repository shipping a WCAG 2.2 AA
  skill, where a GitHub-rendered Mermaid block reaches a screen reader as nothing at all. Two smaller
  problems ride along: the `critique-critic` node uses decision-diamond shape for a node with two
  unconditional outputs, and the diagram puts the critic on the only path, while the prose directly
  beneath correctly hedges it as "where a subagent tool is available".

  The P6 commit message states that the new diagrams are "each followed by a one-line plain-text
  summary" and describes the README additions as "x2 additions net one new". Both halves are wrong:
  counting mermaid fences in the pre-P6 README (`git show 7a0875c:README.md`, grep for the mermaid
  fence) returns **0**, so both README diagrams are new in this pass, and one of them has no summary.

  Credit where due: the shared color palette across all five diagrams is Tailwind 800-on-100 pairs
  throughout, which clears WCAG AA contrast comfortably, and no diagram encodes meaning in color
  alone. The palette was chosen carefully. The alt text was not.

**`CONTRIBUTING.md`, read as an outside contributor.** Good. It answers the three questions a
contributor actually has, in order: does my thing belong here (the Two-Part Gate, with the
methodology's rejection table linked), what will be checked and in what order (the seven-item review
list, with item 7 called out as the least negotiable), and what will get me rejected outright (the
paraphrase policy, stated as "rejected outright, not sent back for revision", which is the right
register for a copyright rule). It names the one non-obvious local prerequisite, the sibling
`agent-skills-toolkit` checkout, with the clone command. The four `methodology.md` anchors it links
resolve: `#2-the-two-part-gate`, `#11-provenance-and-intellectual-property`, and
`#12-contributing-a-skill` all match real `## ` headings.

Two nits. It says the generated markers live "in `README.md` and `bench/README.md`", but
`bench/README.md` carries only `bench-results`, not `skill-catalog`; true collectively, loose
individually. And it tells contributors to "run whichever [CI jobs] your change touches", which is
good advice that becomes actively misleading for `unit-node`. See finding 2 below.

**`SECURITY.md`, read as an outside contributor.** Strong, and unusually falsifiable for the genre.
I checked its four load-bearing factual claims rather than reading past them:

- "`skills/` and `contract/` contain none of those calls" (`subprocess`, network modules,
  `eval`/`exec`): **verified**, a grep for all of them across both trees returns nothing.
- "`package-lock.json`'s only package entry is this repository itself": **verified**, the lockfile
  has exactly one entry, `""`, with no dependencies.
- "`bench/run_bench.py` calls the Anthropic Messages API": **verified**, the file exists at that
  path.
- "Node carries zero [third-party dependencies]": **verified**, `package.json` declares no
  `dependencies` or `devDependencies`.

One gap. Both reporting channels it offers,
`https://github.com/product-on-purpose/critique-skills/security/advisories/new` and the issues URL,
404 for anyone outside this project while the repository is private. `README.md`, `QUICKSTART.md`,
and `RELEASE-NOTES.md` all now carry the pre-release caveat; `SECURITY.md` and `CONTRIBUTING.md`
("Open an issue") do not, so the two governance documents most likely to be read by someone who
wants to reach the maintainer are the two that silently do not work. One sentence each fixes it.

### 4. Other checks run this pass

- **Relative-link check across 148 markdown files** in `docs/`, `examples/`, `bench/`, `skills/`,
  `agents/`, `.github/`: one hit, a `(path)` placeholder inside `docs/internal/execution/P0-report.md`.
  Link hygiene in the shipping docs is excellent.
- **Relative-link check across the eight top-level documents**: seven hits, all in `INDEX.md`. See
  finding 1.
- **`examples/` envelopes**: all six validate (`python -m contract.validate examples/*/envelope.json`
  reports `valid` six times). `examples/README.md`'s "Honesty labeling, explained once" section is
  the strongest single piece of prose added in this pass; it separates bit-for-bit reproducible
  scripted output, curated-from-golden judged output, and authored illustration, and it repeats the
  distinction on each page rather than only in the index.
- **`QUICKSTART.md`'s central falsifiable claim**: the golden artifact at
  `skills/critique-clarity/examples/clarity-golden-01-passive-and-nominalization.md` hashes to
  `10e2c8bde7e7427efb74b6f306aa2f6630f8aef35cd145131ba5b6a5eaf3efa2`, exactly the value printed at
  `QUICKSTART.md` line 143, and `golden-01.json` carries F-001 through F-004 with the criteria,
  severities, and locations the tutorial's table promises.

## Hostile-reader points

The three weakest points in the repository as it now stands, ranked by how much damage an attack on
each would do.

### 1. `INDEX.md` asserts seven paths that do not exist

`INDEX.md` is linked from `README.md`'s repo-structure block as "Generated repo map (drift-checked)".
Its "Manifests" and "Documentation and governance" sections link seven paths, and **none of the seven
exists in this repository**:

`.codex-plugin/plugin.json` (described as "Codex native manifest (generated; do not hand-edit)",
though `library.json` declares `agent-targets: ["claude"]` only), `manifest.generated.json`,
`STANDARD.md` (described as "the Advanced Skill Library Standard (normative)", which lives in the
toolkit repo, where `README.md` correctly links it), `docs/internal/backlog/`,
`docs/internal/STATUS.md`, `agents/_chain-permitted.yaml`, and `templates/`.

Why this is the worst of the three: the failure is structurally invisible to CI. `gen-index.mjs
--check` compares the committed `INDEX.md` against what the generator would produce, and the
generator produces exactly this boilerplate, so the check passes and will always pass. The repository
cannot detect it with any command it currently runs. And it lands precisely on the trust claim this
library is built to make. `README.md` line 112 says the tables "are generated, unedited"; line 195
says "Nothing here is estimated, recalled, or asserted without a run that produced it". A reader who
clicks through from that page to a generated index and finds seven dead links is holding the exact
counterexample.

Mitigating: `scripts/gen-index.mjs` lines 18-25 document the limitation honestly in a source comment,
naming all seven paths and attributing them to the toolkit's generator rendering boilerplate written
for its own repo layout, per the wrap-do-not-vendor rule (ADR 0011, gate wiring as a toolkit
wrapper). That comment is the right call and it is where the fix belongs. But no reader of `INDEX.md`
sees it.

Not fixable from here without either an upstream change to the toolkit's `gen-index` generator or a
post-processing step in `scripts/gen-index.mjs`, and `INDEX.md` itself must not be hand-edited.
Reported, not patched.

### 2. The `unit-node` CI job runs zero tests and cannot fail

`npm test` resolves to `node --test`. Run from the repo root it reports `# tests 0 / # pass 0 /
# fail 0`. There is no `*.test.mjs`, `*.test.js`, `test-*.mjs`, or `test/` directory anywhere in the
tree; every test directory in the repo (`bench/*/tests/`, `contract/tests/`, `scripts/tests/`,
`skills/*/scripts/tests/`) is Python. `.github/workflows/ci.yml` lines 79-95 run `npm test` on two
Node versions, so `unit-node` reports green twice per run and has never had the ability to report
anything else.

Three documents advertise the job as real: `AGENTS.md` line 71 ("seven jobs, each a single command"),
`CHANGELOG.md` line 38 (enumerating `unit-node` among them), and `CONTRIBUTING.md` line 83, which
tells a contributor to "run whichever ones your change touches". A contributor who modifies
`scripts/gen-index.mjs`, `scripts/check-release-versions.mjs`, `scripts/lib/version-manifest.mjs`, or
`scripts/extract-release-notes.mjs` will follow that instruction, run `npm test`, see it pass, and
reasonably conclude their change is covered. It is not. The Node spine, five executable scripts plus
two library modules, has no unit tests at all; its only coverage is the smoke provided by the four
`--check` modes running in the `drift` job.

This is the sharpest available attack on the repository's measurement ethos, because the ethos is the
product. The library's central argument is that an unmeasured claim is a draft, not a contribution
(`CONTRIBUTING.md` item 7, quoting methodology Section 12). A CI job that measures nothing and
reports success is that same failure mode, in the repository's own infrastructure.

**Previously named.** `P5-report.md` recorded it verbatim: "`node --test` was also run for
completeness (not part of the specified suite): 0 tests found, no `*.test.mjs`/`*.test.js` files
exist in the repo, which is the expected, pre-existing state, not a regression from this pass."
Accurate, and it does not make the job less vacuous.

### 3. The README's flagship diagram has no text alternative

Covered in full under "New-content quality" above. In short: of five Mermaid diagrams added in this
pass, four carry an "In text:" restatement and the fifth, the one in `README.md`'s "How a critique
runs" section, does not. GitHub renders a Mermaid block as an image with no alt text, so the four
restatements are the only thing standing between these diagrams and total inaccessibility, and the
most prominent diagram in the repository is the one missing it. The library ships
`critique-accessibility`, whose criteria include `WCAG-1.1.1`. The P6 commit message asserts every new
diagram has a summary, and that both README diagrams are not both new; counting mermaid fences in
`git show 7a0875c:README.md` returns 0, so both are new and the assertion is wrong.

A hostile reader does not need to construct this argument. They need to run `critique-accessibility`
on the rendered README.

### Are the previously-named weak points addressed, or merely reworded?

**Addressed, genuinely, with one carved-out exception.** This is the third time the question has been
put in this build, and the honest answer splits three ways.

**The eight hostile-reader points from P5 were fixed, and I re-verified six of the eight against
primary sources rather than re-reading the prose that claims they were fixed:**

- The "all three core skills beat baseline on both pinned tiers" claim: `CHANGELOG.md` lines 47-52
  now name which two do, say `critique-usability` qualifies on Haiku only, and say `critique-docs`
  ships on precision dominance at equal recall. I checked all four assertions against `results.json`;
  all four hold.
- The "lowest number is 0.309" claim: `README.md` line 209 now names 0.309 as the consistency floor
  specifically, states plainly that it is not the lowest published figure, and names 0.155 and 0.150
  as lower. I traced 0.155 to the accessibility 0.1.0 Sonnet entry and 0.150 to
  `bench/results/README.md` line 379. This is a substantive rewrite, not a hedge.
- The provenance sentence: `README.md` line 195 now reads `bench/results/runs*/` and names both
  `runs/` and `runs-cal1/` explicitly. Both directories exist and hold 462 and 40 envelopes.
- `critique-usability`'s narrow artifact claim: present at `README.md` line 242, outside the
  generated markers, and the catalog `--check` still reports no drift.
- The corpus count: `bench/results/measurement-manifest.json` reports `artifact_count: 23`, matching
  the corrected prose.
- The front-page table ordering and the recall-only verdict bug: the location-level table now runs
  first at `README.md` line 127, and `critique-usability` / Sonnet reads `no pass on this tier
  (qualifies via haiku)` rather than the old recall-only "beats baseline". Both are generated output,
  so the generator was actually changed.

**The P5 open items were carried forward, not closed, and two are now on their third pass unaddressed:**
`node --test` finding zero tests (named in P5, still zero, promoted to a top-three finding above) and
`rc-handover.md` not existing in the repository. On the second: commit `f3e6f61` ("P5 close: S-08
fulfilled, RC handover delivered") states the handover "exist[s] in `_local/initial-plan/` (gitignored
by design)". `git ls-files | grep -i handover` returns nothing. The handover is real but
machine-local, so it does not travel with the branch. Also still open from P5: the
`plugin-dev:plugin-validator` and `plugin-dev:skill-reviewer` runs that the release plan's B5 phase
names have never been performed; S-07 (CI pipeline) AC-6, CI runtime on GitHub-hosted runners, has
never been measured; and `plan_v0.1.0.md` lines 115-117 still mark R1 (consistency floor), R2
(usability artifact-type claim), and R3 (baseline model tiers) as `Open` with an `Updated` date of
2026-07-31, though all three are settled elsewhere.

**The three findings in this report are new, not reworded versions of anything.** None of `INDEX.md`'s
dead links, the missing diagram alternative, or the stale `CHANGELOG.md` tier count appears in any
prior execution report. Two of the three were created by this pass: the diagrams are new in `44c2826`,
and the tier-count staleness was introduced by `44c2826` dropping the count from 12 to 4 without
updating the sentence that quotes it.

So: the answer is not "reworded". The measured claims were genuinely repaired and the repairs hold
under independent re-verification. What has happened instead is that each pass has moved the weakest
point one layer outward, from the numbers, to the prose about the numbers, and now to the
infrastructure that supports the prose. That is the correct direction of travel, and it is also why
the same question keeps producing three answers.

## Must know before tagging

1. **`CHANGELOG.md` line 93 is stale and one command falsifies it.** It states that
   `node scripts/check.mjs` reports "Tier: Convergent (Advanced blocked: 12 issues)". It now reports
   4; the P6 commit message itself says "This drops the above-declared-tier issue count from 12 to
   4". The `CHANGELOG.md` sentence was not updated to match. This ships inside the release. Fix
   before tagging: change `12` to `4`, or drop the parenthetical count and keep "0 errors and 0
   warnings at the declared tier", which is the durable claim.
2. **Both dated sections read `2026-08-01`.** `CHANGELOG.md` line 8 and `RELEASE-NOTES.md` line 9 both
   date v0.1.0 to 2026-08-01. Substantive content landed on 2026-08-03 (`examples/`, `CONTRIBUTING.md`,
   `SECURITY.md`, five diagrams, eight folder READMEs). Decide deliberately: bump both to the actual
   tag date, or keep 2026-08-01 as the content-freeze date. Do not let the tag date and the section
   date diverge silently.
3. **`node scripts/extract-release-notes.mjs` writes `RELEASE_BODY.md` to the repo root, and that
   path is not gitignored.** `git check-ignore RELEASE_BODY.md` returns nothing. `AGENTS.md` line 123
   documents the command, so a maintainer following the documented release rehearsal dirties their
   tree with a file that is one `git add -A` away from being committed. P5 had to delete it manually;
   so did this pass. Harmless in CI, where `release.yml` runs it on a throwaway checkout. One line in
   `.gitignore` closes it permanently.
4. **The RC handover does not travel with the branch.** It lives in `_local/initial-plan/`, which is
   gitignored. Anyone tagging from a different machine or a fresh clone has no handover document.
   Either accept that or copy the tagging-relevant parts into `docs/internal/` before the tag.
5. **The install paths still do not resolve, and that is now stated but not solved.** The repository
   is private, public `main` carries only an initial commit, and `critique-skills` is unlisted in the
   `product-on-purpose/agent-plugins` marketplace. `README.md` (IMPORTANT callout at line 74),
   `QUICKSTART.md` (lines 9-14), `RELEASE-NOTES.md` (line 79), and the "At a glance" table
   (`README.md` line 417) all say so plainly. The tag is safe; announcing the tag is not, until the
   push and the marketplace entry land.
6. **`SECURITY.md` and `CONTRIBUTING.md` carry no pre-release caveat.** Both point readers at
   `github.com/product-on-purpose/critique-skills` URLs (security advisories, new issue) that 404
   while the repository is private. These are the two documents a reader uses to reach the
   maintainer.
7. **`README.md`'s badge row still reads `status: initial release`** with no pre-release qualifier at
   the badge level. The qualifier is in the callout 13 lines below, which is close, but the badge is
   what a skimmer reads and what a screenshot crops to. The integrator reported this as knowingly
   unfixed; I agree it is not a blocker and disagree that changing it is scope creep. It is one URL.

## Open items

### Carry to v0.1.x

- **`INDEX.md`'s seven non-existent paths.** Fix upstream in the toolkit's `gen-index` generator so
  the "Manifests" and "Documentation and governance" sections derive from `ctx` instead of fixed
  boilerplate, or add a post-processing filter in `scripts/gen-index.mjs`. Do not hand-edit
  `INDEX.md`. Finding 1 above.
- **File the upstream `SKIP_DIRS` issue against `agent-skills-toolkit`.** Adding `__pycache__` and
  `.pytest_cache` to the set at `scripts/lib/fs-utils.mjs` line 14 clears three of the four remaining
  above-tier gate issues in this repo, and every other Python-bearing family plugin, permanently.
- **Add the missing plain-text restatement** under `README.md`'s "How a critique runs" diagram, and
  consider whether the `critique-critic` node should be a process box rather than a decision diamond.
  Finding 3 above.
- **Add `RELEASE_BODY.md` to `.gitignore`.** Must-know item 3.
- **Add a pre-release note to `SECURITY.md` and `CONTRIBUTING.md`.** Must-know item 6.
- **Reconcile `README.md` line 215's 0.976 with `RELEASE-NOTES.md`'s 0.988**, or label line 215's
  figure as criterion-level so the before-and-after does not switch metrics.
- **Update `plan_v0.1.0.md` lines 115-117**: R1 (consistency floor, settled by ADR 0022), R2
  (usability artifact-type claim, settled in `SKILL.md` and `README.md`), and R3 (baseline model
  tiers, settled and pinned throughout `bench/results/`) are all still marked `Open`. Carried from
  P5 unchanged.
- **Give the Node spine unit tests, or stop advertising `unit-node` as a job.** Either write
  `*.test.mjs` coverage for `scripts/lib/version-manifest.mjs`, `check-release-versions.mjs`, and
  `extract-release-notes.mjs`, or fold the `drift` job's `--check` runs into `unit-node` so the job
  name describes something real. Finding 2 above.
- **`.gitattributes` protects only `bench/corpus/**` with `-text`.** `core.autocrlf` is `true` on
  this machine, so a fresh Windows clone converts every other text file to CRLF, which invalidates the
  `artifact_sha256` values recorded in the 29 `skills/*/examples/golden-*.json` fixtures. Nothing
  currently verifies those hashes, so nothing breaks today; the load-bearing case, the bench corpus,
  is correctly protected. Widen the rule before anything starts checking skill-example hashes.

### Carry to v0.2

- **Run the two named external validators**, `plugin-dev:plugin-validator` and
  `plugin-dev:skill-reviewer`, which the release plan's B5 phase names and which have never been run.
  Carried from P5.
- **Measure CI runtime on GitHub-hosted runners** (S-07, the CI pipeline spec, AC-6). Never measured.
  Carried from P5.
- **Gold tier**: the `architecture-overview` / `architecture-detailed` doc pair (R-CONTENT-4, gate
  G10). Deliberately out of scope for v0.1.0 and correctly left undone.
- **Golden-envelope run metadata is authored, and nothing says so.** Every
  `skills/*/examples/golden-*.json` and every `examples/*/envelope.json` carries
  `"model": "claude-sonnet-4-5-20250929"` and a specific `timestamp`, for envelopes that were not
  produced by a live call to that model (the scripted findings are regenerated from `checks.py` per
  the P3 calibration report; the `run` block matches the illustrative envelope in `methodology.md`
  line 176). That model is also not one of the two pinned benchmark tiers, so the published
  performance figures do not describe it. `examples/README.md` labels lanes scrupulously but says
  nothing about the `run` block. Either label the run metadata as illustrative or regenerate the
  fixtures from real calls.
- **Human acceptance data.** Disposition-based acceptance rate remains a v0.2 measure, correctly
  stated as absent in `RELEASE-NOTES.md`.
- **`results.json` cannot say which run set an entry came from**, and scoring `bench/results/runs`
  without excluding `runs/steering/` silently changes the `critique-clarity` / Sonnet numbers. Both
  documented in `bench/results/README.md`'s known-issues section. Carried from P5.

## Recommendation

**Merge.** Then fix must-know items 1, 3, and 7, plus the missing diagram restatement, as a single
small commit before tagging; each is one line or one paragraph, and each is a thing a hostile reader
would otherwise find first. Item 2, the release date, is a decision rather than a fix and should be
made deliberately at tag time. `INDEX.md` and `unit-node` are v0.1.x work, not tag blockers.

The measured claims in this repository hold up. I checked eleven of them against the run data and ten
resolved exactly, with the eleventh honestly labeled as a derived cut at its source. The retracted
survey claim is gone. The failure the library is proudest of publishing is still published. What
needs attention now is a layer out from the numbers: the repository's claims about its own tooling.

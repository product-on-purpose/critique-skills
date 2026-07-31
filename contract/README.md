# The critique contract

`critique-contract.schema.json` is the machine-parseable interface every part of this library produces or consumes. Skills emit findings into it, the critic subagent emits envelopes of it, the bench computes recall and consistency from it, CI validates it, and `--gate` mode exits on it. It is JSON Schema draft 2020-12, contract version **1.0.0**.

**This schema and `docs/explanation/methodology.md` together govern every finding in the library.** The methodology is the constitution: it says what a finding must be. The schema is the enforceable subset: it says what a finding must look like. A finding that fails the schema is invalid. A finding that passes the schema and breaks a methodology field contract is still wrong, and the sections below name exactly which rules fall on which side of that line. Where the schema and the methodology disagree, the methodology is correct and the schema is a bug.

## Three document types

| Document | Definition | What it is |
|---|---|---|
| Finding | `#/$defs/finding` (anchor `#finding`) | One defect claim, one criterion, one location. |
| Run envelope | `#/$defs/envelope` (anchor `#envelope`) | One skill run against one artifact: `run`, `findings[]`, `summary`. |
| Disposition log | `#/$defs/dispositionLog` (anchor `#dispositionLog`) | A human's accept, reject, or defer decisions over one run's findings. |

Validating the file root dispatches on one key: a document carrying `dispositions` is validated as a disposition log, and every other object is validated as a run envelope. To validate a bare finding, reference `#/$defs/finding` directly.

## Finding

Required: `id`, `criterion`, `lane`, `severity`, `location`, `evidence`, `violation`, `fix`, `confidence`. Optional: `instances`, `rubric_source`, `selector`.

| Field | Shape | Notes |
|---|---|---|
| `id` | `F-` plus 1 to 6 digits | Unique within its envelope. Zero padding allowed (`F-007`). |
| `criterion` | criterion ID, see below | Its namespace must appear in `run.rubrics`. |
| `lane` | `scripted` or `judged` | Deterministic script, or model judgment. |
| `severity` | integer 0 to 4 | The single scale, all domains. See `docs/reference/severity-scale.md`. |
| `location` | free text, 1 to 400 chars | Specific enough to navigate to unaided. |
| `evidence` | free text, to 2000 chars | A quotation or a measurement, never a characterization. |
| `violation` | free text, to 1000 chars | Which part of the criterion was breached. |
| `fix` | free text, to 1000 chars | Actionable and specific. |
| `confidence` | `high`, `medium`, `low` | Forced to `high` when `lane` is `scripted`. |
| `instances` | array of `{location, selector?, evidence?}` | For a recurring breach. At least 2 entries, no duplicates. |
| `rubric_source` | `bundled` or `byor` | Absent means `bundled`. Forced to `byor` for a `BYOR-` criterion. |
| `selector` | object, reserved | Unvalidated in 1.x. Producers may write it; consumers must not read it. |

## Run envelope

`run` requires `skill`, `skill_version`, `contract_version`, `artifact`, `artifact_sha256`, `model`, `timestamp`, `rubrics`, and optionally carries `stripped_context`.

- `artifact` is a relative POSIX path. Absolute paths, drive letters, and backslashes are rejected so an envelope reads the same on any machine and carries no local filesystem layout.
- `timestamp` is RFC 3339 in UTC with a literal trailing `Z`. Other offsets are rejected so timestamps sort lexically.
- `rubrics` lists every criterion namespace the run drew on. A criterion's namespace is the text before its first hyphen: `WCAG-1.4.3` has namespace `WCAG`.
- `stripped_context` is the clean-context ledger: entries of `{kind, note}` recording framing that arrived with the artifact and was disregarded. Absence asserts nothing was stripped; an empty array is rejected.

`summary` requires `by_severity`, `suppressed_count`, `gate`, and `severity_3_threshold`. `by_severity` requires all five keys `"0"` through `"4"` and counts **every** finding the run produced, including the ones the output bound suppressed. `findings[]` carries only the emitted ones, so the sum of `by_severity` equals `len(findings)` plus `suppressed_count`. The gate reads `summary` and nothing else.

## Disposition log

`contract_version`, an `envelope` reference, and at least one entry of `{finding_id, disposition}` with optional `note`, `criterion`, and `decided_at`. The envelope reference requires `skill`, `artifact_sha256`, and `timestamp`, the composite key that identifies a run; optional `path` and `envelope_sha256` bind it to a stored file. Finding IDs are unique only within a run, so the reference is what makes the log resolvable at all.

## Criterion ID grammar

```
^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+(?:\.[A-Z0-9]+)*)+(?![\s\S])
```

Uppercase, namespaced, `SOURCE-CRITERION`. The source is a letter followed by letters and digits. The criterion is one or more hyphen-separated segments, each of which may carry dot-separated parts so upstream numbering survives verbatim.

Accepted: `NNG-H4`, `WCAG-1.4.3`, `PLAIN-ACTIVE`, `TOULMIN-WARRANT`, `PYRAMID-MECE`, `DIATAXIS-MODE`, `AE-TITLE`, `NNG-EM-CONSTRUCTIVE`, `BYOR-BRAND-VOICE`.
Rejected: `nng-h4`, `WCAG`, `WCAG-`, `-H4`, `WCAG--1`, `WCAG-1.`, `WCAG_1`, `W CAG-1`.

The trailing `(?![\s\S])` is an end-of-input assertion, used in place of `$` throughout the schema. Python's `re` treats `$` as matching before a trailing newline, so `"WCAG-1.4.3\n"` would pass a `$`-anchored pattern in the Python validator while failing in an ECMA-262 one. The lookahead behaves identically in both.

## No em dash, no en dash

Every prose field rejects U+2014 EM DASH and U+2013 EN DASH anywhere in the string, by pattern. House style is enforced at the contract boundary because that is the cheapest single enforcement point: one rule, one place, every skill. Use `" - "`, a comma, or a colon; numeric ranges use a plain hyphen. Prose fields must also be non-empty and carry no leading or trailing whitespace.

A pattern reaches only the fields the schema types, which left `selector` as a way in, for keys as much as for values. Validator rule 9 closes it by testing every string in the parsed document instead, so the two defences overlap on prose fields and only the validator covers the reserved object.

## Gate exit codes

`--gate` computes an exit code from `summary` alone. The effective severity-3 threshold is the `--threshold` argument when given, and `summary.severity_3_threshold` otherwise. Default threshold is 0.

| Exit | Condition |
|---|---|
| 0 | Clean: no severity 4, and severity-3 count at or below the threshold. |
| 1 | Any severity 4. |
| 2 | Severity-3 count above the threshold. |
| 3 | Input is not a contract-valid document. |
| 4 | Usage error: bad arguments, unreadable or unparseable file. |

Exit 1 takes precedence over exit 2. Codes 3 and 4 exist so a malformed envelope can never be mistaken for a passing gate. Without `--gate`, the CLI exits 0 when the document is valid and 1 when it is not. A negative `--threshold` is a usage error, not a stricter setting: `severity_3_threshold` is a count with a minimum of 0, and a negative value would fail a run with no severity-3 findings at all. A valid document with no `summary`, which is to say a disposition log, is also a usage error under `--gate`, because no gate verdict exists to report and reporting 0 would read as a pass.

**Set `--threshold` when you gate on an envelope you did not produce.** The stored `severity_3_threshold` makes the exit code computable from `summary` alone, which is what it is for, but the producer of an envelope is the skill under test. Rule 11 warns when a run passes only because of its own declared threshold; `--strict` turns that warning into exit 3, and an explicit `--threshold` settles it outright.

## Rules the validator enforces beyond the schema

JSON Schema cannot express these, and the validator must implement all of them. Most are contract violations. Two, marked below, are reported as warnings and promoted to errors by `--strict`. Numbering is append-only: a rule keeps its number for the life of contract 1.x, so 8 stays where it is rather than being tidied into the warnings at the end.

1. **Finding IDs are unique** within an envelope.
2. **Histogram totals reconcile:** the sum of `summary.by_severity` equals `len(findings)` plus `summary.suppressed_count`.
3. **Severity 3 and 4 are never suppressed:** `by_severity["4"]` equals the number of emitted severity-4 findings, and `by_severity["3"]` equals the number of emitted severity-3 findings. For severities 0 to 2, the recorded count is at least the emitted count.
4. **The gate verdict is recomputed:** `summary.gate` must equal `fail` when `by_severity["4"]` is above zero or `by_severity["3"]` is above `summary.severity_3_threshold`, and `pass` otherwise.
5. **Rubrics cover the findings:** every finding's criterion namespace appears in `run.rubrics`.
6. **Integer fields are JSON integer literals.** JSON Schema's `integer` type accepts `3.0`; the contract does not. This covers `findings[].severity` and all three integer fields of the summary: `by_severity` values, `suppressed_count`, and `severity_3_threshold`. The summary is the load-bearing half. A histogram written `{"4": 0.0}` beside an emitted severity-4 finding is a value the schema admits, and a cross-check that read it as "not an integer, skip" would let that envelope pass the gate at exit 0. Rules 2, 3, and 4 therefore read integral floats as the numbers they are and rely on this rule to reject them separately, so no single mistake can switch a cross-check off.
7. **Disposition entries resolve:** whenever the referenced envelope is available, every `finding_id` exists in it, and a denormalized `criterion` matches that finding's criterion.
8. **Output bounding (warning):** at most five emitted findings below severity 3 (methodology section 7). This is a warning in contract 1.x because the methodology marks the bounding threshold, not the bounding principle, as provisional.
9. **No em dash and no en dash anywhere in the document.** The schema enforces this by pattern on every field it types as prose. This rule applies the same test to every string in the parsed document, object keys included, which is how it reaches `selector`, the one object the schema leaves unvalidated, and any field a later minor version adds. It is also the only one of these rules that applies to a bare finding.
10. **Timestamps name a real instant.** The schema pattern fixes the shape and the trailing `Z`; it cannot reject month 13 or 31 February. Checked on `run.timestamp`, `envelope.timestamp`, and `dispositions[].decided_at`. Second 60 is accepted, because RFC 3339 permits a leap second. A value whose shape is already wrong is left to the pattern rather than reported twice.
11. **Producer-declared threshold (warning):** the run passes only because of the `severity_3_threshold` it declares for itself, meaning `by_severity["4"]` is zero and `by_severity["3"]` is above zero but not above the declared threshold. Rules 2, 3, and 4 make the counts honest, but the counts are not the whole gate: the producer of an envelope is the skill under test, and nothing stops it carrying its own pass mark. A nonzero threshold is legitimate project policy, so this cannot be an error; it is surfaced so that a consumer gating on someone else's envelope knows to pass `--threshold` instead of trusting the stored value.

## What the schema does not check

These are methodology field contracts that no schema can express. They are review-lane rules, enforced by the skill's own instructions, by the critic subagent's protocol, and by human disposition. The full boundary, and the reasoning for accepting it rather than approximating it in code, is [0016 - Contract enforcement boundary](../docs/internal/decisions/0016-contract-enforcement-boundary.md); the reader-facing version is in [docs/reference/critique-contract.md](../docs/reference/critique-contract.md).

- Whether `evidence` is a quotation or a measurement rather than a characterization. "The contrast seems low" is schema-valid and contract-breaking.
- Whether `location` is navigable unaided. "Throughout the document" passes the pattern and fails the methodology.
- Whether `fix` is actionable. "Improve clarity" passes the pattern and fails the methodology.
- Whether `violation` names the breached part of the criterion rather than restating that something is bad.
- Whether a `scripted` finding really came from a deterministic script.
- Whether `stripped_context` records every piece of framing that was actually disregarded.
- Whether a finding's `severity` is the severity the artifact deserves. The rules above make the histogram agree with `findings[]`; nothing can make either agree with reality. A run that rates a catastrophe a 2 emits a valid envelope, and a run that rates everything a 4 does too.
- Whether a suppressed finding really was below severity 3. Suppressed findings appear only as counts, so their severities are the producer's claim. The arithmetic of rules 2 and 3 forces suppression to land in severities 0 to 2, which bounds the damage without verifying the claim.
- Whether a run in BYOR mode marked every finding `rubric_source: byor`. The schema forces it for a `BYOR-` criterion, but a user rubric may declare its own namespace, and no document records which mode a run was in.

## Versioning and extension

`contract_version` is owned by this file and versioned independently of the plugin, starting at 1.0.0 while the plugin is at 0.1.0. This file validates 1.x documents only. Patch is editorial, minor adds optional fields or relaxes constraints, major changes required fields or meanings and ships as a new file at a new path. Release version-bump tooling must never touch it. See [0013 - Contract versioning](../docs/internal/decisions/0013-contract-versioning-independent.md).

Every object in the schema sets `additionalProperties: false`, with exactly one exception: `finding.selector` and `instances[].selector`, an object reserved for a structured location pointer whose vocabulary is not settled. It is the only place unknown properties are accepted, no v0.1 consumer reads it, and the reasoning is in [0012 - Location grammar](../docs/internal/decisions/0012-location-grammar-freetext-plus-reserved-selector.md). Unvalidated is not unpoliced: validator rule 9 rejects an em dash or en dash inside it, keys included, which is the one contract rule that follows a document into territory the schema does not describe. The clean-context ledger's design is in [0014 - Stripped context](../docs/internal/decisions/0014-stripped-context-run-field.md).

## Checking the schema itself

From the repository root:

```
python -c "import json,jsonschema; jsonschema.Draft202012Validator.check_schema(json.load(open('contract/critique-contract.schema.json'))); print('schema OK')"
```

Requires Python 3.12 and `jsonschema`. The document validator and its CLI (`contract/validate.py`, `python -m contract.validate <file> [--gate] [--threshold N] [--strict]`) implement the interface described above and ship with S-02 (critique-contract effort); this README is their specification.

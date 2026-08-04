# QUICKSTART

One path, no branches beyond how you installed: install, run one critique against a file, read
what comes back, record one decision on it. Five minutes, inside a single Claude Code session. No
separate API key: critique runs as a skill in the session you already have open.

## 1. Install

> [!IMPORTANT]
> **Pre-release: the commands below are not resolvable yet.** This repository is currently private
> and its public `main` branch has not received this release's content beyond an initial placeholder
> commit; it is also not yet listed in the `product-on-purpose/agent-plugins` marketplace registry.
> Both install paths described here will fail until that changes. If you already have direct access
> to this private repository, clone it and check out the release branch instead.

Two ways to get `critique-skills` in place, once published. The rest of this walkthrough assumes
the plugin path; a repo checkout is a clearly-labeled alternative, needed only if you want to run
the benchmark or the contract validator directly rather than through a skill invocation.

**As a Claude Code plugin (this walkthrough's main path):**

```
/plugin marketplace add product-on-purpose/agent-plugins
/plugin install critique-skills@product-on-purpose
```

**Alternative, a repo checkout** (for `bench/` reproduction or scripting `contract/validate.py`
directly):

```
git clone https://github.com/product-on-purpose/critique-skills.git
cd critique-skills
```

Wherever this walkthrough gives a path relative to the plugin's own files, a repo checkout already
has that path relative to its own root; the checkout-specific notes below say where that shortcut
applies.

**One prerequisite either way.** Step 4 runs `contract/validate.py` to check a disposition log; its
only runtime dependency is `jsonschema`, and `/plugin install` does not install it, that command
sets up the skill, not a Python environment for it. Install it once:

```
pip install "jsonschema>=4.20,<5"
```

(`python -m pip install "jsonschema>=4.20,<5"` if `pip` is not directly on your PATH.)

## 2. Run one critique

The bundled example is
[`skills/critique-clarity/examples/clarity-golden-01-passive-and-nominalization.md`](skills/critique-clarity/examples/clarity-golden-01-passive-and-nominalization.md):
two short paragraphs, two passive-voice sentences and one nominalization planted on purpose so
`critique-clarity` has something concrete to find. It ships in the repo specifically to be the
first thing you critique.

**Plugin install:** that path is relative to the plugin's own installed files, not your working
directory, so ask Claude to fetch it rather than typing the path yourself as if it were local:

> Copy `skills/critique-clarity/examples/clarity-golden-01-passive-and-nominalization.md` from the
> installed `critique-skills` plugin into this directory, then critique the copy for clarity.

Claude Code can read its own installed plugin files directly, typically cached locally under
`~/.claude/plugins/cache/product-on-purpose/critique-skills/` (the exact version-numbered folder
under it varies by release, which is exactly why this asks Claude to find the file rather than
naming that folder). If Claude cannot locate it from that description, ask it to list the plugin's
installed files first.

**Repo checkout:** the file is already at that path relative to your checkout's root; skip the copy
and ask directly:

> Critique `skills/critique-clarity/examples/clarity-golden-01-passive-and-nominalization.md` for
> clarity.

`critique-clarity`'s own description names "review," "feedback," "clarity," and "prose document,"
so a request like either one above triggers it without naming the skill directly. If nothing
triggers, ask explicitly: "Use critique-clarity on that file."

## 3. Read the envelope

What comes back is one contract-valid run envelope, not a paragraph of prose. It has exactly three
parts:

- **`run`** - which skill ran, which version, which model, the artifact's own `artifact_sha256`,
  and when.
- **`findings`** - one structured record per defect: a criterion ID, a `lane` (`scripted` or
  `judged`), a `severity` from 0 to 4, a `location` you can navigate to unaided, `evidence` quoted
  or measured from the artifact, the `violation`, a `fix`, and a `confidence`.
- **`summary`** - counts by severity, how many findings were suppressed below the output bound,
  and a `gate` verdict (`pass` or `fail`).

On this example, expect four findings, all severity 2, `gate: pass` (nothing reaches severity 3),
along the lines of:

| id | criterion | severity | location |
|---|---|---|---|
| F-001 | `PLAIN-ACTIVE` | 2 | Current Status, paragraph 1 |
| F-002 | `PLAIN-ACTIVE` | 2 | Current Status, paragraph 1 |
| F-003 | `PLAIN-NOMINALIZATION` | 2 | Current Status, paragraph 2 |
| F-004 | `PLAIN-TRANSITIONS` | 2 | Current Status, paragraph 2 |

One finding in full, so you can see every field at once:

```json
{
  "id": "F-001",
  "criterion": "PLAIN-ACTIVE",
  "lane": "scripted",
  "severity": 2,
  "location": "Current Status, paragraph 1",
  "evidence": "The vendor contract was reviewed by the finance team last quarter.",
  "violation": "The sentence uses a be-verb plus past-participle passive construction in a context where the actor is recoverable and worth naming directly.",
  "fix": "Rewrite the sentence in active voice, naming the actor that performs the action.",
  "confidence": "high"
}
```

Your run's exact wording may not match this one letter for letter (a fresh judged-lane pass can
phrase a violation or a fix slightly differently), but which criteria the four findings sit under,
and `gate: pass`, should not vary. If your result differs in kind rather than in wording, that
itself is worth noting: `bench/results/README.md` publishes exactly how much this skill's output
varies run to run, and it is not zero. The full committed reference is
[`skills/critique-clarity/examples/golden-01.json`](skills/critique-clarity/examples/golden-01.json).
The field contracts behind every one of these keys, what a schema can check and what only a human
reviewer can, are in `docs/reference/critique-contract.md`.

## 4. Record one disposition

Critique never edits your artifact. A human decides what happens to each finding: accept, reject,
or defer (`docs/explanation/methodology.md`, Section 10, "Human-in-the-loop by contract"). Pick
one finding, F-001 above, and record a decision on it. Full logging conventions, including where a
running log lives and how acceptance rate feeds back into the library, are in
`docs/how-to/dispositions.md`; the minimum a single decision needs is this shape, saved anywhere
convenient (`disposition.json` in your working directory is fine):

```json
{
  "contract_version": "1.0.0",
  "envelope": {
    "skill": "critique-clarity",
    "skill_version": "0.1.0",
    "artifact": "skills/critique-clarity/examples/clarity-golden-01-passive-and-nominalization.md",
    "artifact_sha256": "10e2c8bde7e7427efb74b6f306aa2f6630f8aef35cd145131ba5b6a5eaf3efa2",
    "timestamp": "2026-07-31T18:05:00Z"
  },
  "dispositions": [
    {
      "finding_id": "F-001",
      "criterion": "PLAIN-ACTIVE",
      "disposition": "accept",
      "note": "Confirmed passive construction with a recoverable actor; rewriting to active voice."
    }
  ]
}
```

Use your own run's values, not the ones above, for every field in `envelope`: `artifact_sha256` and
`timestamp` will differ from this reference run regardless of install path, and `artifact` itself
will differ too if you copied the example into a plugin-install working directory rather than
critiquing it at its repo-checkout path. The disposition log's `envelope` block has to name the
actual run it disposes findings from. Confirm the log itself is well-formed:

```
python -m contract.validate disposition.json
```

**Repo checkout:** run that command from the repo root; `contract` resolves with no extra setup.
**Plugin install:** `contract` is not on your Python path by default, since only the skill was
installed, not a package. Ask Claude to run the validator instead of invoking it yourself:

> Validate `disposition.json` against the critique contract, using `contract/validate.py` from the
> installed `critique-skills` plugin.

`valid` means the document holds together as a disposition log. It does not mean the disposition
you recorded was the right call; that judgment is yours, which is the whole point of Section 10.

That is the complete loop this library exists to support: critique, disposition. Nothing above
edited your document. Only you decided what changes.

Want more worked examples before pointing this at your own files? `examples/README.md` indexes six
skill walkthroughs and three cross-cutting recipes, organized by task.

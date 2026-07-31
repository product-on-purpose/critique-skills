"""critique-toy scripted lane: TOY-ACTIVE, TOY-HEDGE, TOY-ORPHAN.

Every criterion this domain defines is deterministically checkable, so
this is the whole scripted lane; there is no judged lane to merge. See
docs/internal/skill-template.md, "Wiring scripts/checks.py", for the
pattern this file follows, and bench/generator/domains/toy.py for the
closed vocabulary (HEDGES, PARTICIPLES) the two text checks below match
against, which is exactly why a fixed substring or prefix match is
deterministic and complete for this domain rather than a heuristic.
"""

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
IMPLEMENTED_CRITERIA = frozenset({"TOY-ACTIVE", "TOY-HEDGE", "TOY-ORPHAN"})

# The toy grammar's own closed hedge vocabulary (bench/generator/domains/
# toy.py, HEDGES), lowercased for a case-insensitive prefix match.
HEDGES = ("it may possibly be the case that", "it could perhaps be argued that")

# The toy grammar's own closed be-plus-participle passive vocabulary
# (bench/generator/domains/toy.py, PARTICIPLES.values()). The toy grammar
# never produces these phrases except by the TOY-ACTIVE injector, so a
# fixed substring match is deterministic and complete for this domain;
# see "Transforms operate on a grammar you own" in bench/generator/README.md.
PASSIVE_MARKERS = ("is reviewed", "is filed", "is closed", "is signed off on")

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _split_sentences(text):
    return [part for part in _SENTENCE_SPLIT_RE.split(text.strip()) if part]


def _parse_blocks(text):
    """A minimal markdown block parser scoped to what the toy grammar
    ever produces: ATX headings (one to six '#' characters, a space,
    then text) and paragraphs (contiguous non-blank, non-heading lines,
    joined with a single space). Blank lines separate blocks and are
    otherwise discarded."""
    blocks = []
    lines = text.splitlines()
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        heading_match = _HEADING_RE.match(line)
        if heading_match:
            blocks.append({
                "kind": "heading",
                "level": len(heading_match.group(1)),
                "text": heading_match.group(2).strip(),
                "line": i + 1,
            })
            i += 1
            continue
        start_line = i + 1
        para_lines = []
        while i < n and lines[i].strip() and not _HEADING_RE.match(lines[i]):
            para_lines.append(lines[i])
            i += 1
        blocks.append({
            "kind": "paragraph",
            "text": " ".join(para_lines).strip(),
            "line": start_line,
        })
    return blocks


def _check_active_and_hedge(blocks):
    """TOY-ACTIVE and TOY-HEDGE both look only at a paragraph's first
    sentence, which is where the toy domain's own injectors place both
    defects (bench/generator/domains/toy.py, inject_active, inject_hedge,
    both `sentence=1`)."""
    findings = []
    heading_text = None
    paragraph_number = 0
    for block in blocks:
        if block["kind"] == "heading":
            heading_text = block["text"]
            continue
        paragraph_number += 1
        sentences = _split_sentences(block["text"])
        if not sentences:
            continue
        first = sentences[0]
        lowered = first.strip().lower()
        location = (
            f"{heading_text}, paragraph {paragraph_number}, first sentence"
            if heading_text
            else f"paragraph {paragraph_number}, first sentence"
        )

        if any(lowered.startswith(hedge) for hedge in HEDGES):
            findings.append(
                RawFinding(
                    criterion="TOY-HEDGE",
                    severity=2,
                    location=location,
                    evidence=first,
                    violation=(
                        "A hedging phrase is stacked ahead of an otherwise direct statement, "
                        "with no stated reason for the qualification."
                    ),
                    fix="Delete the hedge and state the sentence directly.",
                )
            )

        if any(marker in first for marker in PASSIVE_MARKERS):
            findings.append(
                RawFinding(
                    criterion="TOY-ACTIVE",
                    severity=2,
                    location=location,
                    evidence=first,
                    violation=(
                        "The sentence is recast into a passive construction that deletes the "
                        "actor, where the toy grammar's active form would have named it directly."
                    ),
                    fix="Rewrite the sentence in active voice, naming the actor that performs the action.",
                )
            )
    return findings


def _check_orphan_headings(blocks):
    """A heading at level 2 or deeper is orphan when no paragraph block
    appears before the next heading of equal or higher level, or the end
    of the document. The document's own level-1 title (always the first
    block the toy grammar's compose() emits) is exempt: it is always
    immediately followed by the first section heading with nothing of
    its own beneath it, so checking it would flag every artifact,
    including every clean one."""
    findings = []
    for index, block in enumerate(blocks):
        if block["kind"] != "heading" or block["level"] <= 1:
            continue
        is_orphan = True
        for later in blocks[index + 1:]:
            if later["kind"] == "paragraph":
                is_orphan = False
                break
            if later["kind"] == "heading" and later["level"] <= block["level"]:
                break  # is_orphan stays True: another heading arrived first
        if is_orphan:
            findings.append(
                RawFinding(
                    criterion="TOY-ORPHAN",
                    severity=3,
                    location=f"the {block['text']} heading",
                    evidence=f"heading: {block['text']}",
                    violation=(
                        "No paragraph appears between this heading and the next heading of equal "
                        "or higher level, so the heading introduces no body."
                    ),
                    fix=f"Add a body paragraph under the {block['text']} heading, or remove the heading.",
                )
            )
    return findings


def check(artifact):
    """artifact: skills._shared.artifact.Artifact (artifact.path,
    artifact.text, artifact.sha256). Returns RawFindings, unranked and
    unbounded; run_scripted_lane does the rest."""
    blocks = _parse_blocks(artifact.text)
    findings = []
    findings.extend(_check_active_and_hedge(blocks))
    findings.extend(_check_orphan_headings(blocks))
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

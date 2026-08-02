#!/usr/bin/env python3
# what-it-is:   the S-04 skill-template self-test runner
# what-it-does: validates one skills/critique-<domain>/ directory against the template
#               contract (frontmatter, lanes, references, evals, examples, tests) and
#               exits non-zero on any breach
# why:          six skill pipelines build in parallel, so a machine-checked template
#               contract is the anti-drift mechanism keeping their output identical
# used-by:      P2 skill-pipeline agents, scripts/tests/test_skill_selftest.py,
#               scripts/tests/test_skills_conformance.py (runs this against every real
#               skills/critique-<domain>/ directory in CI), and the P3 conformance sweep
"""skill-selftest: the per-skill template-conformance validator.

See `docs/internal/skill-template.md`, section "Self-test", for the
frontmatter, references, evals, and examples formats this checks
against; that document is the specification and this file is its
implementation, so where the two disagree, the document is correct and
this file is a bug.

Usage:
    python scripts/skill-selftest.py <skill-dir>

Exit 0 when every check passes. Exit 1 when any check fails. Every
failure carries a distinct `rule` name (S-04 spec AC-2: each of the
five named failure modes, plus every other check here, must fail
distinctly rather than collapsing into one generic message), printed as
`[rule] path: message`.

This script deliberately depends on nothing beyond the Python 3.12
stdlib plus `contract.validate` (already a dependency of the repository
it is validating), matching the stdlib-preferred posture the rest of
this repository's Python tooling follows (docs/internal/decisions/
0009-python-node-toolchain-split.md). SKILL.md frontmatter is YAML in
name only: this file implements a small, deliberately restricted block
subset (mappings, sequences of scalars, sequences of flat mappings, no
anchors, no multi-line scalars, and no flow style beyond the bare `[]`
empty-sequence token) rather than depending on PyYAML, because that
subset is all six skills' frontmatter ever needs.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from contract.validate import validate_document  # noqa: E402

# --------------------------------------------------------------------------
# Tunable thresholds. Named here, once, so a rule's number and its
# rationale live next to each other rather than scattered through the
# checks below.
# --------------------------------------------------------------------------

SKILL_MD_MAX_LINES = 500  # S-04 spec, Non-Functional Requirements
TRIGGER_EVALS_MIN_CASES = 20  # S-04 spec, directory shape comment
TRIGGER_EVALS_MIN_NEGATIVES = 3
TRIGGER_EVALS_MIN_CROSS_DOMAIN_NEGATIVES = 3  # S-05 spec, Behavior/Examples
EXAMPLES_MIN_GOLDEN = 3  # S-04 spec, directory shape comment
EXAMPLES_MIN_ANTI = 1
GOLDEN_NOTE_MIN_LENGTH = 40  # characters; forces an actual explanation, not "ok"

# Paraphrase heuristic (S-04 spec AC-7, "implement as a documented
# heuristic"): a quoted span longer than this many words is treated as
# reproduced source text rather than a short anchor quote. This is an
# approximation, not a copyright detector; docs/internal/skill-template.md
# states its limits.
MAX_ANCHOR_QUOTE_WORDS = 25

CRITERION_ID_RE = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+(?:\.[A-Z0-9]+)*)+$")
SKILL_NAME_RE = re.compile(r"^critique-[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
OPERATIONALIZATION_VALUES = frozenset({"paraphrased", "open-standard", "byor"})
QUOTE_CHARS = ('"', "“", "”")


@dataclass(frozen=True)
class Issue:
    rule: str
    path: str
    message: str

    def __str__(self) -> str:
        location = self.path if self.path else "<root>"
        return f"[{self.rule}] {location}: {self.message}"


# --------------------------------------------------------------------------
# A minimal block-style frontmatter parser: mappings, sequences of
# scalars, sequences of flat mappings. No flow style except the bare
# empty-sequence token `[]`, no multi-line scalars (so no `>`/`|` block
# scalars), no anchors. This is the dialect docs/internal/skill-template.md
# mandates for SKILL.md frontmatter, not a general YAML parser.
# --------------------------------------------------------------------------


class FrontmatterError(Exception):
    """Raised when SKILL.md's frontmatter cannot be parsed at all."""


class BlockScalarError(FrontmatterError):
    """Raised when a value uses a YAML block-scalar indicator (`>`, `>-`,
    `|`, `|-`, and friends). General YAML allows these; this dialect
    deliberately does not, because a block scalar is a multi-line value
    and every value here is one line.

    It gets its own exception type, and its own `rule` name at the
    reporting layer, because the generic parse failure it would
    otherwise raise ("could not parse frontmatter past line N") points
    at the *continuation* line rather than the block-scalar indicator
    that caused it, which is actively misleading. This is the single
    most likely way to write invalid frontmatter, since folded scalars
    are how most YAML front matter in the wild wraps a long description.
    """


_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.\-]*):\s*(.*)$")

# The YAML block-scalar indicators: literal (`|`) and folded (`>`), each
# with an optional chomping modifier (`-`/`+`) and an optional explicit
# indentation digit.
_BLOCK_SCALAR_RE = re.compile(r"^[|>][-+]?\d?$")


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


class _Cursor:
    def __init__(self, lines: list[str]):
        self.lines = lines
        self.i = 0

    def peek(self) -> str | None:
        return self.lines[self.i] if self.i < len(self.lines) else None

    def peek_indent(self) -> int | None:
        line = self.peek()
        return None if line is None else _indent_of(line)

    def advance(self) -> str:
        line = self.lines[self.i]
        self.i += 1
        return line


def _parse_scalar(text: str) -> Any:
    text = text.strip()
    if _BLOCK_SCALAR_RE.match(text):
        raise BlockScalarError(
            f"block scalar '{text}' is not supported: every value in this frontmatter "
            "dialect is a single line. Put the value on one line, in double quotes if "
            "it contains a ': ' or a '#' (docs/internal/skill-template.md, "
            '"SKILL.md frontmatter" > "Format")'
        )
    if text in ("", "null", "~"):
        return None
    if text == "[]":
        # The one flow-style token this dialect accepts, because block
        # style has no way to write an empty sequence at all and a
        # legitimately empty lane (checks.judged on an all-scripted
        # skill) has to be writable. Non-empty flow sequences stay
        # unsupported: `[A, B]` falls through and parses as the literal
        # string "[A, B]", which then fails the criterion-ID grammar
        # loudly rather than silently looking like a list.
        return []
    if text in ("true", "True"):
        return True
    if text in ("false", "False"):
        return False
    if len(text) >= 2 and text.startswith('"') and text.endswith('"'):
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise FrontmatterError(f"invalid double-quoted scalar {text!r}: {exc}") from exc
    if len(text) >= 2 and text.startswith("'") and text.endswith("'"):
        return text[1:-1].replace("''", "'")
    return text


def _parse_node(cur: _Cursor, indent: int) -> Any:
    if cur.peek_indent() != indent:
        raise FrontmatterError(f"unexpected indentation at line {cur.i + 1}: {cur.peek()!r}")
    content = cur.peek()[indent:]  # type: ignore[index]
    if content.startswith("- "):
        return _parse_sequence(cur, indent)
    return _parse_mapping(cur, indent)


def _parse_mapping(cur: _Cursor, indent: int) -> dict[str, Any]:
    result: dict[str, Any] = {}
    while cur.peek() is not None and cur.peek_indent() == indent:
        content = cur.peek()[indent:]  # type: ignore[index]
        if content.startswith("- "):
            break
        match = _KEY_RE.match(content)
        if not match:
            raise FrontmatterError(f"expected 'key: value' at line {cur.i + 1}: {cur.peek()!r}")
        key, rest = match.group(1), match.group(2).strip()
        cur.advance()
        if rest == "":
            nested_indent = cur.peek_indent()
            if nested_indent is not None and nested_indent > indent:
                result[key] = _parse_node(cur, nested_indent)
            else:
                result[key] = None
        else:
            result[key] = _parse_scalar(rest)
    return result


def _parse_sequence(cur: _Cursor, indent: int) -> list[Any]:
    items: list[Any] = []
    while (
        cur.peek() is not None
        and cur.peek_indent() == indent
        and cur.peek()[indent:].startswith("- ")  # type: ignore[index]
    ):
        line = cur.advance()
        rest = line[indent:][2:]
        key_match = _KEY_RE.match(rest)
        if key_match:
            item_indent = indent + 2
            key, value_rest = key_match.group(1), key_match.group(2).strip()
            item: dict[str, Any] = {key: (_parse_scalar(value_rest) if value_rest else None)}
            item.update(_parse_mapping(cur, item_indent))
            items.append(item)
        elif rest.strip() == "":
            nested_indent = cur.peek_indent()
            if nested_indent is not None and nested_indent > indent:
                items.append(_parse_node(cur, nested_indent))
            else:
                items.append(None)
        else:
            items.append(_parse_scalar(rest.strip()))
    return items


def extract_frontmatter_block(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise FrontmatterError("SKILL.md must open with a '---' frontmatter delimiter on line 1")
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i])
    raise FrontmatterError("SKILL.md frontmatter has no closing '---' delimiter")


def parse_frontmatter(text: str) -> dict[str, Any]:
    block = extract_frontmatter_block(text)
    lines = [line for line in block.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    cur = _Cursor(lines)
    if not lines:
        return {}
    value = _parse_mapping(cur, 0)
    if cur.peek() is not None:
        raise FrontmatterError(f"could not parse frontmatter past line {cur.i + 1}")
    return value


# --------------------------------------------------------------------------
# Check 1: frontmatter contract
# --------------------------------------------------------------------------


def check_frontmatter(skill_dir: Path) -> tuple[dict[str, Any] | None, list[Issue]]:
    """Returns (frontmatter, issues). frontmatter is None only when it
    could not be parsed at all, in which case every other check that
    depends on it is skipped by the caller.
    """
    issues: list[Issue] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return None, [Issue("skill-md-missing", str(skill_md), "SKILL.md does not exist")]

    text = skill_md.read_text(encoding="utf-8")
    try:
        fm = parse_frontmatter(text)
    except BlockScalarError as exc:
        # Reported ahead of the generic parse failure, and under its own
        # rule name, because the generic message names the wrong line.
        return None, [Issue("frontmatter-block-scalar-unsupported", str(skill_md), str(exc))]
    except FrontmatterError as exc:
        return None, [Issue("frontmatter-unparseable", str(skill_md), str(exc))]

    required = ("name", "description", "version", "license", "rubric_sources", "checks")
    for key in required:
        if key not in fm or fm[key] in (None, ""):
            issues.append(Issue("frontmatter-missing-field", key, f"frontmatter is missing '{key}'"))

    name = fm.get("name")
    if isinstance(name, str) and name:
        if name != skill_dir.name:
            issues.append(
                Issue(
                    "frontmatter-name-mismatch",
                    "name",
                    f"frontmatter name '{name}' does not match directory name '{skill_dir.name}'",
                )
            )
        if not SKILL_NAME_RE.match(name):
            issues.append(
                Issue("frontmatter-name-invalid", "name", f"'{name}' does not match 'critique-<domain>'")
            )

    version = fm.get("version")
    if isinstance(version, str) and version and not SEMVER_RE.match(version):
        issues.append(Issue("frontmatter-version-invalid", "version", f"'{version}' is not semantic-version-shaped"))

    description = fm.get("description")
    if isinstance(description, str) and description and len(description) < 40:
        issues.append(
            Issue(
                "frontmatter-description-too-short",
                "description",
                "description is too short to name artifact types and everyday trigger phrasings",
            )
        )

    issues.extend(_check_rubric_sources(fm.get("rubric_sources")))
    issues.extend(_check_checks_lanes(fm.get("checks")))

    return fm, issues


def _check_rubric_sources(rubric_sources: Any) -> list[Issue]:
    issues: list[Issue] = []
    if rubric_sources is None:
        return issues
    if not isinstance(rubric_sources, list) or not rubric_sources:
        return [
            Issue(
                "frontmatter-rubric-sources-empty",
                "rubric_sources",
                "rubric_sources must be a non-empty list",
            )
        ]
    for index, entry in enumerate(rubric_sources):
        path = f"rubric_sources[{index}]"
        if not isinstance(entry, dict):
            issues.append(Issue("frontmatter-rubric-source-invalid", path, "entry is not a mapping"))
            continue
        for field_name in ("id", "citation", "accessed", "operationalization"):
            if not entry.get(field_name):
                issues.append(
                    Issue("frontmatter-rubric-source-invalid", path, f"missing or empty '{field_name}'")
                )
        operationalization = entry.get("operationalization")
        if operationalization is not None and operationalization not in OPERATIONALIZATION_VALUES:
            issues.append(
                Issue(
                    "frontmatter-rubric-source-invalid",
                    f"{path}.operationalization",
                    f"'{operationalization}' is not one of {sorted(OPERATIONALIZATION_VALUES)}",
                )
            )
    return issues


def _check_checks_lanes(checks: Any) -> list[Issue]:
    issues: list[Issue] = []
    if not isinstance(checks, dict) or "scripted" not in checks or "judged" not in checks:
        return [
            Issue(
                "frontmatter-checks-lane-missing",
                "checks",
                "frontmatter must declare both checks.scripted and checks.judged, "
                "each a list of criterion IDs (S-04 spec AC-2: 'missing lane declaration')",
            )
        ]

    # An empty lane is legitimate (a skill whose criteria are all
    # deterministic has nothing in checks.judged) and is written either
    # as `judged: []` or as `judged:` with nothing after it; both land
    # here as [] or None respectively. A lane holding a scalar is a
    # different defect from a lane that is absent, so it gets its own
    # rule rather than borrowing the "missing lane" one.
    lane_issues: list[Issue] = []
    for lane_name in ("scripted", "judged"):
        value = checks.get(lane_name)
        if value is not None and not isinstance(value, list):
            lane_issues.append(
                Issue(
                    "frontmatter-checks-lane-invalid",
                    f"checks.{lane_name}",
                    f"must be a list of criterion IDs (or empty), got {value!r}. "
                    "An empty lane is written 'judged: []' or 'judged:' with nothing after it; "
                    "a non-empty flow sequence like '[A, B]' is not supported by this dialect",
                )
            )
    if lane_issues:
        return lane_issues

    scripted = checks.get("scripted") or []
    judged = checks.get("judged") or []

    for lane_name, lane in (("scripted", scripted), ("judged", judged)):
        for index, criterion in enumerate(lane):
            if not isinstance(criterion, str) or not CRITERION_ID_RE.match(criterion):
                issues.append(
                    Issue(
                        "frontmatter-criterion-id-invalid",
                        f"checks.{lane_name}[{index}]",
                        f"{criterion!r} does not match the criterion ID grammar",
                    )
                )

    overlap = sorted(set(scripted) & set(judged))
    for criterion in overlap:
        issues.append(
            Issue(
                "lane-overlap",
                "checks",
                f"criterion '{criterion}' is declared in both checks.scripted and checks.judged "
                "(S-04 spec AC-2: 'criterion in both lanes')",
            )
        )

    if not scripted and not judged:
        issues.append(Issue("frontmatter-checks-empty", "checks", "checks.scripted and checks.judged are both empty"))

    return issues


# --------------------------------------------------------------------------
# Check 2: lane-manifest consistency against scripts/checks.py
# --------------------------------------------------------------------------


def check_lane_manifest_consistency(skill_dir: Path, frontmatter: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []

    # With no lane declaration to compare against, every criterion
    # checks.py implements would be reported "undeclared", burying the
    # one real defect under a pile of consequences of it. The missing
    # declaration is already reported by _check_checks_lanes; say it
    # once (S-04 spec AC-2: each failure mode fails distinctly).
    checks = frontmatter.get("checks")
    if not isinstance(checks, dict) or "scripted" not in checks:
        return []

    checks_py = skill_dir / "scripts" / "checks.py"
    if not checks_py.is_file():
        return [Issue("checks-py-missing", str(checks_py), "scripts/checks.py does not exist")]

    module, load_issue = _load_module(checks_py)
    if load_issue is not None:
        return [load_issue]

    implemented = getattr(module, "IMPLEMENTED_CRITERIA", None)
    if implemented is None:
        return [
            Issue(
                "checks-py-missing-implemented-criteria",
                str(checks_py),
                "scripts/checks.py must declare a module-level IMPLEMENTED_CRITERIA "
                "(an iterable of every criterion ID its scripted lane checks)",
            )
        ]
    implemented_set = set(implemented)

    checks = frontmatter.get("checks") or {}
    declared_scripted = set(checks.get("scripted") or []) if isinstance(checks, dict) else set()

    undeclared = sorted(implemented_set - declared_scripted)
    for criterion in undeclared:
        issues.append(
            Issue(
                "scripted-check-undeclared",
                criterion,
                f"scripts/checks.py implements '{criterion}' but checks.scripted does not declare it "
                "(S-04 spec AC-2: 'undeclared scripted check')",
            )
        )

    unimplemented = sorted(declared_scripted - implemented_set)
    for criterion in unimplemented:
        issues.append(
            Issue(
                "scripted-check-unimplemented",
                criterion,
                f"checks.scripted declares '{criterion}' but scripts/checks.py's "
                "IMPLEMENTED_CRITERIA does not include it",
            )
        )

    return issues


def _load_module(path: Path) -> tuple[Any, Issue | None]:
    module_name = f"_skill_selftest_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        return None, Issue("checks-py-import-error", str(path), "could not build an import spec")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001 - reporting any import-time failure is the point
        return None, Issue("checks-py-import-error", str(path), f"{type(exc).__name__}: {exc}")
    return module, None


# --------------------------------------------------------------------------
# Check 3: example envelopes
# --------------------------------------------------------------------------


def check_examples(skill_dir: Path, frontmatter: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    examples_dir = skill_dir / "examples"
    if not examples_dir.is_dir():
        return [Issue("examples-dir-missing", str(examples_dir), "examples/ does not exist")]

    files = sorted(examples_dir.glob("*.json"))
    golden_count = 0
    anti_count = 0
    skill_name = frontmatter.get("name")

    for path in files:
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(Issue("example-not-json", str(path), str(exc)))
            continue
        if not isinstance(doc, dict):
            issues.append(Issue("example-not-json", str(path), "top level must be a JSON object"))
            continue

        kind = doc.get("kind")
        if kind == "golden":
            golden_count += 1
            issues.extend(_check_golden_example(path, doc, skill_name))
        elif kind == "anti":
            anti_count += 1
            issues.extend(_check_anti_example(path, doc))
        else:
            issues.append(Issue("example-kind-invalid", str(path), f"'kind' must be 'golden' or 'anti', got {kind!r}"))

    if golden_count < EXAMPLES_MIN_GOLDEN:
        issues.append(
            Issue(
                "examples-too-few-golden",
                str(examples_dir),
                f"found {golden_count} golden example(s), need at least {EXAMPLES_MIN_GOLDEN}",
            )
        )
    if anti_count < EXAMPLES_MIN_ANTI:
        issues.append(
            Issue(
                "examples-too-few-anti",
                str(examples_dir),
                f"found {anti_count} anti-example(s), need at least {EXAMPLES_MIN_ANTI}",
            )
        )

    return issues


def _check_golden_example(path: Path, doc: dict[str, Any], skill_name: Any) -> list[Issue]:
    issues: list[Issue] = []
    for field_name in ("artifact", "expected_envelope", "note"):
        if not doc.get(field_name):
            issues.append(Issue("example-missing-field", f"{path}.{field_name}", f"golden example is missing '{field_name}'"))

    note = doc.get("note")
    if isinstance(note, str) and 0 < len(note) < GOLDEN_NOTE_MIN_LENGTH:
        issues.append(
            Issue(
                "example-note-too-short",
                f"{path}.note",
                f"note is {len(note)} characters, needs at least {GOLDEN_NOTE_MIN_LENGTH} "
                "to explain why the findings are correct",
            )
        )

    envelope = doc.get("expected_envelope")
    if isinstance(envelope, dict):
        result = validate_document(envelope)
        for error in result.errors:
            issues.append(
                Issue(
                    "example-schema-invalid",
                    f"{path}.expected_envelope.{error.path}",
                    str(error.message),
                )
            )
        run_skill = envelope.get("run", {}).get("skill") if isinstance(envelope.get("run"), dict) else None
        if skill_name and run_skill and run_skill != skill_name:
            issues.append(
                Issue(
                    "example-skill-mismatch",
                    f"{path}.expected_envelope.run.skill",
                    f"'{run_skill}' does not match frontmatter name '{skill_name}'",
                )
            )
    return issues


def _check_anti_example(path: Path, doc: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    for field_name in ("query", "note"):
        if not doc.get(field_name):
            issues.append(Issue("example-missing-field", f"{path}.{field_name}", f"anti-example is missing '{field_name}'"))
    return issues


# --------------------------------------------------------------------------
# Check 4: trigger evals
# --------------------------------------------------------------------------


def check_trigger_evals(skill_dir: Path, frontmatter: dict[str, Any]) -> list[Issue]:
    path = skill_dir / "evals" / "triggers.eval.json"
    if not path.is_file():
        return [Issue("trigger-evals-missing", str(path), "evals/triggers.eval.json does not exist")]

    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [Issue("trigger-evals-not-json", str(path), str(exc))]

    if not isinstance(doc, dict) or not isinstance(doc.get("cases"), list):
        return [Issue("trigger-evals-malformed", str(path), "expected a JSON object with a 'cases' array")]

    cases = doc["cases"]
    issues: list[Issue] = []
    skill_name = frontmatter.get("name")

    well_formed: list[dict[str, Any]] = []
    for index, case in enumerate(cases):
        case_path = f"cases[{index}]"
        if (
            not isinstance(case, dict)
            or not isinstance(case.get("query"), str)
            or not case.get("query")
            or not isinstance(case.get("should_trigger"), bool)
        ):
            issues.append(
                Issue(
                    "trigger-case-malformed",
                    case_path,
                    "each case needs a non-empty string 'query' and a boolean 'should_trigger'",
                )
            )
            continue
        well_formed.append(case)

    if len(cases) < TRIGGER_EVALS_MIN_CASES:
        issues.append(
            Issue(
                "trigger-evals-too-few",
                str(path),
                f"{len(cases)} case(s), need at least {TRIGGER_EVALS_MIN_CASES} "
                "(S-04 spec AC-2: 'under-20 trigger evals')",
            )
        )

    positives = [c for c in well_formed if c["should_trigger"] is True]
    negatives = [c for c in well_formed if c["should_trigger"] is False]

    if not positives:
        issues.append(Issue("trigger-evals-no-positive-case", str(path), "no case has should_trigger: true"))

    if len(negatives) < TRIGGER_EVALS_MIN_NEGATIVES:
        issues.append(
            Issue(
                "trigger-evals-too-few-negatives",
                str(path),
                f"{len(negatives)} negative case(s), need at least {TRIGGER_EVALS_MIN_NEGATIVES}",
            )
        )

    cross_domain_negatives = [
        c
        for c in negatives
        if isinstance(c.get("cross_domain"), str)
        and c["cross_domain"].startswith("critique-")
        and c["cross_domain"] != skill_name
    ]
    if len(cross_domain_negatives) < TRIGGER_EVALS_MIN_CROSS_DOMAIN_NEGATIVES:
        issues.append(
            Issue(
                "trigger-evals-too-few-cross-domain-negatives",
                str(path),
                f"{len(cross_domain_negatives)} negative case(s) name another skill in 'cross_domain', "
                f"need at least {TRIGGER_EVALS_MIN_CROSS_DOMAIN_NEGATIVES}",
            )
        )

    return issues


# --------------------------------------------------------------------------
# Check 5: paraphrase heuristic
# --------------------------------------------------------------------------


def _split_table_row(line: str) -> list[str]:
    trimmed = line.strip()
    if trimmed.startswith("|"):
        trimmed = trimmed[1:]
    if trimmed.endswith("|"):
        trimmed = trimmed[:-1]
    return [cell.strip() for cell in trimmed.split("|")]


def _find_markdown_tables(text: str) -> list[dict[str, Any]]:
    """Every pipe-table block in `text`: a header row, a '---'-style
    separator row, and the data rows that follow. Assumes no escaped
    pipes inside a cell, which the references table format never needs.
    """
    lines = text.splitlines()
    tables = []
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|") and i + 1 < len(lines):
            separator = lines[i + 1].strip()
            if re.fullmatch(r"\|?[\s:|-]+\|?", separator) and "-" in separator:
                header = _split_table_row(lines[i])
                rows = []
                j = i + 2
                while j < len(lines) and lines[j].lstrip().startswith("|"):
                    rows.append(_split_table_row(lines[j]))
                    j += 1
                tables.append({"header": header, "rows": rows, "line": i + 1})
                i = j
                continue
        i += 1
    return tables


def _quoted_spans(line: str) -> list[str]:
    spans = re.findall(r'"([^"]*)"', line)
    spans += re.findall(r"“([^”]*)”", line)
    return spans


def check_paraphrase_heuristic(skill_dir: Path) -> list[Issue]:
    """A documented approximation (S-04 spec AC-7), not a copyright
    detector: flags any quoted span longer than MAX_ANCHOR_QUOTE_WORDS
    words as exceeding a 'short anchor quote', and flags any quotation
    mark at all inside a criterion table's Operationalization column,
    since that column must be original paraphrase with zero quoted
    source text (see docs/internal/decisions/0006-copyright-paraphrase-
    policy.md).
    """
    references_dir = skill_dir / "references"
    if not references_dir.is_dir():
        return [Issue("references-dir-missing", str(references_dir), "references/ does not exist")]

    issues: list[Issue] = []
    for path in sorted(references_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for span in _quoted_spans(line):
                word_count = len(span.split())
                if word_count > MAX_ANCHOR_QUOTE_WORDS:
                    issues.append(
                        Issue(
                            "paraphrase-quote-too-long",
                            f"{path}:{line_number}",
                            f"quoted span is {word_count} words, exceeding the "
                            f"{MAX_ANCHOR_QUOTE_WORDS}-word short-anchor-quote limit",
                        )
                    )

        if path.name == "severity-anchors.md":
            continue

        tables = _find_markdown_tables(text)
        op_tables = [t for t in tables if any(h.lower() == "operationalization" for h in t["header"])]
        if not op_tables:
            issues.append(
                Issue(
                    "references-criterion-table-missing",
                    str(path),
                    "no criterion table with an 'Operationalization' column was found",
                )
            )
            continue

        for table in op_tables:
            header = [h.lower() for h in table["header"]]
            op_index = header.index("operationalization")
            id_index = header.index("id") if "id" in header else None
            for row in table["rows"]:
                if len(row) <= op_index:
                    continue
                cell = row[op_index]
                if any(q in cell for q in QUOTE_CHARS):
                    row_id = row[id_index] if id_index is not None and len(row) > id_index else "?"
                    issues.append(
                        Issue(
                            "paraphrase-operationalization-quoted",
                            f"{path} ({row_id})",
                            "the Operationalization column must be original paraphrase; "
                            "it contains a quotation mark",
                        )
                    )
    return issues


# --------------------------------------------------------------------------
# Check 6: SKILL.md length
# --------------------------------------------------------------------------


def check_skill_md_length(skill_dir: Path) -> list[Issue]:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return []  # already reported by check_frontmatter
    line_count = len(skill_md.read_text(encoding="utf-8").splitlines())
    if line_count > SKILL_MD_MAX_LINES:
        return [
            Issue(
                "skill-md-too-long",
                str(skill_md),
                f"{line_count} lines, exceeding the {SKILL_MD_MAX_LINES}-line limit",
            )
        ]
    return []


# --------------------------------------------------------------------------
# Check 7: pytest
# --------------------------------------------------------------------------


def check_test_module_names(skill_dir: Path) -> list[Issue]:
    """Every skill's `scripts/tests/` test module basename must end with
    `_<domain>`, so no two skills ship a module with the same basename.

    This is not style policing. Under pytest's default (prepend) import
    mode, two files both named `scripts/tests/test_checks.py` collide at
    collection time with "import file mismatch: imported module
    'test_checks' has this __file__ attribute ...", and the whole repo
    suite aborts with a collection error rather than a test failure. A
    skill directory cannot be a Python package (a hyphen is not a valid
    identifier), so `__init__.py` files do not disambiguate them either;
    a unique basename is the only fix that works, and it has to be
    enforced from inside one skill directory because that is all this
    self-test can see.
    """
    tests_dir = skill_dir / "scripts" / "tests"
    if not tests_dir.is_dir():
        return []  # reported by check_pytest
    domain_match = SKILL_NAME_RE.match(skill_dir.name)
    if not domain_match:
        return []  # the directory name itself is already being reported
    domain = skill_dir.name[len("critique-"):]
    suffix = f"_{domain.replace('-', '_')}"
    issues: list[Issue] = []
    for path in sorted(tests_dir.glob("test_*.py")):
        if not path.stem.endswith(suffix):
            issues.append(
                Issue(
                    "checks-py-test-module-name",
                    str(path),
                    f"test module basenames must end with '{suffix}' (so '{path.stem}{suffix}.py'): "
                    "two skills shipping the same basename abort the whole repository pytest run "
                    "with an import-file-mismatch collection error, not a test failure",
                )
            )
    return issues


def check_pytest(skill_dir: Path) -> list[Issue]:
    tests_dir = skill_dir / "scripts" / "tests"
    if not tests_dir.is_dir():
        return [Issue("checks-py-tests-missing", str(tests_dir), "scripts/tests/ does not exist")]
    test_files = list(tests_dir.glob("test_*.py"))
    if not test_files:
        return [Issue("checks-py-tests-missing", str(tests_dir), "scripts/tests/ has no test_*.py files")]

    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(tests_dir), "-q"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        tail = "\n".join(result.stdout.strip().splitlines()[-20:])
        return [Issue("checks-py-pytest-failed", str(tests_dir), tail or result.stderr.strip())]
    return []


# --------------------------------------------------------------------------
# Advisory (non-blocking) checks
# --------------------------------------------------------------------------

TRIGGER_PHRASES = (
    "review",
    "feedback",
    "second opinion",
    "red-line",
    "redline",
    "quality check",
    "critique",
)

# The family U5 scorer awards its single largest block of credit for an
# explicit use-when clause, and recognises it by a fixed set of openers.
# This is that opener set, not the scorer: matching one of these is
# necessary for a >= 0.7 U5 score (S-04 spec AC-6) but nowhere near
# sufficient, and the scorer itself stays in `agent-skills-toolkit`
# (docs/internal/decisions/0011-gate-wiring-toolkit-wrapper.md: wrap the
# toolkit, never vendor its checks). Kept here only so a pipeline agent
# learns about the miss from its own self-test rather than from a
# conformance-gate warning after the fact.
USE_WHEN_OPENERS = (
    "use when",
    "use this when",
    "use this skill when",
    "use whenever",
    "use this whenever",
    "use this skill whenever",
    "when the user",
    "whenever the user",
    "when you need",
    "for when",
    "if the user asks",
    "if the user mentions",
    "if the user wants",
    "if the user needs",
)


def check_description_quality_advisory(frontmatter: dict[str, Any]) -> list[Issue]:
    """Not the family's U5 description-quality scorer (that scorer lives
    in the sibling `agent-skills-toolkit` repository and runs as part of
    the family conformance gate, `node scripts/check.mjs`; S-04 spec
    AC-6 is measured there, not here). These are cheap, template-local,
    non-blocking sanity checks on the two things a critique-<domain>
    description most often gets wrong: no everyday trigger phrasing at
    all, and a trigger clause phrased as "Use for ..." rather than the
    "Use when ..." construction the U5 scorer recognises.
    """
    description = frontmatter.get("description")
    if not isinstance(description, str) or not description:
        return []
    lowered = description.lower()
    issues: list[Issue] = []
    if not any(phrase in lowered for phrase in TRIGGER_PHRASES):
        issues.append(
            Issue(
                "description-quality-advisory",
                "description",
                "description does not use any everyday trigger phrasing "
                f"({', '.join(TRIGGER_PHRASES)}); this is advisory, not a substitute "
                "for the family U5 scorer",
            )
        )
    if not any(opener in lowered for opener in USE_WHEN_OPENERS):
        issues.append(
            Issue(
                "description-missing-use-when-advisory",
                "description",
                "description has no explicit use-when clause; the family U5 scorer "
                "recognises only these openers, and a description without one caps out "
                "below the 0.7 the S-04 spec AC-6 requires: "
                f"{', '.join(repr(o) for o in USE_WHEN_OPENERS)}",
            )
        )
    return issues


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------


def run_selftest(skill_dir: Path) -> tuple[list[Issue], list[Issue]]:
    """Returns (errors, warnings). Only errors affect the exit code."""
    errors: list[Issue] = []
    warnings: list[Issue] = []

    frontmatter, frontmatter_issues = check_frontmatter(skill_dir)
    errors.extend(frontmatter_issues)

    if frontmatter is not None:
        errors.extend(check_lane_manifest_consistency(skill_dir, frontmatter))
        errors.extend(check_examples(skill_dir, frontmatter))
        errors.extend(check_trigger_evals(skill_dir, frontmatter))
        warnings.extend(check_description_quality_advisory(frontmatter))

    errors.extend(check_paraphrase_heuristic(skill_dir))
    errors.extend(check_skill_md_length(skill_dir))
    errors.extend(check_test_module_names(skill_dir))
    errors.extend(check_pytest(skill_dir))

    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python scripts/skill-selftest.py",
        description="Validate one skills/critique-<domain>/ directory against the S-04 skill template.",
    )
    parser.add_argument("skill_dir", help="Path to the skill directory, e.g. skills/critique-clarity")
    args = parser.parse_args(argv)

    skill_dir = Path(args.skill_dir)
    if not skill_dir.is_dir():
        print(f"usage error: '{skill_dir}' is not a directory", file=sys.stderr)
        return 1

    errors, warnings = run_selftest(skill_dir)

    for issue in errors:
        print(str(issue), file=sys.stderr)
    for issue in warnings:
        print(f"warning: {issue}", file=sys.stderr)

    if errors:
        print(f"skill-selftest: {len(errors)} error(s), {len(warnings)} warning(s). FAIL", file=sys.stderr)
        return 1

    print(f"skill-selftest: 0 errors, {len(warnings)} warning(s). PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

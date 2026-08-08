"""CLI: the bench.yml workflow_dispatch entry point (S-07 CI-pipeline spec), and the real
reproduction harness the P3 self-audit found missing (docs/internal/execution/P3-report.md,
"Provenance gap: no committed harness actually calls a live model or the critic subagent").

For a given (skill, artifact, tier, k) grid, this module:

1. Discovers the grid from what is actually declared: skills from library.json, artifacts from
   `bench/corpus/<domain>/*.manifest.json`, tiers from `bench/results/measurement-manifest.json`'s
   pinned `models` list (the same file ADR 0023 records the measurement basis in).
2. Runs the scripted lane locally, via each skill's own `scripts/checks.py`, exactly as
   `agents/critique-critic.md`'s Protocol section describes it.
3. Runs the judged lane against the Anthropic API (the `anthropic` package; see ADR 0025), with a
   system prompt assembled from the skill's `SKILL.md` and `references/*.md`, restricted to that
   skill's `checks.judged` criteria (the scripted criteria are already covered by step 2).
4. Merges both lanes into one pool and applies the skill's bounded-output rule over that combined
   pool, the same rule `skills/_shared/envelope.py` already implements for the scripted-only case
   (methodology section 7; `agents/critique-critic.md`, Protocol step 5).
5. Validates the assembled envelope against the contract before writing it, and never writes one
   that fails.
6. Runs the frozen baseline condition (`bench/baseline/prompt.txt` plus
   `bench/baseline/postprocess.py`) against the same artifacts and tiers, alongside every skill.
7. Scores the resulting run set with `bench/metrics`, writing a `results.schema.json`-valid
   `results.json`.

Existing envelopes under `bench/results/runs/` are immutable measurement evidence; this harness
never reads them and writing new ones is always to a caller-chosen `--out-dir`, never implied.

A live run reaches the model through the Claude Code CLI, not the Anthropic API, so it needs NO
API key: it authenticates from a Claude subscription, interactively on a workstation or via a
`claude setup-token` credential in CLAUDE_CODE_OAUTH_TOKEN where nobody is logged in (ADR 0030).
`--dry-run` validates inputs and plans the exact grid without calling any model or needing the CLI
at all (S-07 AC-3: "dry-run mode works without the secret").

Usage:
    python bench/run_bench.py [--skills all] [--k 5] [--tiers ""] [--dry-run]
    python bench/run_bench.py --skills critique-clarity --k 5 --out-dir /tmp/bench-run
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "library.json").is_file():
            return candidate
    raise RuntimeError("could not locate the repository root (no library.json found above this file)")


ROOT = _find_repo_root(Path(__file__).resolve())
# `python bench/run_bench.py`, the invocation bench.yml and this module's own docstring document,
# puts this file's own directory (bench/) on sys.path[0], not the repository root, so "bench" and
# "contract" and "skills" do not resolve as top-level packages without this. Matches the same
# bootstrap every skill's scripts/checks.py already carries, for the same reason.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bench.baseline.postprocess import BASELINE_SKILL, postprocess as baseline_postprocess  # noqa: E402
from bench.metrics.__main__ import ScoreError, build_results  # noqa: E402
from contract.validate import validate_document  # noqa: E402
from skills._shared.envelope import (  # noqa: E402
    CONTRACT_VERSION,
    build_summary,
    by_severity_histogram,
    rank_and_bound,
    to_finding_dict,
)
from skills._shared.findings import RawFinding  # noqa: E402

LIBRARY_JSON = ROOT / "library.json"
DEFAULT_CORPUS_DIR = ROOT / "bench" / "corpus"
DEFAULT_OUT_DIR = ROOT / "bench" / "results" / "runs"
DEFAULT_MANIFEST_PATH = ROOT / "bench" / "results" / "measurement-manifest.json"
BASELINE_PROMPT_PATH = ROOT / "bench" / "baseline" / "prompt.txt"
SEVERITY_SCALE_PATH = ROOT / "docs" / "reference" / "severity-scale.md"
DEFAULT_MAX_TOKENS = 8192


# ---------------------------------------------------------------------------
# Skill discovery and filtering (unchanged from the pre-harness stub)
# ---------------------------------------------------------------------------


def declared_skills() -> list[str]:
    """Skill names from library.json's components.skills, whatever shape each entry takes
    (a bare name, or an object carrying one). Returns [] if library.json is missing, unreadable,
    or declares none yet."""
    try:
        data = json.loads(LIBRARY_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"bench: cannot read {LIBRARY_JSON}: {exc}", file=sys.stderr)
        return []
    skills = data.get("components", {}).get("skills", [])
    return [s.get("name", s) if isinstance(s, dict) else s for s in skills]


def resolve_filter(skills: list[str], raw_filter: str) -> list[str]:
    """`raw_filter` is "all" (or blank) for every declared skill, else a comma-separated allowlist."""
    if raw_filter in ("", "all"):
        return skills
    wanted = {s.strip() for s in raw_filter.split(",") if s.strip()}
    return [s for s in skills if s in wanted]


# ---------------------------------------------------------------------------
# SKILL.md frontmatter: judged criteria, rubric namespaces, skill version
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_SCRIPTED_BLOCK_RE = re.compile(r"^  scripted:\n((?:    - .+\n?)+)", re.MULTILINE)
_JUDGED_BLOCK_RE = re.compile(r"^  judged:\n((?:    - .+\n?)+)", re.MULTILINE)
_VERSION_RE = re.compile(r"^version:\s*(\S+)\s*$", re.MULTILINE)


def _extract_list_block(body: str, pattern: re.Pattern[str]) -> list[str]:
    match = pattern.search(body)
    if not match:
        return []
    return [line.strip()[2:].strip() for line in match.group(1).splitlines() if line.strip().startswith("- ")]


def parse_skill_frontmatter(skill_md_text: str) -> dict[str, Any]:
    """A restricted parser for this repository's own SKILL.md frontmatter shape
    (docs/internal/skill-template.md): a YAML block delimited by '---' lines, with
    'checks: scripted: / judged:' as two-space-indented keys and their criterion ids as
    four-space '- ID' items, and a top-level 'version:' scalar. Not a general YAML parser; every
    SKILL.md in this repository is hand-written to exactly this shape (verified against all six
    launch skills), and this function raises rather than guess at a different one.

    `rubrics` is derived from the criterion IDs themselves, the text before each one's first
    hyphen (contract/critique-contract.schema.json, $defs/rubricNamespace's own definition), not
    from `rubric_sources[].id`: for critique-microcopy and critique-usability those two lists
    differ (rubric_sources carries "NNG-EM" or "NNG-HEURISTICS"/"NNG-SEVERITY", the actual
    namespace every criterion ID shares is "NNG"), and run.rubrics must be the namespace, or the
    validator's rubrics-cover-findings rule fails on every finding this harness emits.
    """
    match = _FRONTMATTER_RE.match(skill_md_text)
    if not match:
        raise ValueError("SKILL.md has no '---' delimited frontmatter block")
    body = match.group(1)
    scripted = _extract_list_block(body, _SCRIPTED_BLOCK_RE)
    judged = _extract_list_block(body, _JUDGED_BLOCK_RE)
    version_match = _VERSION_RE.search(body)
    version = version_match.group(1) if version_match else "0.1.0"
    rubrics = sorted({criterion.split("-", 1)[0] for criterion in scripted + judged})
    return {"scripted": scripted, "judged": judged, "rubrics": rubrics, "version": version}


# ---------------------------------------------------------------------------
# Grid: tiers, artifacts, cells
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Tier:
    alias: str
    model_id: str


@dataclass(frozen=True)
class ArtifactRef:
    domain: str
    path: str
    sha256: str
    artifact_type: str

    @property
    def artifact_id(self) -> str:
        return Path(self.path).stem


@dataclass(frozen=True)
class GridCell:
    """One (skill or baseline, artifact, tier, run) cell of the measurement grid.

    `skill` is what gets written to `run.skill`: the emitting critique-<domain> skill for a
    "skill" condition cell, or `BASELINE_SKILL` ("baseline-generic") for a "baseline" one.
    """

    condition: str  # "skill" or "baseline"
    skill: str
    artifact: ArtifactRef
    tier: Tier
    run_index: int
    out_path: Path


def load_measurement_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_tiers(models: Sequence[dict[str, Any]], raw_tiers: str) -> list[Tier]:
    """`raw_tiers` is blank for every pinned tier in `models`, else a comma-separated allowlist
    of tier aliases (bench/results/measurement-manifest.json's own "haiku" and "sonnet")."""
    all_tiers = [Tier(alias=m["alias"], model_id=m["id"]) for m in models]
    if not raw_tiers.strip():
        return all_tiers
    by_alias = {t.alias: t for t in all_tiers}
    wanted = [w.strip() for w in raw_tiers.split(",") if w.strip()]
    missing = [w for w in wanted if w not in by_alias]
    if missing:
        raise ValueError(f"unknown tier alias(es) {missing}; pinned aliases are {sorted(by_alias)}")
    return [by_alias[w] for w in wanted]


def discover_skill_artifacts(corpus_dir: Path, skill: str) -> list[ArtifactRef]:
    """Every artifact this skill's domain corpus declares, from
    `bench/corpus/<domain>/*.manifest.json` (bench/README.md, "Layout"). `domain` is the skill
    name with its `critique-` prefix removed, the same convention `skills/critique-<domain>/`
    itself already uses. Returns [] when the domain has no corpus directory yet."""
    domain = skill.removeprefix("critique-")
    domain_dir = corpus_dir / domain
    if not domain_dir.is_dir():
        return []
    refs = []
    for manifest_path in sorted(domain_dir.glob("*.manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        refs.append(
            ArtifactRef(
                domain=domain,
                path=manifest["artifact"],
                sha256=manifest["artifact_sha256"],
                artifact_type=manifest["artifact_type"],
            )
        )
    return refs


def plan_grid(
    skills: Sequence[str],
    tiers: Sequence[Tier],
    k: int,
    *,
    corpus_dir: Path,
    out_dir: Path,
    include_baseline: bool = True,
) -> list[GridCell]:
    """The full (skill, artifact, tier, k) grid, plus a baseline cell alongside every skill cell
    unless `include_baseline` is False. Deterministic order: skills sorted, artifacts sorted (as
    `discover_skill_artifacts` already returns them), tiers in the order `resolve_tiers` gave
    them, run index ascending, skill cell before its paired baseline cell.
    """
    cells: list[GridCell] = []
    for skill in sorted(skills):
        for artifact in discover_skill_artifacts(corpus_dir, skill):
            for tier in tiers:
                for run_index in range(1, k + 1):
                    cells.append(
                        GridCell(
                            condition="skill",
                            skill=skill,
                            artifact=artifact,
                            tier=tier,
                            run_index=run_index,
                            out_path=out_dir / skill / artifact.artifact_id / f"{tier.alias}-r{run_index}.json",
                        )
                    )
                    if include_baseline:
                        cells.append(
                            GridCell(
                                condition="baseline",
                                skill=BASELINE_SKILL,
                                artifact=artifact,
                                tier=tier,
                                run_index=run_index,
                                out_path=out_dir
                                / "baseline"
                                / artifact.domain
                                / artifact.artifact_id
                                / f"{tier.alias}-r{run_index}.json",
                            )
                        )
    return cells


def format_grid(cells: Sequence[GridCell]) -> list[str]:
    """The exact planned grid, one line per cell, for --dry-run (S-07 AC-3)."""
    skill_count = sum(1 for c in cells if c.condition == "skill")
    baseline_count = sum(1 for c in cells if c.condition == "baseline")
    lines = [
        f"bench: {len(cells)} cell(s) planned ({skill_count} skill run(s), {baseline_count} baseline run(s))"
    ]
    for cell in cells:
        lines.append(
            f"bench:   [{cell.condition}] {cell.skill} {cell.artifact.artifact_id} "
            f"{cell.tier.alias} ({cell.tier.model_id}) r{cell.run_index} -> {cell.out_path.as_posix()}"
        )
    return lines


# ---------------------------------------------------------------------------
# Scripted lane: run a skill's own scripts/checks.py
# ---------------------------------------------------------------------------


class ScriptedLaneError(RuntimeError):
    """Raised when a skill's scripts/checks.py exits non-zero or does not print a JSON envelope."""


def run_scripted_lane_subprocess(skill: str, artifact_disk_path: Path, *, repo_root: Path) -> dict[str, Any]:
    """Run `python skills/<skill>/scripts/checks.py <artifact> --repo-root <repo_root>`, the same
    invocation `agents/critique-critic.md`'s Protocol section describes, and parse its stdout
    envelope (`run.model` is "none": no judged lane ran inside checks.py itself).
    """
    checks_py = repo_root / "skills" / skill / "scripts" / "checks.py"
    if not checks_py.is_file():
        raise ScriptedLaneError(f"{checks_py} does not exist")
    proc = subprocess.run(
        [sys.executable, str(checks_py), str(artifact_disk_path), "--repo-root", str(repo_root)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode != 0:
        raise ScriptedLaneError(f"{checks_py} exited {proc.returncode}: {proc.stderr.strip()}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ScriptedLaneError(f"{checks_py} did not print a JSON envelope: {exc}") from exc


# ---------------------------------------------------------------------------
# Judged lane: prompt assembly and the Anthropic API call
# ---------------------------------------------------------------------------

_JUDGED_SYSTEM_TEMPLATE = """You are performing the judged-lane portion of a {skill_name} critique run, the same clean-context
protocol agents/critique-critic.md defines: you have not seen any authoring history, drafts, prior
critique, or the requester's opinion of the artifact, and you never edit anything.

This run's scripted-lane criteria are already covered by a separate deterministic pass. Evaluate
only the judged criteria listed below, in the order listed, and report no finding against any
other criterion.

Judged criteria for this run:
{judged_criteria_list}

Follow this protocol:
1. Inventory the artifact's structure. No findings yet.
2. Sweep every judged criterion above, in the listed order, evaluating each against the whole
   artifact before moving to the next.
3. Once every criterion has been swept, assign severity to every finding as its own pass, using
   the weighing order below (impact, then frequency, then persistence) and this skill's own
   severity anchors.
4. Do not rank or bound your output. Report every finding you found in step 2, in the order you
   found it; a separate process combines your findings with the scripted lane's and applies the
   output bound once, over the combined pool.

Severity scale, weighed impact first, then frequency, then persistence:
{severity_scale}

This skill's own SKILL.md, in full, for the criterion definitions, operational tests, and
severity anchors your sweep must use:
{skill_md}

This skill's reference material:
{references}

Output contract: your final message is exactly one JSON object and nothing else, no markdown
code fence, no prose before or after it:

{{"findings": [{{"criterion": "<one of the judged criteria above, exact string>", "severity": <integer 0 to 4>, "location": "<where in the artifact, specific enough to navigate to unaided>", "evidence": "<a short quotation from the artifact or a measurement taken from it, never a characterization>", "violation": "<which part of the criterion was breached>", "fix": "<a specific, actionable change>", "confidence": "<high, medium, or low>"}}]}}

If you find no problems under any judged criterion, output {{"findings": []}} and nothing else.
Never invent a location, a quotation, or a fix: every finding you report must be checkable
against the artifact text you were given.
"""


def build_judged_system_prompt(skill: str, *, repo_root: Path = ROOT) -> tuple[str, dict[str, Any]]:
    """The judged-lane system prompt for `skill`, assembled from its SKILL.md and
    references/*.md, plus the parsed frontmatter (`judged`, `rubrics`, `version`) the caller
    needs to build the rest of the envelope.
    """
    skill_dir = repo_root / "skills" / skill
    skill_md_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = parse_skill_frontmatter(skill_md_text)

    references_dir = skill_dir / "references"
    reference_parts = []
    if references_dir.is_dir():
        for ref_path in sorted(references_dir.glob("*.md")):
            reference_parts.append(f"### {ref_path.name}\n\n{ref_path.read_text(encoding='utf-8')}")

    severity_scale_text = SEVERITY_SCALE_PATH.read_text(encoding="utf-8")
    judged_criteria_list = "\n".join(f"- {c}" for c in frontmatter["judged"])

    system_prompt = _JUDGED_SYSTEM_TEMPLATE.format(
        skill_name=skill,
        judged_criteria_list=judged_criteria_list,
        severity_scale=severity_scale_text,
        skill_md=skill_md_text,
        references="\n\n".join(reference_parts) if reference_parts else "(no references directory)",
    )
    return system_prompt, frontmatter


def _response_text(response: Any) -> str:
    """Concatenate the text of every text content block in a Messages API response. Accepts both
    a real SDK response (attribute access) and a test double (an object or dict exposing the
    same shape), so the same code path is exercised in tests and in a live run.
    """
    parts: list[str] = []
    for block in getattr(response, "content", None) or []:
        text = getattr(block, "text", None)
        if text is None and isinstance(block, dict):
            text = block.get("text")
        if text:
            parts.append(text)
    return "".join(parts)


_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*\n(.*)\n```\s*$", re.DOTALL)
_DASHES = {chr(0x2014): " - ", chr(0x2013): " - "}
_WHITESPACE_RE = re.compile(r"\s+")

_JUDGED_FIELD_MAX_LENGTH = {"location": 400, "evidence": 2000, "violation": 1000, "fix": 1000}


def _sanitize_prose(text: str, *, max_length: int) -> str:
    """Enforce the contract's prose rules (no em dash, no en dash, no leading or trailing
    whitespace) on a judged-lane model response, the way bench/baseline/postprocess.py already
    does for the baseline lane: the model was never told the house style either. Built with
    chr() so this file carries none of the punctuation it exists to strip, matching
    contract/validate.py's own convention.
    """
    for bad, replacement in _DASHES.items():
        text = text.replace(bad, replacement)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    if len(text) > max_length:
        text = text[:max_length].rstrip()
    return text


class JudgedLaneError(RuntimeError):
    """Raised when a judged-lane response cannot be parsed at all: not valid JSON, or missing the
    required top-level shape. A single malformed finding inside an otherwise-valid response is
    dropped instead, matching bench/baseline/postprocess.py's own "drop this block" policy.
    """


def _strip_code_fence(text: str) -> str:
    match = _CODE_FENCE_RE.match(text.strip())
    return match.group(1) if match else text.strip()


def _coerce_severity(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        severity = value
    elif isinstance(value, float) and value.is_integer():
        severity = int(value)
    elif isinstance(value, str) and value.strip().lstrip("-").isdigit():
        severity = int(value.strip())
    else:
        return None
    return severity if 0 <= severity <= 4 else None


def _coerce_confidence(value: Any) -> str:
    if isinstance(value, str) and value.strip().lower() in ("high", "medium", "low"):
        return value.strip().lower()
    return "medium"


def _parse_judged_findings(text: str, *, allowed_criteria: set[str]) -> list[dict[str, Any]]:
    """Parse a judged-lane response into finding dicts (no `id`, `lane` forced to "judged"). A
    finding whose criterion is not in `allowed_criteria`, whose severity does not parse to an
    integer 0 to 4, or that is missing a required text field, is dropped rather than guessed at.
    """
    stripped = _strip_code_fence(text)
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise JudgedLaneError(
            f"judged-lane response is not valid JSON: {exc}; response started with {stripped[:200]!r}"
        ) from exc

    if isinstance(data, list):
        raw_items = data
    elif isinstance(data, dict) and isinstance(data.get("findings"), list):
        raw_items = data["findings"]
    else:
        raise JudgedLaneError("judged-lane response JSON has no top-level 'findings' array")

    findings: list[dict[str, Any]] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        criterion = item.get("criterion")
        if not isinstance(criterion, str) or criterion not in allowed_criteria:
            continue
        severity = _coerce_severity(item.get("severity"))
        if severity is None:
            continue

        text_fields: dict[str, str] | None = {}
        for field_name, max_length in _JUDGED_FIELD_MAX_LENGTH.items():
            value = item.get(field_name)
            if not isinstance(value, str) or not value.strip():
                text_fields = None
                break
            text_fields[field_name] = _sanitize_prose(value, max_length=max_length)
        if text_fields is None:
            continue

        findings.append(
            {
                "criterion": criterion,
                "lane": "judged",
                "severity": severity,
                "confidence": _coerce_confidence(item.get("confidence")),
                **text_fields,
            }
        )
    return findings


# ---------------------------------------------------------------------------
# Transport: Claude Code, not the Anthropic SDK
# ---------------------------------------------------------------------------
#
# Both lanes reach a model through an object exposing `client.messages.create(...)`. That was the
# Anthropic SDK's shape, and it is kept, because it is also the shape the test doubles implement:
# swapping the transport therefore changes one factory function and nothing else, and every existing
# test still exercises the same code path.
#
# It is Claude Code rather than the API for the reason ADR 0030 gives: a run authenticates from a
# Claude subscription, so no ANTHROPIC_API_KEY exists anywhere, for a user or a maintainer. Probed
# on a clean CI runner 2026-08-08 with a `claude setup-token` credential in CLAUDE_CODE_OAUTH_TOKEN.
#
# Two constraints this must respect, both easy to break by accident:
#
#   1. NEVER pass --bare. Its own documentation says auth there is "strictly ANTHROPIC_API_KEY or
#      apiKeyHelper (OAuth and keychain are never read)", so it silently reintroduces the key. It is
#      otherwise attractive for a benchmark because it skips hooks and plugin sync.
#   2. ALWAYS pass --model. Without it a run inherits whatever model the caller happens to be using,
#      and a benchmark that does not control its own model is measuring nothing reproducible.


@dataclass(frozen=True)
class _TextBlock:
    """One content block, shaped like the Messages API's, so _response_text reads it unchanged."""

    text: str
    type: str = "text"


@dataclass(frozen=True)
class _ClaudeCodeResponse:
    content: list[_TextBlock]


class _ClaudeCodeMessages:
    """`messages.create(...)`, backed by a non-interactive `claude -p` invocation."""

    def __init__(self, *, cli: str = "claude", timeout: int = 900) -> None:
        self._cli = cli
        self._timeout = timeout

    def create(
        self,
        *,
        model: str,
        messages: Sequence[dict[str, Any]],
        system: str | None = None,
        max_tokens: int | None = None,  # noqa: ARG002 - accepted for interface parity, see below
        **_ignored: Any,
    ) -> _ClaudeCodeResponse:
        # max_tokens has no Claude Code equivalent and is accepted only so the call sites and the
        # SDK-shaped test doubles stay identical. Dropping it is safe here: it was an upper bound,
        # never a target, and the judged lane's output is bounded by the protocol rather than by
        # token count.
        #
        # NEITHER prompt goes on the command line. The first live run of this transport failed every
        # skill cell with "[WinError 206] The filename or extension is too long", because a judged
        # system prompt assembled from SKILL.md plus references/*.md exceeds the platform's argument
        # limit. Baseline cells, which carry no system prompt, succeeded in the same run. So the
        # system prompt goes to a temp file and the user prompt goes over stdin, and neither can
        # grow into that failure again as skills or artifacts get larger.
        prompt = "\n\n".join(str(m.get("content", "")) for m in messages)
        argv = [self._cli, "--model", model, "-p"]
        system_file: Path | None = None
        try:
            if system:
                # --append-system-prompt-file rather than --system-prompt-file: the original
                # measurement ran under a subagent that had Claude Code's own context plus its
                # instructions, so replacing the system prompt outright would diverge from it
                # further, not less.
                fd, name = tempfile.mkstemp(prefix="bench-system-", suffix=".txt", text=True)
                system_file = Path(name)
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    fh.write(system)
                argv[1:1] = ["--append-system-prompt-file", str(system_file)]
            proc = subprocess.run(
                argv,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                encoding="utf-8",
            )
        finally:
            if system_file is not None:
                system_file.unlink(missing_ok=True)
        if proc.returncode != 0:
            raise RuntimeError(
                f"claude exited {proc.returncode} for model {model}: "
                f"{(proc.stderr or proc.stdout or '').strip()[:400]}"
            )
        return _ClaudeCodeResponse(content=[_TextBlock(text=(proc.stdout or "").strip())])


class ClaudeCodeClient:
    """An Anthropic-SDK-shaped client that runs prompts through the Claude Code CLI.

    Exists so a live benchmark run needs no API key. `claude` must be on PATH, and must be
    authenticated: interactively on a workstation, or via a `claude setup-token` credential in
    CLAUDE_CODE_OAUTH_TOKEN on a machine where nobody is logged in.
    """

    def __init__(self, *, cli: str = "claude", timeout: int = 900) -> None:
        self.messages = _ClaudeCodeMessages(cli=cli, timeout=timeout)


def call_judged_lane(
    client: Any,
    *,
    model_id: str,
    system_prompt: str,
    artifact_path: str,
    artifact_text: str,
    allowed_criteria: Sequence[str],
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> list[dict[str, Any]]:
    response = client.messages.create(
        model=model_id,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": f"Artifact: {artifact_path}\n\n{artifact_text}"}],
    )
    return _parse_judged_findings(_response_text(response), allowed_criteria=set(allowed_criteria))


@functools.lru_cache(maxsize=1)
def _baseline_prompt_text() -> str:
    return BASELINE_PROMPT_PATH.read_text(encoding="utf-8")


def call_baseline_lane(
    client: Any, *, model_id: str, artifact_text: str, max_tokens: int = DEFAULT_MAX_TOKENS
) -> str:
    """Invoke the frozen baseline prompt against `artifact_text`, the artifact as the only other
    input (bench/baseline/README.md, "Runner spec", step 1): no rubric, no criterion list, and
    no prior critique are ever added.
    """
    response = client.messages.create(
        model=model_id,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": f"{_baseline_prompt_text()}\n\n---\n\n{artifact_text}"}],
    )
    return _response_text(response)


# ---------------------------------------------------------------------------
# Lane merge and bounding
# ---------------------------------------------------------------------------


def _to_raw_finding(finding: dict[str, Any]) -> RawFinding:
    return RawFinding(
        criterion=finding["criterion"],
        severity=int(finding["severity"]),
        location=finding["location"],
        evidence=finding["evidence"],
        violation=finding["violation"],
        fix=finding["fix"],
        lane=finding.get("lane", "scripted"),
        confidence=finding.get("confidence", "high"),
        instances=tuple(finding.get("instances") or ()),
        rubric_source=finding.get("rubric_source"),
        selector=finding.get("selector"),
    )


def merge_lanes(
    scripted_findings: Sequence[dict[str, Any]], judged_findings: Sequence[dict[str, Any]]
) -> tuple[list[dict[str, Any]], int, dict[str, int]]:
    """Combine both lanes' findings into one pool and apply the skill's bounded-output rule over
    that combined pool (agents/critique-critic.md, Protocol step 5), reusing the library's own
    canonical rank-and-bound implementation (skills/_shared/envelope.py) rather than a second
    copy of it. Returns (findings, suppressed_count, histogram); `findings` carries fresh
    F-NNN ids assigned after ranking, so a scripted id and a judged id can never collide.
    """
    raw = [_to_raw_finding(f) for f in scripted_findings] + [_to_raw_finding(f) for f in judged_findings]
    histogram = by_severity_histogram(raw)
    emitted_raw, suppressed_count = rank_and_bound(raw)
    findings = [to_finding_dict(r, finding_id=f"F-{index:03d}") for index, r in enumerate(emitted_raw, start=1)]
    return findings, suppressed_count, histogram


def assemble_merged_envelope(
    *,
    skill: str,
    skill_version: str,
    artifact_path: str,
    artifact_sha256: str,
    model: str,
    timestamp: str,
    rubrics: Sequence[str],
    scripted_findings: Sequence[dict[str, Any]],
    judged_findings: Sequence[dict[str, Any]],
    severity_3_threshold: int = 0,
) -> dict[str, Any]:
    """Assemble one contract-valid run envelope from both lanes' findings."""
    findings, suppressed_count, histogram = merge_lanes(scripted_findings, judged_findings)
    summary = build_summary(histogram=histogram, suppressed_count=suppressed_count, severity_3_threshold=severity_3_threshold)
    run = {
        "skill": skill,
        "skill_version": skill_version,
        "contract_version": CONTRACT_VERSION,
        "artifact": artifact_path,
        "artifact_sha256": artifact_sha256,
        "model": model,
        "timestamp": timestamp,
        "rubrics": list(rubrics),
    }
    return {"run": run, "findings": findings, "summary": summary}


# ---------------------------------------------------------------------------
# Cell execution
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_artifact(repo_root: Path, artifact: ArtifactRef) -> str:
    """Read the artifact's bytes and verify them against the manifest's own sha256, the same
    check bench/metrics/__main__.py's own artifact reader makes: a run against the wrong bytes
    is not a reproduction of anything.
    """
    disk_path = repo_root / artifact.path
    raw = disk_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != artifact.sha256:
        raise RuntimeError(
            f"{disk_path}: sha256 {digest} does not match manifest artifact_sha256 {artifact.sha256}"
        )
    return raw.decode("utf-8")


RunScriptedFn = Callable[..., dict[str, Any]]


def execute_skill_cell(
    cell: GridCell,
    *,
    client: Any,
    repo_root: Path,
    run_scripted_fn: RunScriptedFn,
    system_prompt: str,
    frontmatter: dict[str, Any],
    max_tokens: int,
    severity_3_threshold: int,
    now_fn: Callable[[], str],
) -> dict[str, Any]:
    artifact_text = _read_artifact(repo_root, cell.artifact)
    scripted_env = run_scripted_fn(cell.skill, repo_root / cell.artifact.path, repo_root=repo_root)
    if scripted_env.get("run", {}).get("artifact_sha256") != cell.artifact.sha256:
        raise RuntimeError("scripted lane reported a different artifact_sha256 than the manifest")

    if frontmatter["judged"]:
        judged_findings = call_judged_lane(
            client,
            model_id=cell.tier.model_id,
            system_prompt=system_prompt,
            artifact_path=cell.artifact.path,
            artifact_text=artifact_text,
            allowed_criteria=frontmatter["judged"],
            max_tokens=max_tokens,
        )
    else:
        judged_findings = []

    return assemble_merged_envelope(
        skill=cell.skill,
        skill_version=frontmatter["version"],
        artifact_path=cell.artifact.path,
        artifact_sha256=cell.artifact.sha256,
        model=cell.tier.model_id,
        timestamp=now_fn(),
        rubrics=frontmatter["rubrics"],
        scripted_findings=scripted_env["findings"],
        judged_findings=judged_findings,
        severity_3_threshold=severity_3_threshold,
    )


def execute_baseline_cell(
    cell: GridCell, *, client: Any, repo_root: Path, max_tokens: int, now_fn: Callable[[], str]
) -> tuple[dict[str, Any], str]:
    artifact_text = _read_artifact(repo_root, cell.artifact)
    raw_text = call_baseline_lane(client, model_id=cell.tier.model_id, artifact_text=artifact_text, max_tokens=max_tokens)
    envelope = baseline_postprocess(
        raw_text,
        artifact=cell.artifact.path,
        artifact_sha256=cell.artifact.sha256,
        model=cell.tier.model_id,
        timestamp=now_fn(),
    )
    return envelope, raw_text


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text = text + "\n"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


@dataclass
class CellResult:
    cell: GridCell
    ok: bool
    detail: str = ""


def execute_grid(
    cells: Sequence[GridCell],
    *,
    client: Any,
    repo_root: Path,
    run_scripted_fn: RunScriptedFn = run_scripted_lane_subprocess,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    severity_3_threshold: int = 0,
    now_fn: Callable[[], str] | None = None,
) -> list[CellResult]:
    """Execute every cell, writing a contract-valid envelope for each one that succeeds. A cell
    that fails (a bad scripted-lane exit, an unparseable judged response, a schema-invalid
    assembled envelope) is recorded as a failure and does not stop the rest of the grid: a
    harness that aborts on the first bad cell throws away every good run that ran before it.
    """
    now_fn = now_fn or _utc_now_iso
    prompt_cache: dict[str, tuple[str, dict[str, Any]]] = {}
    results: list[CellResult] = []

    for cell in cells:
        try:
            if cell.condition == "skill":
                if cell.skill not in prompt_cache:
                    prompt_cache[cell.skill] = build_judged_system_prompt(cell.skill, repo_root=repo_root)
                system_prompt, frontmatter = prompt_cache[cell.skill]
                envelope = execute_skill_cell(
                    cell,
                    client=client,
                    repo_root=repo_root,
                    run_scripted_fn=run_scripted_fn,
                    system_prompt=system_prompt,
                    frontmatter=frontmatter,
                    max_tokens=max_tokens,
                    severity_3_threshold=severity_3_threshold,
                    now_fn=now_fn,
                )
                validation = validate_document(envelope)
                if not validation.ok:
                    raise RuntimeError(f"assembled envelope is not contract-valid: {validation.errors[0]}")
                _write_json(cell.out_path, envelope)
            else:
                envelope, raw_text = execute_baseline_cell(
                    cell, client=client, repo_root=repo_root, max_tokens=max_tokens, now_fn=now_fn
                )
                validation = validate_document(envelope)
                if not validation.ok:
                    raise RuntimeError(f"baseline envelope is not contract-valid: {validation.errors[0]}")
                _write_json(cell.out_path, envelope)
                _write_text(cell.out_path.with_name(cell.out_path.name + ".raw.txt"), raw_text)
            results.append(CellResult(cell=cell, ok=True))
        except Exception as exc:  # a harness must keep going and report, never crash the whole grid on one bad cell
            results.append(CellResult(cell=cell, ok=False, detail=str(exc)))

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _client_factory() -> Any:
    """The transport a live run uses. See ClaudeCodeClient for why it is not the Anthropic SDK."""
    return ClaudeCodeClient()


def _check_out_dir_is_not_committed_evidence(out_dir: Path) -> str | None:
    """Refuse to write into a run set that already holds committed envelopes."""

    # bench/results/runs*/ is immutable measurement evidence: the published figures are recomputed
    # from those files, so overwriting them silently invalidates every number this library reports.
    # The default --out-dir was that directory, which made a live run with no arguments destructive
    # by default. That is not hypothetical: on 2026-08-08 a unit test whose precondition had changed
    # fell through to the live path with default arguments and overwrote nine committed baseline
    # envelopes. They were restored from git, but nothing had stopped it.
    #
    # An empty or absent directory is fine, so a fresh run set needs no ceremony.
    try:
        existing = sorted(out_dir.rglob("*.json")) if out_dir.exists() else []
    except OSError:
        return None
    if not existing:
        return None
    return (
        f"--out-dir {out_dir} already contains {len(existing)} envelope(s). Envelopes under "
        "bench/results/runs*/ are immutable measurement evidence and are never overwritten: the "
        "published figures are recomputed from them. Pass --out-dir pointing at a fresh directory."
    )


def _check_claude_cli(cli: str = "claude") -> str | None:
    """Return a message naming what is wrong, or None if a live run can proceed.

    Two failures are worth telling apart: the CLI missing, and the CLI present but unable to
    authenticate. The second is what happens on a build machine with no credential, and the remedy
    is different, so the message says which one it is.
    """
    try:
        proc = subprocess.run(
            [cli, "--version"], capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL
        )
    except FileNotFoundError:
        return (
            f"the '{cli}' CLI is required for a live run and is not on PATH. Install Claude Code, or "
            "pass --dry-run to validate the wiring without it. No API key is needed either way."
        )
    except subprocess.TimeoutExpired:
        return f"'{cli} --version' timed out; the CLI appears installed but is not responding."
    if proc.returncode != 0:
        return f"'{cli} --version' exited {proc.returncode}: {(proc.stderr or '').strip()[:200]}"
    if os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        return None
    # No token in the environment is normal and fine on a workstation, where the CLI is logged in
    # interactively. It is only a problem where nobody is logged in, which the first model call
    # will surface with the CLI's own error rather than a guess made here.
    return None


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python bench/run_bench.py",
        description="Run the bench harness for one or more skills (bench.yml dispatch entry point).",
    )
    parser.add_argument("--skills", default="all", help='Comma-separated skill names, or "all" (default).')
    parser.add_argument("--k", type=int, default=5, help="Repeat count per skill per artifact (default 5).")
    parser.add_argument(
        "--tiers", default="", help="Comma-separated pinned tier aliases (blank = both pinned tiers)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the exact planned grid and exit; no model call, no secret required.",
    )
    parser.add_argument(
        "--out-dir",
        default=str(DEFAULT_OUT_DIR),
        help="Where envelopes are written. Refuses to write into a run set that already holds "
        "committed evidence; pass a fresh directory for a live run.",
    )
    parser.add_argument("--corpus", default=str(DEFAULT_CORPUS_DIR), help="Corpus root (default bench/corpus).")
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST_PATH),
        help="Pinned-tier manifest (default bench/results/measurement-manifest.json).",
    )
    parser.add_argument("--no-baseline", action="store_true", help="Skip the frozen-baseline condition.")
    parser.add_argument(
        "--no-score", action="store_true", help="Skip the bench.metrics scoring step after a live run."
    )
    parser.add_argument(
        "--results-out",
        default=None,
        help="Where to write the scored results.json (default: the parent of --out-dir, results.json).",
    )
    parser.add_argument("--run-set", default=None, help="Recorded run_set identifier (default bench-<UTC date>).")
    parser.add_argument(
        "--severity-3-threshold",
        type=int,
        default=0,
        dest="severity_3_threshold",
        help="Gate threshold recorded on every emitted envelope (default 0).",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        dest="max_tokens",
        help=f"max_tokens for every model call (default {DEFAULT_MAX_TOKENS}).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if args.k < 1:
        print("bench: --k must be at least 1", file=sys.stderr)
        return 2

    all_skills = declared_skills()
    selected = resolve_filter(all_skills, args.skills)

    print(f"bench: skills filter '{args.skills}' -> {len(selected)} of {len(all_skills)} declared skill(s)")
    print(f"bench: k={args.k}, tiers='{args.tiers or '(default pinned tiers)'}', dry_run={args.dry_run}")

    manifest_path = Path(args.manifest)
    try:
        manifest = load_measurement_manifest(manifest_path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"bench: cannot read {manifest_path}: {exc}", file=sys.stderr)
        return 2

    try:
        tiers = resolve_tiers(manifest.get("models", []), args.tiers)
    except ValueError as exc:
        print(f"bench: {exc}", file=sys.stderr)
        return 2

    corpus_dir = Path(args.corpus)
    out_dir = Path(args.out_dir)
    cells = plan_grid(
        selected, tiers, args.k, corpus_dir=corpus_dir, out_dir=out_dir, include_baseline=not args.no_baseline
    )

    for line in format_grid(cells):
        print(line)

    if args.dry_run:
        return 0

    # A live run needs the Claude Code CLI, not an API key (ADR 0030). Checked here rather than at
    # the first model call so a misconfigured dispatch fails immediately and says what is wrong,
    # instead of after planning a grid and part-running it.
    cli_check = _check_claude_cli()
    if cli_check is not None:
        print(f"bench: {cli_check}", file=sys.stderr)
        return 1

    out_dir_check = _check_out_dir_is_not_committed_evidence(Path(args.out_dir))
    if out_dir_check is not None:
        print(f"bench: {out_dir_check}", file=sys.stderr)
        return 1

    if not selected or not cells:
        print("bench: no skills to run yet (library.json declares none, or none matched the filter); nothing to do.")
        return 0

    try:
        client = _client_factory()
    except RuntimeError as exc:
        print(f"bench: {exc}", file=sys.stderr)
        return 1

    results = execute_grid(
        cells,
        client=client,
        repo_root=ROOT,
        max_tokens=args.max_tokens,
        severity_3_threshold=args.severity_3_threshold,
    )
    failures = [r for r in results if not r.ok]
    print(f"bench: {len(results) - len(failures)} of {len(results)} cell(s) written to {out_dir}")
    for failure in failures:
        cell = failure.cell
        print(
            f"bench: FAILED [{cell.condition}] {cell.skill} {cell.artifact.artifact_id} "
            f"{cell.tier.alias} r{cell.run_index}: {failure.detail}",
            file=sys.stderr,
        )

    if failures:
        print(f"bench: {len(failures)} cell(s) failed; skipping the scoring step.", file=sys.stderr)
        return 1

    if args.no_score:
        return 0

    run_set = args.run_set or f"bench-{_utc_now_iso()[:10]}"
    results_out = Path(args.results_out) if args.results_out else out_dir.parent / "results.json"
    try:
        scored = build_results(corpus_dir, out_dir, run_set=run_set, generated_at=_utc_now_iso(), repo_root=ROOT)
    except (ScoreError, OSError) as exc:
        print(f"bench: scoring failed: {exc}", file=sys.stderr)
        return 1
    _write_json(results_out, scored)
    print(f"bench: wrote {results_out} ({len(scored['entries'])} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

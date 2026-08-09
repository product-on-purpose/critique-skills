"""CLI: the bench.yml workflow_dispatch entry point (S-07 CI-pipeline spec), and the real
reproduction harness the P3 self-audit found missing (docs/internal/execution/P3-report.md,
"Provenance gap: no committed harness actually calls a live model or the critic subagent").

For a given (skill, artifact, tier, k) grid, this module:

1. Discovers the grid from what is actually declared: skills from library.json, artifacts from
   `bench/corpus/<domain>/*.manifest.json`, tiers from `bench/results/measurement-manifest.json`'s
   pinned `models` list (the same file ADR 0023 records the measurement basis in).
2. Stages each artifact alone in a temp directory, away from the `*.manifest.json` seeded-defect
   answer key that sits beside it in the corpus (see `staged_artifact`).
3. Runs the REAL skill against that staged copy, through `claude --plugin-dir`, and takes the
   envelope it emits (ADR 0030's fidelity half). The harness assembles no prompt of its own: it
   used to build a judged-lane system prompt from the skill's `SKILL.md` and `references/*.md`,
   which was a second definition of the critique protocol with nothing keeping it in step with
   the real one in `agents/critique-critic.md` and the six `SKILL.md` files.
4. Fills in the `run` block, which the skill cannot know: the corpus path, the manifest sha256,
   the pinned model id and the run timestamp. `findings` and `summary` are the skill's own, and
   are never rewritten; the skill runs both lanes and applies its own bounded-output rule over the
   combined pool (methodology section 7; `agents/critique-critic.md`, Protocol step 5).
5. Validates the envelope against the contract before writing it, and never writes one that fails.
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
import contextlib
import functools
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Sequence


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
# Only CONTRACT_VERSION: since ADR 0030's fidelity half the skill does its own ranking, bounding
# and summarising, and the harness no longer keeps a second copy of that logic.
from skills._shared.envelope import CONTRACT_VERSION  # noqa: E402

LIBRARY_JSON = ROOT / "library.json"
DEFAULT_CORPUS_DIR = ROOT / "bench" / "corpus"
DEFAULT_OUT_DIR = ROOT / "bench" / "results" / "runs"
DEFAULT_MANIFEST_PATH = ROOT / "bench" / "results" / "measurement-manifest.json"
BASELINE_PROMPT_PATH = ROOT / "bench" / "baseline" / "prompt.txt"
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
# The judged lane runs the real skill; the harness only reads its frontmatter
# ---------------------------------------------------------------------------

def load_skill_frontmatter(skill: str, *, repo_root: Path = ROOT) -> dict[str, Any]:
    """The parsed SKILL.md frontmatter (`judged`, `scripted`, `rubrics`, `version`) the harness
    needs to fill in an envelope's `run` block.

    This is all that survives of what used to be build_judged_system_prompt(). The harness no
    longer assembles a judged-lane prompt from SKILL.md and references/*.md: that was a second
    definition of the critique protocol, and ADR 0030's fidelity half deleted it in favour of
    running the real skill. What is still needed from the file is its declared version and
    rubrics, because the skill is never told which run it is part of.
    """
    skill_md_text = (repo_root / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    return parse_skill_frontmatter(skill_md_text)


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
class JudgedLaneError(RuntimeError):
    """Raised when a skill run cannot be turned into an envelope at all: the response was not
    JSON, or was JSON of the wrong shape. The cell is recorded as failed rather than written,
    because a harness must never invent or partially assemble measurement evidence.
    """


def _strip_code_fence(text: str) -> str:
    """Models wrap JSON in a fence regardless of instruction, so an envelope arrives fenced often
    enough that treating it as a failure would throw away good cells."""
    match = _CODE_FENCE_RE.match(text.strip())
    return match.group(1) if match else text.strip()


def _extract_envelope(text: str) -> dict[str, Any] | None:
    """The last balanced JSON object in `text` that looks like a run envelope, or None.

    A real skill run narrates. Measured against the pinned haiku tier on 2026-08-09, the response
    was 7403 bytes that opened "Now I'll perform the judged criterion sweep", walked through four
    protocol passes, and only then emitted the envelope, fenced, at the end. Requiring the whole
    response to parse would have discarded a complete, contract-valid run.

    Last rather than first, and shape-checked rather than merely valid JSON, because a run
    typically echoes its scripted lane's own output on the way past. Taking the first object, or
    any object that happens to parse, captures that intermediate instead of the merged result.
    """
    candidate: dict[str, Any] | None = None
    for start, char in enumerate(text):
        if char != "{":
            continue
        depth = 0
        for end in range(start, len(text)):
            if text[end] == "{":
                depth += 1
            elif text[end] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        parsed = json.loads(text[start : end + 1])
                    except json.JSONDecodeError:
                        pass
                    else:
                        if (
                            isinstance(parsed, dict)
                            and isinstance(parsed.get("findings"), list)
                            and isinstance(parsed.get("run"), dict)
                            and isinstance(parsed.get("summary"), dict)
                        ):
                            candidate = parsed
                    break
    return candidate


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
        plugin_dir: Path | str | None = None,
        cwd: Path | str | None = None,
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
        # Isolation, on BOTH lanes. Measured 2026-08-09: without these two flags a nested run
        # offered 97 skills, the six under test plus 91 from the operator's own ambient
        # configuration, along with whatever plugins, MCP servers and hooks it carries, and a full
        # skill run never finished. --plugin-dir adds a plugin; it does not isolate an environment,
        # and without isolation two operators are not running the same benchmark. With these, the
        # same probe offered 18, all of them the CLI's own built-ins plus the plugin under test.
        # The baseline gets them too: the committed baseline envelopes were produced by a plain API
        # call with no environment at all, so isolating it moves it closer to that, not further.
        argv = [self._cli, "--model", model, "--setting-sources", "", "--strict-mcp-config", "-p"]
        # --plugin-dir loads this repository as a plugin so the judged lane can run the REAL skill
        # (ADR 0030's fidelity half) instead of a prompt the harness assembles. The frozen baseline
        # condition passes no plugin_dir: loading the plugin for it would stop it being a baseline.
        if plugin_dir is not None:
            # An explicit allowlist rather than --permission-mode bypassPermissions, which would
            # hand write access to the repository being measured and would contradict SECURITY.md's
            # claim that the critic has no Write and no Edit. Measured sufficient: the same run
            # completed with 9 findings across both lanes under this allowlist alone.
            argv[1:1] = [
                "--plugin-dir",
                str(plugin_dir),
                "--allowedTools",
                "Read,Bash,Glob,Grep,Task,Skill",
            ]
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
                # cwd is the staged artifact's directory for a skill run, so the agent's working
                # directory contains the artifact and nothing else. See staged_artifact().
                cwd=str(cwd) if cwd is not None else None,
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


_SKILL_RUN_INSTRUCTION = (
    "Use the {skill} skill to critique {artifact}. Follow the skill's protocol exactly, including "
    "running its scripted lane. Output ONLY the final run envelope: one JSON object, with no prose "
    "before or after it and no markdown code fence."
)


def call_skill_lane(
    client: Any,
    *,
    model_id: str,
    skill: str,
    staged_path: Path,
    repo_root: Path,
    severity_3_threshold: int = 0,
) -> dict[str, Any]:
    """Run the REAL skill through Claude Code and return the envelope it emitted.

    This is ADR 0030's fidelity half. The harness used to assemble its own judged-lane system
    prompt from a skill's SKILL.md and references/*.md, which was a second definition of the
    critique protocol living alongside the real one in agents/critique-critic.md and the six
    SKILL.md files, with nothing keeping them in step. Now the skill runs, and the harness only
    transports the result: the skill does its own lane merge and output bounding, so the harness
    must not do either.

    The artifact is named by its bare filename and the process runs with cwd set to the staging
    directory, so the corpus path never reaches the skill and the sibling seeded-defect manifest
    is not discoverable. See staged_artifact().
    """
    instruction = _SKILL_RUN_INSTRUCTION.format(skill=skill, artifact=staged_path.name)
    if severity_3_threshold:
        # Only when it is not the default. agents/critique-critic.md documents this input as "a
        # gate threshold; 0 when omitted", so saying nothing is how you ask for 0, and mentioning
        # it anyway would change the prompt for every cell the committed evidence was measured with.
        instruction += f"\n\nUse severity_3_threshold = {severity_3_threshold} for the gate."
    response = client.messages.create(
        model=model_id,
        messages=[{"role": "user", "content": instruction}],
        plugin_dir=repo_root,
        cwd=staged_path.parent,
    )
    text = _strip_code_fence(_response_text(response))
    envelope = _extract_envelope(text)
    if envelope is None:
        raise JudgedLaneError(
            f"{skill}: no run envelope found in the skill's response: {text[:300]}"
        )
    return envelope


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
# Cell execution
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@contextlib.contextmanager
def staged_artifact(artifact: ArtifactRef, *, repo_root: Path) -> Iterator[Path]:
    """Copy `artifact` alone into a fresh temporary directory and yield the copy.

    Ground-truth isolation. `bench/corpus/<domain>/<id>.manifest.json` is the complete
    seeded-defect answer key (criterion, location, expected severity) and it sits directly beside
    `<id>.md`. That was harmless while the judged lane inlined the artifact's text into a prompt,
    because the model had no filesystem. It stops being harmless the moment the lane runs the real
    skill through Claude Code: `agents/critique-critic.md` declares `Read` and `Bash`, and the
    skill's own protocol tells it to run `scripts/checks.py <artifact>` against a real path. A
    skill that can read the answer key it is being scored against is not being measured.

    `bench/generator/README.md`'s leak rule already covers the artifact's own text and the naming
    of corpus paths, on the stated grounds that "the artifact path is handed to the skill under
    test". It does not cover a sibling answer key, because until now nothing could read one.

    The filename is kept: leak rule 4 guarantees corpus ids carry no criterion ID, no defect
    count, and none of `clean`, `defect`, `seed`, `plant`, `bug`, so the name reveals nothing, and
    keeping it means a failed cell can be traced back to its artifact.
    """
    disk_path = repo_root / artifact.path
    raw = disk_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != artifact.sha256:
        raise RuntimeError(
            f"{disk_path}: sha256 {digest} does not match manifest artifact_sha256 {artifact.sha256}"
        )
    staging = Path(tempfile.mkdtemp(prefix="bench-artifact-"))
    try:
        staged = staging / disk_path.name
        staged.write_bytes(raw)
        yield staged
    finally:
        shutil.rmtree(staging, ignore_errors=True)


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


def execute_skill_cell(
    cell: GridCell,
    *,
    client: Any,
    repo_root: Path,
    frontmatter: dict[str, Any],
    now_fn: Callable[[], str],
    severity_3_threshold: int = 0,
) -> dict[str, Any]:
    """Run the real skill against a staged copy of the artifact and return its envelope, with the
    provenance the skill could not know filled in by the harness.

    Two responsibilities, split on who can be trusted to know what:

    * The **skill** owns `findings` and `summary`. It is what is being measured, it runs both of
      its own lanes, and it applies its own bounded-output rule over the combined pool. The
      harness deliberately no longer does any of that; doing it here is what made this module a
      second definition of the protocol (ADR 0030).
    * The **harness** owns the `run` block. The skill is handed a staged file in a temp directory
      and is never told the corpus path, the pinned model id, or the run timestamp, so it cannot
      fill these in and must not be trusted to. Writing the staged path into a committed envelope
      would also publish the running user's home directory and make the evidence unreproducible.
    """
    with staged_artifact(cell.artifact, repo_root=repo_root) as staged:
        envelope = call_skill_lane(
            client,
            model_id=cell.tier.model_id,
            skill=cell.skill,
            staged_path=staged,
            repo_root=repo_root,
            severity_3_threshold=severity_3_threshold,
        )

    envelope["run"] = {
        "skill": cell.skill,
        "skill_version": frontmatter["version"],
        "contract_version": CONTRACT_VERSION,
        "artifact": cell.artifact.path,
        "artifact_sha256": cell.artifact.sha256,
        "model": cell.tier.model_id,
        "timestamp": now_fn(),
        "rubrics": list(frontmatter["rubrics"]),
    }
    return envelope


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
    frontmatter_cache: dict[str, dict[str, Any]] = {}
    results: list[CellResult] = []

    for cell in cells:
        try:
            if cell.condition == "skill":
                if cell.skill not in frontmatter_cache:
                    frontmatter_cache[cell.skill] = load_skill_frontmatter(cell.skill, repo_root=repo_root)
                envelope = execute_skill_cell(
                    cell,
                    client=client,
                    repo_root=repo_root,
                    frontmatter=frontmatter_cache[cell.skill],
                    now_fn=now_fn,
                    severity_3_threshold=severity_3_threshold,
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

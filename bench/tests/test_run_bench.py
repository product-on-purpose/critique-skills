"""Tests for bench/run_bench.py: grid planning, ground-truth isolation, the skill-lane transport,
envelope validity, and the baseline (postprocess) path.

No test in this file reaches a model. Every model call is a fake client object implementing the
same `client.messages.create(**kwargs) -> response` shape the transport does (response.content is
a list of objects carrying `.text`), matching this module's own `_response_text` helper. Tests
that could otherwise fall through to a real `claude` process patch the seam with `_forbid`.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

import bench.run_bench as run_bench
from bench.baseline.postprocess import postprocess as baseline_postprocess
from bench.run_bench import (
    ArtifactRef,
    GridCell,
    JudgedLaneError,
    Tier,
    _response_text,
    call_baseline_lane,
    declared_skills,
    discover_skill_artifacts,
    execute_baseline_cell,
    execute_grid,
    format_grid,
    main,
    parse_skill_frontmatter,
    plan_grid,
    resolve_filter,
    resolve_tiers,
)
from contract.validate import validate_document

FIXED_TIMESTAMP = "2026-07-31T00:00:00Z"


def _now() -> str:
    return FIXED_TIMESTAMP


# ---------------------------------------------------------------------------
# Fakes: a client with the same shape client.messages.create(...) has
# ---------------------------------------------------------------------------


class FakeTextBlock:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class FakeResponse:
    def __init__(self, text: str) -> None:
        self.content = [FakeTextBlock(text)]


class FakeMessages:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> FakeResponse:
        self.calls.append(kwargs)
        return self._responses.pop(0)


def _forbid(name: str):
    """A stand-in that fails the test if called.

    A live-path test that accidentally reaches a real transport spawns real `claude` processes,
    which hangs the suite and costs tokens. That happened once while ADR 0030 was being
    implemented, because a test asserting the old ANTHROPIC_API_KEY precondition fell through to
    the run loop when the precondition changed. Patching the seams with this makes the same
    mistake fail fast and say so.
    """

    def _boom(*_args: Any, **_kwargs: Any):
        raise AssertionError(f"{name} must not be reached in this test; it would call a real model")

    return _boom


class FakeClient:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.messages = FakeMessages(responses)


# ---------------------------------------------------------------------------
# Corpus fixture: a small, hermetic (skill, artifact) corpus under tmp_path
# ---------------------------------------------------------------------------


def _write_corpus_artifact(corpus_dir: Path, domain: str, name: str, text: str, artifact_type: str = "markdown-prose") -> ArtifactRef:
    """Write a fake corpus artifact plus its manifest under `corpus_dir`. `manifest["artifact"]`
    is always recorded as "bench/corpus/<domain>/<name>.md", matching the real corpus's own
    convention: a caller that wants `_read_artifact(repo_root, ...)` to resolve it must pass
    `corpus_dir = repo_root / "bench" / "corpus"`.
    """
    import hashlib

    domain_dir = corpus_dir / domain
    domain_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = domain_dir / f"{name}.md"
    artifact_path.write_text(text, encoding="utf-8", newline="\n")
    sha256 = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    manifest = {
        "artifact": f"bench/corpus/{domain}/{name}.md",
        "artifact_sha256": sha256,
        "artifact_type": artifact_type,
        "defects": [],
    }
    (domain_dir / f"{name}.manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return ArtifactRef(domain=domain, path=manifest["artifact"], sha256=sha256, artifact_type=artifact_type)


def _write_fake_skill(repo_root: Path, skill: str, *, scripted: list[str], judged: list[str], version: str = "0.1.0") -> None:
    """A minimal, self-contained skills/<skill>/SKILL.md fixture, so tests that exercise
    load_skill_frontmatter / execute_grid never need to read the real repository's skills tree or
    write into it."""
    skill_dir = repo_root / "skills" / skill
    skill_dir.mkdir(parents=True, exist_ok=True)
    scripted_lines = "\n".join(f"    - {c}" for c in scripted) or "    - PLACEHOLDER"
    judged_lines = "\n".join(f"    - {c}" for c in judged) or "    - PLACEHOLDER"
    skill_md = (
        "---\n"
        f"name: {skill}\n"
        f"version: {version}\n"
        "checks:\n"
        "  scripted:\n"
        f"{scripted_lines}\n"
        "  judged:\n"
        f"{judged_lines}\n"
        "---\n\n"
        f"# {skill}\n\nA fake skill fixture for bench/run_bench.py tests.\n"
    )
    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")


# ---------------------------------------------------------------------------
# Grid planning
# ---------------------------------------------------------------------------


def test_discover_skill_artifacts_reads_manifests_sorted(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "corpus"
    ref_b = _write_corpus_artifact(corpus_dir, "toy", "toy-002", "Second.\n")
    ref_a = _write_corpus_artifact(corpus_dir, "toy", "toy-001", "First.\n")

    refs = discover_skill_artifacts(corpus_dir, "critique-toy")

    assert [r.path for r in refs] == [ref_a.path, ref_b.path]


def test_discover_skill_artifacts_missing_domain_is_empty(tmp_path: Path) -> None:
    assert discover_skill_artifacts(tmp_path / "corpus", "critique-nonexistent") == []


def test_plan_grid_size_matches_skills_times_artifacts_times_tiers_times_k_times_conditions(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "corpus"
    _write_corpus_artifact(corpus_dir, "toy", "toy-001", "One.\n")
    _write_corpus_artifact(corpus_dir, "toy", "toy-002", "Two.\n")
    tiers = [Tier(alias="haiku", model_id="model-a"), Tier(alias="sonnet", model_id="model-b")]

    cells = plan_grid(["critique-toy"], tiers, k=3, corpus_dir=corpus_dir, out_dir=tmp_path / "runs")

    # 2 artifacts * 2 tiers * 3 k * 2 conditions (skill, baseline)
    assert len(cells) == 24
    assert sum(1 for c in cells if c.condition == "skill") == 12
    assert sum(1 for c in cells if c.condition == "baseline") == 12


def test_plan_grid_without_baseline_omits_baseline_cells(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "corpus"
    _write_corpus_artifact(corpus_dir, "toy", "toy-001", "One.\n")
    tiers = [Tier(alias="haiku", model_id="model-a")]

    cells = plan_grid(["critique-toy"], tiers, k=5, corpus_dir=corpus_dir, out_dir=tmp_path / "runs", include_baseline=False)

    assert len(cells) == 5
    assert all(c.condition == "skill" for c in cells)


def test_plan_grid_output_paths_match_the_committed_evidence_layout(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "corpus"
    _write_corpus_artifact(corpus_dir, "clarity", "clarity-001", "Text.\n")
    tiers = [Tier(alias="haiku", model_id="model-a")]
    out_dir = tmp_path / "runs"

    cells = plan_grid(["critique-clarity"], tiers, k=1, corpus_dir=corpus_dir, out_dir=out_dir)

    skill_cell = next(c for c in cells if c.condition == "skill")
    baseline_cell = next(c for c in cells if c.condition == "baseline")
    assert skill_cell.out_path == out_dir / "critique-clarity" / "clarity-001" / "haiku-r1.json"
    assert baseline_cell.out_path == out_dir / "baseline" / "clarity" / "clarity-001" / "haiku-r1.json"
    assert baseline_cell.skill == "baseline-generic"


def test_format_grid_prints_one_line_per_cell_plus_a_summary(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "corpus"
    _write_corpus_artifact(corpus_dir, "toy", "toy-001", "One.\n")
    tiers = [Tier(alias="haiku", model_id="claude-haiku-4-5-20251001")]
    cells = plan_grid(["critique-toy"], tiers, k=1, corpus_dir=corpus_dir, out_dir=tmp_path / "runs")

    lines = format_grid(cells)

    assert lines[0].startswith("bench: 2 cell(s) planned")
    assert sum(1 for line in lines if "[skill]" in line) == 1
    assert sum(1 for line in lines if "[baseline]" in line) == 1
    assert "claude-haiku-4-5-20251001" in "\n".join(lines)


def test_resolve_tiers_blank_returns_every_pinned_tier() -> None:
    models = [{"alias": "haiku", "id": "claude-haiku-4-5-20251001"}, {"alias": "sonnet", "id": "claude-sonnet-5"}]
    assert resolve_tiers(models, "") == [Tier("haiku", "claude-haiku-4-5-20251001"), Tier("sonnet", "claude-sonnet-5")]


def test_resolve_tiers_filters_by_alias() -> None:
    models = [{"alias": "haiku", "id": "claude-haiku-4-5-20251001"}, {"alias": "sonnet", "id": "claude-sonnet-5"}]
    assert resolve_tiers(models, "sonnet") == [Tier("sonnet", "claude-sonnet-5")]


def test_resolve_tiers_unknown_alias_raises() -> None:
    models = [{"alias": "haiku", "id": "claude-haiku-4-5-20251001"}]
    with pytest.raises(ValueError, match="unknown tier alias"):
        resolve_tiers(models, "opus")


def test_declared_skills_and_resolve_filter_still_work() -> None:
    all_skills = declared_skills()
    assert "critique-clarity" in all_skills
    assert resolve_filter(all_skills, "critique-clarity") == ["critique-clarity"]
    assert resolve_filter(all_skills, "all") == all_skills
    assert resolve_filter(all_skills, "") == all_skills


# ---------------------------------------------------------------------------
# SKILL.md frontmatter parsing
# ---------------------------------------------------------------------------


def test_parse_skill_frontmatter_reads_judged_criteria_and_derives_rubrics_by_namespace() -> None:
    text = (
        "---\n"
        "name: critique-toy\n"
        "version: 0.1.0\n"
        "checks:\n"
        "  scripted:\n"
        "    - TOY-ALPHA\n"
        "  judged:\n"
        "    - TOY-BETA\n"
        "    - TOY-GAMMA\n"
        "---\n\n# critique-toy\n"
    )
    frontmatter = parse_skill_frontmatter(text)
    assert frontmatter["judged"] == ["TOY-BETA", "TOY-GAMMA"]
    assert frontmatter["rubrics"] == ["TOY"]
    assert frontmatter["version"] == "0.1.0"


def test_parse_skill_frontmatter_derives_rubrics_from_criterion_namespace_not_rubric_sources_id() -> None:
    """critique-microcopy and critique-usability are the real-world case this guards: their
    rubric_sources[].id values ("NNG-EM", "NNG-HEURISTICS") are not the criterion namespace
    ("NNG") every finding's rubrics-cover-findings check actually needs."""
    text = (
        "---\n"
        "name: critique-microcopy\n"
        "version: 0.1.0\n"
        "rubric_sources:\n"
        "  - id: NNG-EM\n"
        "checks:\n"
        "  scripted:\n"
        "    - NNG-EM-TIMING\n"
        "  judged:\n"
        "    - NNG-EM-PROXIMITY\n"
        "---\n\n# critique-microcopy\n"
    )
    frontmatter = parse_skill_frontmatter(text)
    assert frontmatter["rubrics"] == ["NNG"]


def test_parse_skill_frontmatter_missing_block_raises() -> None:
    with pytest.raises(ValueError, match="frontmatter"):
        parse_skill_frontmatter("# no frontmatter here\n")


def test_load_skill_frontmatter_against_the_real_critique_clarity_skill() -> None:
    """What survives of build_judged_system_prompt(): the harness still needs the declared
    version and rubric namespaces to fill in an envelope's run block, but no longer assembles a
    judged-lane prompt, because the real skill now runs instead."""
    frontmatter = run_bench.load_skill_frontmatter("critique-clarity")

    assert frontmatter["version"]
    assert frontmatter["rubrics"] == ["PLAIN", "WILLIAMS"]
    assert frontmatter["judged"], "critique-clarity declares judged criteria"


# ---------------------------------------------------------------------------
# Baseline (postprocess) path
# ---------------------------------------------------------------------------


def test_call_baseline_lane_sends_prompt_txt_and_artifact_with_no_system_prompt() -> None:
    client = FakeClient([FakeResponse("No problems found.")])

    raw_text = call_baseline_lane(client, model_id="claude-sonnet-5", artifact_text="Document body.")

    assert raw_text == "No problems found."
    call = client.messages.calls[0]
    assert "system" not in call
    assert "Document body." in call["messages"][0]["content"]
    assert "critiquing a single document" in call["messages"][0]["content"]


def test_execute_baseline_cell_matches_calling_postprocess_directly(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "bench" / "corpus"
    artifact = _write_corpus_artifact(corpus_dir, "clarity", "clarity-001", "Body text.\n")
    cell = GridCell(
        condition="baseline",
        skill="baseline-generic",
        artifact=artifact,
        tier=Tier(alias="sonnet", model_id="claude-sonnet-5"),
        run_index=1,
        out_path=tmp_path / "out.json",
    )
    raw_response = "No problems found."
    client = FakeClient([FakeResponse(raw_response)])

    envelope, raw_text = execute_baseline_cell(cell, client=client, repo_root=tmp_path, max_tokens=1024, now_fn=_now)

    assert raw_text == raw_response
    expected = baseline_postprocess(
        raw_response, artifact=artifact.path, artifact_sha256=artifact.sha256, model="claude-sonnet-5", timestamp=FIXED_TIMESTAMP
    )
    assert envelope == expected
    result = validate_document(envelope)
    assert result.ok, result.errors


# ---------------------------------------------------------------------------
# execute_grid: the full pipeline, scripted and judged lanes both faked
# ---------------------------------------------------------------------------


def _toy_envelope_from_skill(criterion: str = "TOY-ALPHA", severity: int = 2) -> dict[str, Any]:
    """What the real skill returns now: a complete envelope, both lanes already merged and
    bounded by the skill itself. The `run` block is deliberately wrong here, because the harness
    overwrites it with provenance the skill is never told."""
    return {
        "run": {
            "skill": "critique-toy",
            "skill_version": "0.0.0",
            "contract_version": "1.0.0",
            "artifact": "toy-001.md",
            "artifact_sha256": "0" * 64,
            "model": "whatever-the-skill-thought",
            "timestamp": "2020-01-01T00:00:00Z",
            "rubrics": ["TOY"],
        },
        "findings": [
            {
                "id": "F-001",
                "criterion": criterion,
                "lane": "scripted",
                "severity": severity,
                "location": "p1",
                "evidence": "e",
                "violation": "v",
                "fix": "f",
                "confidence": "high",
            }
        ],
        "summary": {
            "by_severity": {str(i): (1 if i == severity else 0) for i in range(5)},
            "gate": "pass",
            "severity_3_threshold": 0,
            "suppressed_count": 0,
        },
    }


def test_execute_grid_writes_a_contract_valid_envelope_per_cell_and_a_raw_txt_for_baseline(tmp_path: Path) -> None:
    _write_fake_skill(tmp_path, "critique-toy", scripted=["TOY-ALPHA"], judged=["TOY-BETA"])
    corpus_dir = tmp_path / "bench" / "corpus"
    _write_corpus_artifact(corpus_dir, "toy", "toy-001", "Body one.\n")
    out_dir = tmp_path / "runs"
    tiers = [Tier(alias="haiku", model_id="claude-haiku-4-5-20251001")]
    cells = plan_grid(["critique-toy"], tiers, k=1, corpus_dir=corpus_dir, out_dir=out_dir)

    client = FakeClient(
        [
            FakeResponse(json.dumps(_toy_envelope_from_skill())),  # skill cell
            FakeResponse("No problems found."),  # baseline cell
        ]
    )

    results = execute_grid(cells, client=client, repo_root=tmp_path, now_fn=_now)

    assert all(r.ok for r in results), [r.detail for r in results if not r.ok]
    skill_path = out_dir / "critique-toy" / "toy-001" / "haiku-r1.json"
    baseline_path = out_dir / "baseline" / "toy" / "toy-001" / "haiku-r1.json"
    assert skill_path.is_file()
    assert baseline_path.is_file()
    assert baseline_path.with_name(baseline_path.name + ".raw.txt").is_file()
    assert not skill_path.with_name(skill_path.name + ".raw.txt").exists()

    skill_envelope = json.loads(skill_path.read_text(encoding="utf-8"))
    result = validate_document(skill_envelope)
    assert result.ok, result.errors
    assert skill_envelope["findings"][0]["criterion"] == "TOY-ALPHA"
    # The harness's provenance replaced the skill's placeholder run block.
    assert skill_envelope["run"]["artifact"] == "bench/corpus/toy/toy-001.md"
    assert skill_envelope["run"]["model"] == "claude-haiku-4-5-20251001"
    assert skill_envelope["run"]["timestamp"] == FIXED_TIMESTAMP


def test_execute_grid_a_failed_cell_does_not_stop_the_rest(tmp_path: Path) -> None:
    """A skill that cannot produce an envelope fails its own cell only. The baseline cell behind
    it must still run: a harness that aborts on the first bad cell throws away every good run."""
    _write_fake_skill(tmp_path, "critique-toy", scripted=["TOY-ALPHA"], judged=["TOY-BETA"])
    corpus_dir = tmp_path / "bench" / "corpus"
    _write_corpus_artifact(corpus_dir, "toy", "toy-001", "Body one.\n")
    out_dir = tmp_path / "runs"
    tiers = [Tier(alias="haiku", model_id="claude-haiku-4-5-20251001")]
    cells = plan_grid(["critique-toy"], tiers, k=1, corpus_dir=corpus_dir, out_dir=out_dir)

    client = FakeClient(
        [
            FakeResponse("I could not read that file, sorry."),  # skill cell: not an envelope
            FakeResponse("No problems found."),  # baseline cell
        ]
    )

    results = execute_grid(cells, client=client, repo_root=tmp_path, now_fn=_now)

    by_condition = {r.cell.condition: r for r in results}
    assert by_condition["skill"].ok is False
    assert "envelope" in by_condition["skill"].detail
    assert by_condition["baseline"].ok is True
    assert not (out_dir / "critique-toy" / "toy-001" / "haiku-r1.json").exists()


def test_execute_grid_rejects_an_artifact_whose_bytes_do_not_match_the_manifest_sha256(tmp_path: Path) -> None:
    """The sha256 guard moved into staging, which is where the artifact is now read. A run
    against different bytes is not a reproduction of anything."""
    _write_fake_skill(tmp_path, "critique-toy", scripted=["TOY-ALPHA"], judged=["TOY-BETA"])
    corpus_dir = tmp_path / "bench" / "corpus"
    artifact_ref = _write_corpus_artifact(corpus_dir, "toy", "toy-001", "Body one.\n")
    # Corrupt the artifact bytes on disk after the manifest recorded their hash.
    (tmp_path / artifact_ref.path).write_text("Tampered.\n", encoding="utf-8", newline="\n")
    out_dir = tmp_path / "runs"
    tiers = [Tier(alias="haiku", model_id="claude-haiku-4-5-20251001")]
    cells = plan_grid(["critique-toy"], tiers, k=1, corpus_dir=corpus_dir, out_dir=out_dir, include_baseline=False)

    # Empty: the cell must fail before it reaches a model at all.
    client = FakeClient([])

    results = execute_grid(cells, client=client, repo_root=tmp_path, now_fn=_now)

    assert len(results) == 1
    assert results[0].ok is False
    assert "sha256" in results[0].detail


# ---------------------------------------------------------------------------
# CLI: main()
# ---------------------------------------------------------------------------


def test_main_dry_run_needs_no_api_key_and_prints_the_planned_grid(monkeypatch, capsys) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    exit_code = main(["--skills", "critique-clarity", "--k", "1", "--dry-run"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "cell(s) planned" in out
    assert "[skill] critique-clarity" in out
    assert "[baseline]" in out


def test_main_dry_run_needs_neither_a_key_nor_the_cli(monkeypatch, capsys) -> None:
    """--dry-run stays secretless and dependency-light: no API key, and not even the Claude Code
    CLI, because it plans the grid without reaching a model at all (S-07 AC-3)."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
    # Fail the run loudly if anything tries to reach a model or probe for the CLI.
    monkeypatch.setattr(run_bench, "_client_factory", _forbid("_client_factory"))
    monkeypatch.setattr(run_bench, "_check_claude_cli", _forbid("_check_claude_cli"))

    exit_code = main(["--skills", "critique-clarity", "--k", "1", "--dry-run"])

    assert exit_code == 0


def test_main_rejects_k_below_one(capsys) -> None:
    exit_code = main(["--k", "0", "--dry-run"])

    assert exit_code == 2
    assert "--k must be at least 1" in capsys.readouterr().err


def test_main_rejects_an_unknown_tier_alias(capsys) -> None:
    exit_code = main(["--tiers", "opus", "--dry-run"])

    assert exit_code == 2
    assert "unknown tier alias" in capsys.readouterr().err


def test_main_live_without_the_cli_fails_loudly_and_names_the_remedy(monkeypatch, capsys) -> None:
    """A live run needs the Claude Code CLI, not an API key (ADR 0030). Absent it, the run must
    stop before planning anything and say what to do, rather than failing at the first model call.
    """
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(
        run_bench, "_check_claude_cli", lambda *a, **k: "the 'claude' CLI is required and is not on PATH."
    )
    monkeypatch.setattr(run_bench, "_client_factory", _forbid("_client_factory"))

    exit_code = main(["--skills", "critique-clarity", "--k", "1"])

    err = capsys.readouterr().err
    assert exit_code == 1
    assert "'claude' CLI is required" in err
    assert "ANTHROPIC_API_KEY" not in err, "the harness must not ask for an API key any more"


def test_main_live_with_no_matching_skills_does_nothing(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(run_bench, "_check_claude_cli", lambda *a, **k: None)
    monkeypatch.setattr(run_bench, "_client_factory", _forbid("_client_factory"))

    # A fresh --out-dir, because the default is the committed evidence directory and the
    # immutability guard would (correctly) refuse it. This test is about skill filtering.
    exit_code = main(["--skills", "no-such-skill", "--k", "1", "--out-dir", str(tmp_path / "runs")])

    assert exit_code == 0
    assert "nothing to do" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# The immutability guard
# ---------------------------------------------------------------------------


def test_a_live_run_refuses_to_write_over_committed_evidence(tmp_path, monkeypatch, capsys) -> None:
    """bench/results/runs*/ is immutable evidence, and the default --out-dir pointed straight at it.

    On 2026-08-08 a unit test whose precondition had changed fell through to the live path with
    default arguments and overwrote nine committed baseline envelopes. They were restored from git,
    but nothing had stopped it, and the published figures are recomputed from those files.
    """
    populated = tmp_path / "runs"
    (populated / "critique-clarity" / "clarity-001").mkdir(parents=True)
    (populated / "critique-clarity" / "clarity-001" / "haiku-r1.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(run_bench, "_check_claude_cli", lambda *a, **k: None)
    monkeypatch.setattr(run_bench, "_client_factory", _forbid("_client_factory"))

    exit_code = main(["--skills", "critique-clarity", "--k", "1", "--out-dir", str(populated)])

    err = capsys.readouterr().err
    assert exit_code == 1
    assert "already contains 1 envelope" in err
    assert "immutable measurement evidence" in err


def test_a_live_run_accepts_a_fresh_out_dir(tmp_path, monkeypatch, capsys) -> None:
    """The guard must not make a legitimate re-measurement awkward: an empty or absent
    directory needs no ceremony."""
    monkeypatch.setattr(run_bench, "_check_claude_cli", lambda *a, **k: None)
    monkeypatch.setattr(run_bench, "_client_factory", _forbid("_client_factory"))

    # No matching skill, so the run stops before any model call; the guard must not fire first.
    exit_code = main(["--skills", "no-such-skill", "--k", "1", "--out-dir", str(tmp_path / "fresh")])

    assert exit_code == 0
    assert "nothing to do" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Ground-truth isolation: staging an artifact away from its manifest
# ---------------------------------------------------------------------------
#
# These matter more than they look. Until the fidelity half of ADR 0030, the judged lane read the
# artifact's TEXT and inlined it into a prompt, so the model had no filesystem and the corpus layout
# was irrelevant. Running the REAL skill through `claude --plugin-dir` changes that: the critic
# declares Read and Bash, and the skill's own protocol tells it to run `scripts/checks.py <artifact>`
# against a real path. `bench/corpus/<domain>/<id>.manifest.json` is the complete seeded-defect
# answer key, and it sits directly beside `<id>.md`.
#
# bench/generator/README.md's leak rule already covers artifact content and path naming, on the
# stated grounds that "the artifact path is handed to the skill under test". It does not cover a
# sibling answer key, because nothing could read one until now.


def _corpus_with_manifest(tmp_path: Path) -> tuple[Path, ArtifactRef]:
    """A miniature corpus laid out the way bench/corpus/ actually is: artifact and answer key
    side by side in one directory."""
    corpus = tmp_path / "bench" / "corpus" / "clarity"
    corpus.mkdir(parents=True)
    # write_bytes, not write_text: on Windows write_text translates \n to \r\n, and the real corpus
    # is LF on disk (.gitattributes enforces it, after every recorded example hash was once wrong
    # for exactly this reason). The manifest sha256 is over the bytes, so the fixture must match.
    body = b"# Home-Office Equipment Stipend Policy\n\nEligibility is described below.\n"
    (corpus / "clarity-001.md").write_bytes(body)
    (corpus / "clarity-001.manifest.json").write_bytes(
        json.dumps({"defects": [{"criterion": "PLAIN-DOUBLE-NEGATIVE", "severity_expected": 2}]}).encode("utf-8")
    )

    artifact = ArtifactRef(
        domain="clarity",
        path="bench/corpus/clarity/clarity-001.md",
        sha256=hashlib.sha256(body).hexdigest(),
        artifact_type="markdown-prose",
    )
    return corpus, artifact


def test_staged_artifact_directory_holds_the_artifact_and_nothing_else(tmp_path) -> None:
    """The seeded-defect manifest must not be reachable from the staged artifact's directory.

    Without this, a judged lane running the real skill could read the answer key it is being
    measured against, and every score it produced would be worthless.
    """
    _, artifact = _corpus_with_manifest(tmp_path)

    with run_bench.staged_artifact(artifact, repo_root=tmp_path) as staged:
        siblings = sorted(p.name for p in staged.parent.iterdir())

    assert siblings == ["clarity-001.md"], f"staged directory leaked {siblings}"


def test_staged_artifact_is_byte_identical_to_the_corpus_copy(tmp_path) -> None:
    """A run against different bytes is not a reproduction of anything, so staging must not
    normalise line endings or re-encode. The manifest sha256 is checked against the staged file."""
    corpus, artifact = _corpus_with_manifest(tmp_path)

    with run_bench.staged_artifact(artifact, repo_root=tmp_path) as staged:
        assert staged.read_bytes() == (corpus / "clarity-001.md").read_bytes()


def test_staged_artifact_keeps_the_opaque_corpus_filename(tmp_path) -> None:
    """Corpus ids are opaque sequential slugs precisely because the path reaches the skill
    (bench/generator/README.md, leak rule 4), so the real filename is safe and keeping it means
    a failing cell can be traced back to its artifact."""
    _, artifact = _corpus_with_manifest(tmp_path)

    with run_bench.staged_artifact(artifact, repo_root=tmp_path) as staged:
        assert staged.name == "clarity-001.md"


def test_staged_artifact_is_removed_on_exit(tmp_path) -> None:
    """A k=5 grid over six skills stages hundreds of copies; leaving them behind fills the disk."""
    _, artifact = _corpus_with_manifest(tmp_path)

    with run_bench.staged_artifact(artifact, repo_root=tmp_path) as staged:
        staged_dir = staged.parent
        assert staged_dir.exists()

    assert not staged_dir.exists()


def test_staged_artifact_rejects_bytes_that_do_not_match_the_manifest(tmp_path) -> None:
    """The existing _read_artifact sha256 guard must survive the rewrite: staging is where the
    artifact is now read, so it is where the check has to happen."""
    corpus, artifact = _corpus_with_manifest(tmp_path)
    (corpus / "clarity-001.md").write_text("tampered\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="does not match manifest"):
        with run_bench.staged_artifact(artifact, repo_root=tmp_path):
            pass


# ---------------------------------------------------------------------------
# Transport: the two constraints ADR 0030 says are easiest to break by accident
# ---------------------------------------------------------------------------


class _FakeProc:
    def __init__(self, stdout: str = "{}", returncode: int = 0) -> None:
        self.stdout = stdout
        self.stderr = ""
        self.returncode = returncode


def _capture_claude_calls(monkeypatch, stdout: str = "{}") -> list[dict[str, Any]]:
    """Record every subprocess invocation the transport makes, without running one."""
    calls: list[dict[str, Any]] = []

    def _fake_run(argv, **kwargs):
        calls.append({"argv": list(argv), **kwargs})
        return _FakeProc(stdout=stdout)

    monkeypatch.setattr(run_bench.subprocess, "run", _fake_run)
    return calls


def test_transport_passes_plugin_dir_model_and_cwd_and_never_bare(tmp_path, monkeypatch) -> None:
    """ADR 0030 names both failure modes explicitly.

    `--bare` reads "strictly ANTHROPIC_API_KEY or apiKeyHelper (OAuth and keychain are never
    read)", so passing it silently reintroduces the API key this whole ADR exists to delete.
    Omitting `--model` makes the run inherit whatever model the caller happens to be using, which
    measures nothing reproducible. Both were comments until now.
    """
    calls = _capture_claude_calls(monkeypatch)

    run_bench._ClaudeCodeMessages().create(
        model="claude-haiku-4-5-20251001",
        messages=[{"role": "user", "content": "critique ./clarity-001.md"}],
        plugin_dir=tmp_path / "repo",
        cwd=tmp_path / "staged",
    )

    argv = calls[0]["argv"]
    assert "--bare" not in argv, "--bare silently reintroduces ANTHROPIC_API_KEY"
    assert argv[argv.index("--model") + 1] == "claude-haiku-4-5-20251001"
    assert argv[argv.index("--plugin-dir") + 1] == str(tmp_path / "repo")
    assert calls[0]["cwd"] == str(tmp_path / "staged")


def test_transport_omits_plugin_dir_for_the_frozen_baseline_lane(monkeypatch) -> None:
    """The baseline condition is frozen: a generic prompt with no skill and no plugin loaded.
    Loading the plugin for it would make the baseline stop being a baseline."""
    calls = _capture_claude_calls(monkeypatch)

    run_bench._ClaudeCodeMessages().create(
        model="claude-haiku-4-5-20251001",
        messages=[{"role": "user", "content": "review this"}],
    )

    argv = calls[0]["argv"]
    assert "--plugin-dir" not in argv
    assert argv[argv.index("--model") + 1] == "claude-haiku-4-5-20251001"


# ---------------------------------------------------------------------------
# The judged lane, running the real skill instead of a reimplementation of it
# ---------------------------------------------------------------------------


_ENVELOPE_FROM_SKILL = {
    "run": {
        "skill": "critique-clarity",
        "skill_version": "0.1.0",
        "contract_version": "1.0.0",
        "artifact": "clarity-001.md",
        "artifact_sha256": "0" * 64,
        "model": "whatever-the-skill-thought",
        "timestamp": "2020-01-01T00:00:00Z",
        "rubrics": ["PLAIN"],
    },
    "findings": [
        {
            "id": "F-001",
            "criterion": "PLAIN-DOUBLE-NEGATIVE",
            "severity": 2,
            "location": "Eligibility, second paragraph",
            "evidence": "not uncommon",
            "violation": "Two negation markers in one clause.",
            "fix": "State it positively.",
            "lane": "scripted",
            "confidence": "high",
        }
    ],
    "summary": {
        "by_severity": {"0": 0, "1": 0, "2": 1, "3": 0, "4": 0},
        "gate": "pass",
        "severity_3_threshold": 0,
        "suppressed_count": 0,
    },
}


def test_skill_lane_returns_the_envelope_the_skill_emitted(monkeypatch, tmp_path) -> None:
    """The point of the fidelity half: the harness stops assembling findings and merely
    transports the envelope the real skill produced."""
    _capture_claude_calls(monkeypatch, stdout=json.dumps(_ENVELOPE_FROM_SKILL))

    envelope = run_bench.call_skill_lane(
        run_bench.ClaudeCodeClient(),
        model_id="claude-haiku-4-5-20251001",
        skill="critique-clarity",
        staged_path=tmp_path / "clarity-001.md",
        repo_root=tmp_path,
    )

    assert envelope["findings"][0]["criterion"] == "PLAIN-DOUBLE-NEGATIVE"
    assert envelope["summary"]["gate"] == "pass"


def test_skill_lane_accepts_a_fenced_envelope(monkeypatch, tmp_path) -> None:
    """Models wrap JSON in a code fence regardless of instruction. The old judged lane already
    stripped fences, and dropping that would turn a formatting habit into a failed cell."""
    fenced = "```json\n" + json.dumps(_ENVELOPE_FROM_SKILL) + "\n```"
    _capture_claude_calls(monkeypatch, stdout=fenced)

    envelope = run_bench.call_skill_lane(
        run_bench.ClaudeCodeClient(),
        model_id="claude-haiku-4-5-20251001",
        skill="critique-clarity",
        staged_path=tmp_path / "clarity-001.md",
        repo_root=tmp_path,
    )

    assert envelope["findings"][0]["severity"] == 2


def test_skill_lane_rejects_a_response_that_is_not_an_envelope(monkeypatch, tmp_path) -> None:
    """A cell that cannot produce an envelope must fail loudly and be recorded as a failed cell,
    never written as a partial or invented one."""
    _capture_claude_calls(monkeypatch, stdout="I had trouble reading that file, sorry.")

    with pytest.raises(JudgedLaneError):
        run_bench.call_skill_lane(
            run_bench.ClaudeCodeClient(),
            model_id="claude-haiku-4-5-20251001",
            skill="critique-clarity",
            staged_path=tmp_path / "clarity-001.md",
            repo_root=tmp_path,
        )


def test_skill_lane_names_the_skill_and_the_staged_file_in_its_prompt(monkeypatch, tmp_path) -> None:
    """The instruction must name the skill (so the right one runs) and the staged filename (so
    the corpus path, and therefore the sibling manifest, is never mentioned)."""
    calls = _capture_claude_calls(monkeypatch, stdout=json.dumps(_ENVELOPE_FROM_SKILL))

    run_bench.call_skill_lane(
        run_bench.ClaudeCodeClient(),
        model_id="claude-haiku-4-5-20251001",
        skill="critique-clarity",
        staged_path=tmp_path / "staged" / "clarity-001.md",
        repo_root=tmp_path,
    )

    prompt = calls[0]["input"]
    assert "critique-clarity" in prompt
    assert "clarity-001.md" in prompt
    assert "bench/corpus" not in prompt, "the corpus path must never reach the skill"


def _clarity_cell(tmp_path: Path, artifact: ArtifactRef) -> GridCell:
    return GridCell(
        condition="skill",
        skill="critique-clarity",
        artifact=artifact,
        tier=Tier(alias="haiku", model_id="claude-haiku-4-5-20251001"),
        run_index=1,
        out_path=tmp_path / "out" / "haiku-r1.json",
    )


_CLARITY_FRONTMATTER = {
    "version": "0.1.0",
    "rubrics": ["PLAIN", "WILLIAMS"],
    "scripted": ["PLAIN-SENTENCE-LENGTH"],
    "judged": ["PLAIN-DOUBLE-NEGATIVE"],
}


def test_execute_skill_cell_keeps_the_skills_measurement_and_owns_the_provenance(tmp_path) -> None:
    """The split the fidelity half introduces: `findings` and `summary` are the skill's, because
    the skill is what is being measured, and the `run` block is the harness's, because the skill
    is deliberately never told the corpus path, the pinned model id, or the run timestamp."""
    _, artifact = _corpus_with_manifest(tmp_path)
    client = FakeClient([FakeResponse(json.dumps(_ENVELOPE_FROM_SKILL))])

    envelope = run_bench.execute_skill_cell(
        _clarity_cell(tmp_path, artifact),
        client=client,
        repo_root=tmp_path,
        frontmatter=_CLARITY_FRONTMATTER,
        now_fn=_now,
    )

    assert envelope["run"]["artifact"] == "bench/corpus/clarity/clarity-001.md"
    assert envelope["run"]["artifact_sha256"] == artifact.sha256
    assert envelope["run"]["model"] == "claude-haiku-4-5-20251001"
    assert envelope["run"]["timestamp"] == FIXED_TIMESTAMP
    assert envelope["run"]["skill"] == "critique-clarity"
    assert envelope["run"]["skill_version"] == "0.1.0"
    assert envelope["run"]["rubrics"] == ["PLAIN", "WILLIAMS"]

    assert envelope["findings"] == _ENVELOPE_FROM_SKILL["findings"]
    assert envelope["summary"] == _ENVELOPE_FROM_SKILL["summary"]


def test_execute_skill_cell_never_leaks_a_staging_path_into_the_envelope(tmp_path) -> None:
    """Envelopes are committed evidence. A temp path would make them non-reproducible and would
    publish the running user's home directory into a public repository."""
    _, artifact = _corpus_with_manifest(tmp_path)
    client = FakeClient([FakeResponse(json.dumps(_ENVELOPE_FROM_SKILL))])

    envelope = run_bench.execute_skill_cell(
        _clarity_cell(tmp_path, artifact),
        client=client,
        repo_root=tmp_path,
        frontmatter=_CLARITY_FRONTMATTER,
        now_fn=_now,
    )

    assert "bench-artifact-" not in json.dumps(envelope)
    assert str(tmp_path) not in json.dumps(envelope)


def test_execute_skill_cell_runs_the_skill_against_the_staged_copy(tmp_path) -> None:
    """The manifest must not be in the directory the skill is pointed at."""
    _, artifact = _corpus_with_manifest(tmp_path)
    client = FakeClient([FakeResponse(json.dumps(_ENVELOPE_FROM_SKILL))])

    run_bench.execute_skill_cell(
        _clarity_cell(tmp_path, artifact),
        client=client,
        repo_root=tmp_path,
        frontmatter=_CLARITY_FRONTMATTER,
        now_fn=_now,
    )

    call = client.messages.calls[0]
    assert call["plugin_dir"] == tmp_path
    assert Path(call["cwd"]).name.startswith("bench-artifact-")


def test_skill_lane_passes_a_non_default_gate_threshold_to_the_skill(monkeypatch, tmp_path) -> None:
    """--severity-3-threshold has to keep meaning what it says. The skill now builds its own
    summary, so the harness can no longer stamp the threshold on afterwards; it must pass it in
    through the interface agents/critique-critic.md already documents ("a gate threshold; 0 when
    omitted")."""
    calls = _capture_claude_calls(monkeypatch, stdout=json.dumps(_ENVELOPE_FROM_SKILL))

    run_bench.call_skill_lane(
        run_bench.ClaudeCodeClient(),
        model_id="claude-haiku-4-5-20251001",
        skill="critique-clarity",
        staged_path=tmp_path / "clarity-001.md",
        repo_root=tmp_path,
        severity_3_threshold=2,
    )

    assert "severity_3_threshold" in calls[0]["input"]
    assert "2" in calls[0]["input"]


def test_skill_lane_stays_silent_about_the_threshold_when_it_is_the_default(monkeypatch, tmp_path) -> None:
    """Every committed envelope was measured at the default. Mentioning it anyway would change
    the prompt for every historical cell and make the re-run non-comparable."""
    calls = _capture_claude_calls(monkeypatch, stdout=json.dumps(_ENVELOPE_FROM_SKILL))

    run_bench.call_skill_lane(
        run_bench.ClaudeCodeClient(),
        model_id="claude-haiku-4-5-20251001",
        skill="critique-clarity",
        staged_path=tmp_path / "clarity-001.md",
        repo_root=tmp_path,
        severity_3_threshold=0,
    )

    assert "severity_3_threshold" not in calls[0]["input"]

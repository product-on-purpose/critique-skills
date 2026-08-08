"""Tests for bench/run_bench.py: grid planning, the scripted-plus-judged lane merge and
bounding, envelope validity, judged-lane response parsing, and the baseline (postprocess) path.

No test in this file makes a network call. Every Anthropic API call is a fake client object
implementing the same `client.messages.create(**kwargs) -> response` shape the real SDK does
(response.content is a list of objects carrying `.text`), matching this module's own
`_response_text` helper.
"""

from __future__ import annotations

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
    ScriptedLaneError,
    Tier,
    _parse_judged_findings,
    _response_text,
    assemble_merged_envelope,
    build_judged_system_prompt,
    call_baseline_lane,
    call_judged_lane,
    declared_skills,
    discover_skill_artifacts,
    execute_baseline_cell,
    execute_grid,
    format_grid,
    main,
    merge_lanes,
    parse_skill_frontmatter,
    plan_grid,
    resolve_filter,
    resolve_tiers,
    run_scripted_lane_subprocess,
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
    build_judged_system_prompt / execute_grid never need to read the real repository's skills
    tree or write into it."""
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


def test_build_judged_system_prompt_against_the_real_critique_clarity_skill() -> None:
    system_prompt, frontmatter = build_judged_system_prompt("critique-clarity")
    assert frontmatter["judged"] == [
        "PLAIN-AUDIENCE",
        "PLAIN-CONSISTENT-TERMS",
        "PLAIN-MAIN-IDEA-FIRST",
        "PLAIN-ORGANIZE",
        "WILLIAMS-CHARACTER-ACTION",
        "WILLIAMS-COHERENCE",
        "WILLIAMS-COHESION",
        "WILLIAMS-STRESS",
    ]
    assert frontmatter["rubrics"] == ["PLAIN", "WILLIAMS"]
    assert "PLAIN-AUDIENCE" in system_prompt
    assert "critique-clarity" in system_prompt
    # references/*.md content is folded in
    assert "PLAIN.md" in system_prompt
    assert "WILLIAMS.md" in system_prompt


# ---------------------------------------------------------------------------
# Judged-lane response parsing
# ---------------------------------------------------------------------------


def test_response_text_concatenates_text_blocks() -> None:
    response = FakeResponse("hello world")
    assert _response_text(response) == "hello world"


def test_response_text_ignores_non_text_attribute_and_dict_blocks() -> None:
    class Response:
        content = [{"type": "text", "text": "a"}, FakeTextBlock("b")]

    assert _response_text(Response()) == "ab"


def test_parse_judged_findings_well_formed_response() -> None:
    text = json.dumps(
        {
            "findings": [
                {
                    "criterion": "PLAIN-AUDIENCE",
                    "severity": 3,
                    "location": "Section 1",
                    "evidence": "quoted text",
                    "violation": "breach",
                    "fix": "do this",
                    "confidence": "high",
                }
            ]
        }
    )
    findings = _parse_judged_findings(text, allowed_criteria={"PLAIN-AUDIENCE"})
    assert len(findings) == 1
    assert findings[0]["lane"] == "judged"
    assert findings[0]["severity"] == 3
    assert findings[0]["confidence"] == "high"


def test_parse_judged_findings_strips_a_markdown_code_fence() -> None:
    text = '```json\n{"findings": []}\n```'
    assert _parse_judged_findings(text, allowed_criteria=set()) == []


def test_parse_judged_findings_drops_a_criterion_outside_the_judged_list() -> None:
    text = json.dumps(
        {
            "findings": [
                {
                    "criterion": "PLAIN-ACTIVE",  # a scripted criterion, not in the judged allowlist
                    "severity": 2,
                    "location": "L",
                    "evidence": "E",
                    "violation": "V",
                    "fix": "F",
                }
            ]
        }
    )
    assert _parse_judged_findings(text, allowed_criteria={"PLAIN-AUDIENCE"}) == []


def test_parse_judged_findings_drops_an_unparseable_severity() -> None:
    text = json.dumps(
        {"findings": [{"criterion": "PLAIN-AUDIENCE", "severity": "catastrophic", "location": "L", "evidence": "E", "violation": "V", "fix": "F"}]}
    )
    assert _parse_judged_findings(text, allowed_criteria={"PLAIN-AUDIENCE"}) == []


def test_parse_judged_findings_drops_a_finding_missing_a_required_field() -> None:
    text = json.dumps(
        {"findings": [{"criterion": "PLAIN-AUDIENCE", "severity": 2, "location": "L", "evidence": "E", "violation": "V"}]}
    )
    assert _parse_judged_findings(text, allowed_criteria={"PLAIN-AUDIENCE"}) == []


def test_parse_judged_findings_sanitizes_em_and_en_dashes() -> None:
    text = json.dumps(
        {
            "findings": [
                {
                    "criterion": "PLAIN-AUDIENCE",
                    "severity": 2,
                    "location": "L",
                    "evidence": "before" + chr(0x2014) + "after",
                    "violation": "V",
                    "fix": "F",
                }
            ]
        }
    )
    findings = _parse_judged_findings(text, allowed_criteria={"PLAIN-AUDIENCE"})
    assert chr(0x2014) not in findings[0]["evidence"]
    assert "before - after" == findings[0]["evidence"]


def test_parse_judged_findings_not_json_raises_judged_lane_error() -> None:
    with pytest.raises(JudgedLaneError, match="not valid JSON"):
        _parse_judged_findings("this is not json at all", allowed_criteria=set())


def test_parse_judged_findings_missing_findings_key_raises() -> None:
    with pytest.raises(JudgedLaneError, match="findings"):
        _parse_judged_findings(json.dumps({"other": []}), allowed_criteria=set())


def test_call_judged_lane_sends_system_and_artifact_and_returns_parsed_findings() -> None:
    response_text = json.dumps(
        {"findings": [{"criterion": "PLAIN-AUDIENCE", "severity": 2, "location": "L", "evidence": "E", "violation": "V", "fix": "F"}]}
    )
    client = FakeClient([FakeResponse(response_text)])

    findings = call_judged_lane(
        client,
        model_id="claude-haiku-4-5-20251001",
        system_prompt="SYSTEM",
        artifact_path="bench/corpus/clarity/clarity-001.md",
        artifact_text="Some text.",
        allowed_criteria=["PLAIN-AUDIENCE"],
    )

    assert len(findings) == 1
    call = client.messages.calls[0]
    assert call["system"] == "SYSTEM"
    assert call["model"] == "claude-haiku-4-5-20251001"
    assert "Some text." in call["messages"][0]["content"]


# ---------------------------------------------------------------------------
# Lane merge and bounding
# ---------------------------------------------------------------------------


def _scripted_finding(criterion: str, severity: int, location: str) -> dict[str, Any]:
    return {
        "criterion": criterion,
        "lane": "scripted",
        "severity": severity,
        "location": location,
        "evidence": "evidence",
        "violation": "violation",
        "fix": "fix",
        "confidence": "high",
    }


def _judged_finding(criterion: str, severity: int, location: str) -> dict[str, Any]:
    return {
        "criterion": criterion,
        "lane": "judged",
        "severity": severity,
        "location": location,
        "evidence": "evidence",
        "violation": "violation",
        "fix": "fix",
        "confidence": "medium",
    }


def test_merge_lanes_combines_both_lanes_with_fresh_sequential_ids() -> None:
    scripted = [_scripted_finding("TOY-A", 2, "p1")]
    judged = [_judged_finding("TOY-B", 3, "p2")]

    findings, suppressed, histogram = merge_lanes(scripted, judged)

    assert [f["id"] for f in findings] == ["F-001", "F-002"]
    assert suppressed == 0
    assert histogram == {"0": 0, "1": 0, "2": 1, "3": 1, "4": 0}
    lanes = {f["lane"] for f in findings}
    assert lanes == {"scripted", "judged"}


def test_merge_lanes_bounds_the_combined_pool_not_each_lane_separately() -> None:
    """Three low-severity scripted findings plus four low-severity judged findings is seven
    below-severity-3 findings combined; the output bound (skills/_shared/envelope.py,
    OUTPUT_BOUND_BELOW_SEVERITY_3 = 5) applies to the combined pool, not per lane, so two of the
    seven are suppressed regardless of which lane found them."""
    scripted = [_scripted_finding("TOY-A", 2, f"s{i}") for i in range(3)]
    judged = [_judged_finding("TOY-B", 2, f"j{i}") for i in range(4)]

    findings, suppressed, histogram = merge_lanes(scripted, judged)

    assert len(findings) == 5
    assert suppressed == 2
    assert histogram["2"] == 7


def test_merge_lanes_keeps_every_severity_3_and_4_finding_regardless_of_bound() -> None:
    scripted = [_scripted_finding("TOY-A", 4, f"s{i}") for i in range(6)]

    findings, suppressed, _histogram = merge_lanes(scripted, [])

    assert len(findings) == 6
    assert suppressed == 0


def test_merge_lanes_ranks_by_severity_descending() -> None:
    scripted = [_scripted_finding("TOY-A", 1, "s1")]
    judged = [_judged_finding("TOY-B", 4, "j1")]

    findings, _suppressed, _histogram = merge_lanes(scripted, judged)

    assert [f["severity"] for f in findings] == [4, 1]


# ---------------------------------------------------------------------------
# Envelope validity
# ---------------------------------------------------------------------------


def test_assemble_merged_envelope_is_contract_valid() -> None:
    envelope = assemble_merged_envelope(
        skill="critique-clarity",
        skill_version="0.1.0",
        artifact_path="bench/corpus/clarity/clarity-001.md",
        artifact_sha256="a" * 64,
        model="claude-sonnet-5",
        timestamp=FIXED_TIMESTAMP,
        rubrics=["PLAIN", "WILLIAMS"],
        scripted_findings=[_scripted_finding("PLAIN-ACTIVE", 2, "p1")],
        judged_findings=[_judged_finding("PLAIN-AUDIENCE", 3, "p2")],
    )
    result = validate_document(envelope)
    assert result.ok, result.errors


def test_assemble_merged_envelope_empty_both_lanes_is_a_clean_pass() -> None:
    envelope = assemble_merged_envelope(
        skill="critique-clarity",
        skill_version="0.1.0",
        artifact_path="bench/corpus/clarity/clarity-001.md",
        artifact_sha256="a" * 64,
        model="claude-sonnet-5",
        timestamp=FIXED_TIMESTAMP,
        rubrics=["PLAIN", "WILLIAMS"],
        scripted_findings=[],
        judged_findings=[],
    )
    result = validate_document(envelope)
    assert result.ok, result.errors
    assert envelope["summary"]["gate"] == "pass"
    assert envelope["findings"] == []


def test_assemble_merged_envelope_gate_fails_on_a_severity_3_judged_finding() -> None:
    envelope = assemble_merged_envelope(
        skill="critique-clarity",
        skill_version="0.1.0",
        artifact_path="bench/corpus/clarity/clarity-001.md",
        artifact_sha256="a" * 64,
        model="claude-sonnet-5",
        timestamp=FIXED_TIMESTAMP,
        rubrics=["PLAIN", "WILLIAMS"],
        scripted_findings=[],
        judged_findings=[_judged_finding("PLAIN-AUDIENCE", 3, "p1")],
    )
    assert envelope["summary"]["gate"] == "fail"


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
# Scripted lane subprocess
# ---------------------------------------------------------------------------


def test_run_scripted_lane_subprocess_against_the_real_critique_clarity_checks() -> None:
    """An integration check against the real, committed critique-clarity skill. `checks.py`
    lives under `repo_root/skills/critique-clarity/scripts/`, and the artifact must live inside
    `repo_root` too (skills/_shared/artifact.py's load_artifact requires it), so this test reads
    an existing committed corpus artifact rather than writing a fixture file: nothing here writes
    to the repository."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    artifact = repo_root / "bench" / "corpus" / "clarity" / "clarity-001.md"

    envelope = run_scripted_lane_subprocess("critique-clarity", artifact, repo_root=repo_root)

    assert envelope["run"]["skill"] == "critique-clarity"
    assert envelope["run"]["model"] == "none"
    assert envelope["run"]["artifact"] == "bench/corpus/clarity/clarity-001.md"
    assert all(f["lane"] == "scripted" for f in envelope["findings"])


def test_run_scripted_lane_subprocess_missing_skill_raises() -> None:
    with pytest.raises(ScriptedLaneError):
        run_scripted_lane_subprocess("critique-does-not-exist", Path("nope.md"), repo_root=Path(".").resolve())


# ---------------------------------------------------------------------------
# execute_grid: the full pipeline, scripted and judged lanes both faked
# ---------------------------------------------------------------------------


def _fake_scripted_ok(skill: str, artifact_disk_path: Path, *, repo_root: Path) -> dict[str, Any]:
    import hashlib

    sha256 = hashlib.sha256(Path(artifact_disk_path).read_bytes()).hexdigest()
    return {
        "run": {"skill": skill, "artifact_sha256": sha256},
        "findings": [
            {
                "id": "F-001",
                "criterion": "TOY-ALPHA",
                "lane": "scripted",
                "severity": 2,
                "location": "p1",
                "evidence": "e",
                "violation": "v",
                "fix": "f",
                "confidence": "high",
            }
        ],
    }


def test_execute_grid_writes_a_contract_valid_envelope_per_cell_and_a_raw_txt_for_baseline(tmp_path: Path) -> None:
    _write_fake_skill(tmp_path, "critique-toy", scripted=["TOY-ALPHA"], judged=["TOY-BETA"])
    corpus_dir = tmp_path / "bench" / "corpus"
    _write_corpus_artifact(corpus_dir, "toy", "toy-001", "Body one.\n")
    out_dir = tmp_path / "runs"
    tiers = [Tier(alias="haiku", model_id="claude-haiku-4-5-20251001")]
    cells = plan_grid(["critique-toy"], tiers, k=1, corpus_dir=corpus_dir, out_dir=out_dir)

    judged_response = FakeResponse(json.dumps({"findings": []}))
    baseline_response = FakeResponse("No problems found.")
    client = FakeClient([judged_response, baseline_response])

    results = execute_grid(cells, client=client, repo_root=tmp_path, run_scripted_fn=_fake_scripted_ok, now_fn=_now)

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


def test_execute_grid_a_failed_cell_does_not_stop_the_rest(tmp_path: Path) -> None:
    _write_fake_skill(tmp_path, "critique-toy", scripted=["TOY-ALPHA"], judged=["TOY-BETA"])
    corpus_dir = tmp_path / "bench" / "corpus"
    _write_corpus_artifact(corpus_dir, "toy", "toy-001", "Body one.\n")
    out_dir = tmp_path / "runs"
    tiers = [Tier(alias="haiku", model_id="claude-haiku-4-5-20251001")]
    cells = plan_grid(["critique-toy"], tiers, k=1, corpus_dir=corpus_dir, out_dir=out_dir)

    def broken_scripted(skill: str, artifact_disk_path: Path, *, repo_root: Path) -> dict[str, Any]:
        raise ScriptedLaneError("boom")

    client = FakeClient([FakeResponse("No problems found.")])  # only the baseline cell reaches the client

    results = execute_grid(cells, client=client, repo_root=tmp_path, run_scripted_fn=broken_scripted, now_fn=_now)

    by_condition = {r.cell.condition: r for r in results}
    assert by_condition["skill"].ok is False
    assert "boom" in by_condition["skill"].detail
    assert by_condition["baseline"].ok is True


def test_execute_grid_rejects_an_artifact_whose_bytes_do_not_match_the_manifest_sha256(tmp_path: Path) -> None:
    _write_fake_skill(tmp_path, "critique-toy", scripted=["TOY-ALPHA"], judged=["TOY-BETA"])
    corpus_dir = tmp_path / "bench" / "corpus"
    artifact_ref = _write_corpus_artifact(corpus_dir, "toy", "toy-001", "Body one.\n")
    # Corrupt the artifact bytes on disk after the manifest recorded their hash.
    (tmp_path / artifact_ref.path).write_text("Tampered.\n", encoding="utf-8", newline="\n")
    out_dir = tmp_path / "runs"
    tiers = [Tier(alias="haiku", model_id="claude-haiku-4-5-20251001")]
    cells = plan_grid(["critique-toy"], tiers, k=1, corpus_dir=corpus_dir, out_dir=out_dir, include_baseline=False)

    client = FakeClient([])

    results = execute_grid(cells, client=client, repo_root=tmp_path, run_scripted_fn=_fake_scripted_ok, now_fn=_now)

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

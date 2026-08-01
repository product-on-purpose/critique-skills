"""`python -m bench.metrics score --corpus DIR --runs DIR --out FILE
[--run-set NAME]`

Scores every contract-valid run envelope found under `--runs` against the
schema-valid manifests found under `--corpus`, joins an envelope to its
manifest on `run.artifact_sha256 == manifest.artifact_sha256`
(bench/README.md: "the join; the path is a convenience"), and writes a
`bench/results/results.schema.json`-valid `results.json` to `--out`.

`build_results` is the library entry point this CLI wraps; call it
directly from a test or another script to avoid the subprocess and
filesystem-write overhead of the CLI.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema

from bench.metrics import score

_MANIFEST_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "generator" / "manifest.schema.json"
_RESULTS_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "results" / "results.schema.json"


class ScoreError(Exception):
    """A corpus, runs, or assembly problem the CLI reports and exits on,
    as distinct from a programming error."""


@functools.lru_cache(maxsize=1)
def _manifest_validator() -> jsonschema.Draft202012Validator:
    schema = json.loads(_MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


@functools.lru_cache(maxsize=1)
def _results_validator() -> jsonschema.Draft202012Validator:
    schema = json.loads(_RESULTS_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def _load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    errors = sorted(_manifest_validator().iter_errors(data), key=str)
    if errors:
        raise ScoreError(f"{path}: not a schema-valid manifest: {errors[0].message}")
    return data


def _load_envelope(path: Path) -> dict[str, Any] | None:
    # Imported lazily so `python -m bench.metrics --help` does not pay for
    # importing the contract package, and so a circular-import surprise
    # at module load time cannot happen.
    from contract.validate import validate_document

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "dispositions" in data:
        return None  # a disposition log, or not a document at all; not scored
    result = validate_document(data)
    if not result.ok:
        raise ScoreError(f"{path}: not a contract-valid envelope: {result.errors[0]}")
    return data


def _read_artifact_text(repo_root: Path, manifest: dict[str, Any]) -> str:
    artifact_path = repo_root / manifest["artifact"]
    raw = artifact_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != manifest["artifact_sha256"]:
        raise ScoreError(
            f"{artifact_path}: sha256 {digest} does not match manifest "
            f"artifact_sha256 {manifest['artifact_sha256']}"
        )
    return raw.decode("utf-8")


def _discover_manifests(corpus_dir: Path) -> list[dict[str, Any]]:
    return [_load_manifest(p) for p in sorted(corpus_dir.rglob("*.manifest.json"))]


def _discover_envelopes(runs_dir: Path) -> list[dict[str, Any]]:
    envelopes: list[dict[str, Any]] = []
    for path in sorted(runs_dir.rglob("*.json")):
        if path.name == "results.json":
            continue
        env = _load_envelope(path)
        if env is not None:
            envelopes.append(env)
    return envelopes


GroupKey = tuple[str, str, str, str]  # (skill, skill_version, model, domain)


def _metric_value(mv: score.MetricValue) -> dict[str, Any]:
    return {"value": score.round3(mv.value), "numerator": mv.numerator, "denominator": mv.denominator}


def _consistency_value(mv: score.MetricValue, consistency_scores: list[score.ConsistencyScore]) -> dict[str, Any]:
    return {
        "value": score.round3(mv.value),
        "artifacts_with_pairs": mv.denominator,
        "total_pairs": sum(c.pairs for c in consistency_scores),
    }


def build_results(
    corpus_dir: Path,
    runs_dir: Path,
    *,
    run_set: str,
    generated_at: str,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Score every envelope under `runs_dir` against every manifest under
    `corpus_dir` and assemble a `results.schema.json`-valid document.

    Manifest and envelope discovery and validation happen here, at the
    I/O boundary; `bench.metrics.score` never reads a file. Artifact
    bytes are read once per distinct artifact (cached by sha256) even
    when several envelopes, or several groups, reference the same one.
    """
    repo_root = repo_root or Path.cwd()
    manifests = _discover_manifests(corpus_dir)
    by_sha = {m["artifact_sha256"]: m for m in manifests}
    envelopes = _discover_envelopes(runs_dir)

    artifact_text_cache: dict[str, str] = {}

    def text_for(m: dict[str, Any]) -> str:
        sha = m["artifact_sha256"]
        if sha not in artifact_text_cache:
            artifact_text_cache[sha] = _read_artifact_text(repo_root, m)
        return artifact_text_cache[sha]

    recall_groups: dict[GroupKey, list[score.ArtifactScore]] = {}
    location_recall_groups: dict[GroupKey, list[score.ArtifactScore]] = {}
    consistency_envelope_groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}

    for env in envelopes:
        run = env["run"]
        sha = run["artifact_sha256"]
        manifest = by_sha.get(sha)
        if manifest is None:
            continue  # no corpus artifact matches this envelope; not scorable
        key: GroupKey = (run["skill"], run["skill_version"], run["model"], manifest["domain"])
        text = text_for(manifest)
        recall_groups.setdefault(key, []).append(score.score_artifact(manifest, env, text))
        location_recall_groups.setdefault(key, []).append(score.score_artifact_location(manifest, env, text))

        consistency_key = (run["skill"], run["skill_version"], run["model"], sha)
        consistency_envelope_groups.setdefault(consistency_key, []).append(env)

    consistency_by_group: dict[GroupKey, list[score.ConsistencyScore]] = {}
    for (skill, skill_version, model, sha), envs in consistency_envelope_groups.items():
        manifest = by_sha[sha]
        cscore = score.score_consistency(manifest, envs, text_for(manifest))
        group_key: GroupKey = (skill, skill_version, model, manifest["domain"])
        consistency_by_group.setdefault(group_key, []).append(cscore)

    entries = []
    for key in sorted(recall_groups):
        skill, skill_version, model, domain = key
        artifact_scores = recall_groups[key]
        location_scores = location_recall_groups[key]
        consistency_scores = consistency_by_group.get(key, [])
        entries.append(
            {
                "skill": skill,
                "skill_version": skill_version,
                "model": model,
                "domain": domain,
                "artifact_type": artifact_scores[0].artifact_type,
                "artifacts_scored": len(artifact_scores),
                "unresolvable_claims": sum(s.unresolvable_claims for s in artifact_scores),
                "recall": _metric_value(score.aggregate_recall(artifact_scores)),
                "precision": _metric_value(score.aggregate_precision(artifact_scores)),
                "recall_location": _metric_value(score.aggregate_recall(location_scores)),
                "precision_location": _metric_value(score.aggregate_precision(location_scores)),
                "clean_fp_rate": _metric_value(score.aggregate_clean_fp_rate(artifact_scores)),
                "consistency": _consistency_value(score.aggregate_consistency(consistency_scores), consistency_scores),
                "consistency_exact": _consistency_value(
                    score.aggregate_consistency_exact(consistency_scores), consistency_scores
                ),
            }
        )

    results = {
        "results_version": "1.1.0",
        "run_set": run_set,
        "generated_at": generated_at,
        "entries": entries,
    }
    errors = sorted(_results_validator().iter_errors(results), key=str)
    if errors:
        raise ScoreError(f"internal error: assembled results.json is not schema-valid: {errors[0].message}")
    return results


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m bench.metrics", description="Score run envelopes against the bench corpus."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    score_cmd = sub.add_parser("score", help="Score envelopes under --runs against manifests under --corpus.")
    score_cmd.add_argument("--corpus", required=True, type=Path, help="Corpus root, e.g. bench/corpus")
    score_cmd.add_argument("--runs", required=True, type=Path, help="Run-set root, e.g. bench/results/<run-set>")
    score_cmd.add_argument("--out", required=True, type=Path, help="Where to write results.json")
    score_cmd.add_argument(
        "--run-set", default=None, help="Recorded run_set identifier; defaults to --runs' own directory name."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if args.command == "score":
        run_set = args.run_set or args.runs.name
        try:
            results = build_results(args.corpus, args.runs, run_set=run_set, generated_at=_now_iso())
        except ScoreError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(results, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        print(f"wrote {args.out} ({len(results['entries'])} entries)")
        return 0

    print(f"usage error: unknown command {args.command!r}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

"""`python -m bench.variance --corpus DIR --runs DIR --out FILE [--run-set NAME]`

Measures the run-to-run variance of the committed figures, and with it the acceptance band
[ADR 0030](../docs/internal/decisions/0030-replace-the-api-key-in-the-bench-harness.md)'s fidelity
gate needs in order to be failable at all.

**Why this exists.** ADR 0030 accepts the rewritten judged lane on "a partial re-run whose figures
land within measured run-to-run variance of the committed ones". No such variance figure existed.
`bench/results/results.json` pools every k=5 repetition and every artifact of a domain into one
cell figure, so each published number is a ratio of sums carrying no recorded spread, and a re-run
returning almost anything could have been declared faithful. This supplies the missing number.

**No model is called and nothing under `bench/results/runs*/` is read for anything but scoring.**
Like `bench/metrics`, this computes from committed envelopes and manifests and from nothing else.

## Method

Three steps, in order, because the third is worthless if the second does not hold.

1. **Scope.** Score the documented view: a run set minus any probe directories. `runs/steering/`
   holds two prompt-injection-resistance probes that share identity fields with the measurement
   grid and pool into `critique-clarity` / sonnet if included, which `bench/results/README.md`
   records as a known layout fragility and excludes by hand in its reproduction recipe. Excluding
   them here makes the recipe a default rather than a step someone must remember.

2. **Decompose, and prove the decomposition.** A committed envelope's filename carries its
   repetition index (`haiku-r3.json`); no contract field records it, which is the `run_set` and
   lane schema debt `ROADMAP.md` lists as v0.2.0 measurement debt, and it is why this parses paths.
   Regrouping on that index and pooling within one repetition yields k figures per cell where
   `results.json` has one, computed through the same `bench.metrics.score` calls `build_results`
   uses.

   Pooling every repetition back together must then reproduce the committed numerator and
   denominator exactly. **If any cell fails that, this refuses to emit a band**, because a
   decomposition that does not sum back to the published figure is measuring something else.

3. **Band.** The published statistic is `sum(numerators) / sum(denominators)` across repetitions
   and artifacts, not a mean of per-repetition ratios, so its sampling variation is estimated by
   resampling **whole repetitions** with replacement and recomputing the pooled ratio. Whole
   repetitions rather than individual artifact scores, because that is what preserves both the
   ratio-of-sums structure and the within-repetition correlation across artifacts.

## What the band does not cover

Stated here as well as in the ADR, because a number is easier to over-read than to re-derive.

- It is **within-run-set repetition variance only**. A fidelity re-run also differs in transport, in
  date, in staging and in isolation flags. Landing inside the band is necessary, not sufficient.
- **k=5 makes the bootstrap coarse.** Five repetitions admit at most 5**5 distinct resamples, so the
  band understates true uncertainty rather than overstating it.
- **Consistency is not banded and cannot be by this method.** `score.score_consistency` compares
  pairs of envelopes and is undefined for a single repetition, so the published 0.309 floor carries
  no uncertainty estimate. A band for it needs a different construction.
"""

from __future__ import annotations

import argparse
import functools
import json
import random
import re
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

import jsonschema

from bench.metrics import score

# Imported rather than reimplemented: manifest discovery, envelope loading and the artifact-hash
# check are the definition of "an envelope this project will score", and a second copy of that
# definition is exactly what ADR 0030 deleted from run_bench.py. Safe to import at module level
# because this module is executed as `python -m bench.variance`, so `bench.metrics.__main__` is
# imported under its real name exactly once; a subcommand living inside `bench.metrics` would
# instead have loaded that file a second time under the name `__main__`.
from bench.metrics.__main__ import (
    _discover_manifests,
    _load_envelope,
    _read_artifact_text,
)

VARIANCE_VERSION = "1.0.0"

_VARIANCE_SCHEMA_PATH = Path(__file__).resolve().parent / "results" / "variance.schema.json"

DEFAULT_DRAWS = 20000
DEFAULT_SEED = 20260815

# Probe run sets that share identity fields with the measurement grid. See the module docstring and
# bench/results/README.md, "Reproduction".
DEFAULT_EXCLUDED_TOP_LEVEL = ("steering",)

_REPETITION_RE = re.compile(r"^(?P<tier>[A-Za-z0-9.\-]+)-r(?P<repetition>\d+)$")

# (metric name, per-envelope scorer, aggregator over ArtifactScore)
_METRICS: tuple[tuple[str, Callable[..., Any], Callable[..., score.MetricValue]], ...] = (
    ("recall", score.score_artifact, score.aggregate_recall),
    ("precision", score.score_artifact, score.aggregate_precision),
    ("recall_location", score.score_artifact_location, score.aggregate_recall),
    ("precision_location", score.score_artifact_location, score.aggregate_precision),
)

# (run set, skill, skill_version, model, domain). The run set is part of the key because more than
# one committed run set can hold the same skill on the same tier, and pooling across them would
# band a figure nobody published. Every entry carries its own `run_set` for the same reason:
# `results.json` records one run_set for a file holding two, which ROADMAP.md lists as measurement
# debt, and there is no reason to repeat that here.
CellKey = tuple[str, str, str, str, str]


class VarianceError(Exception):
    """A scoping, decomposition or reproduction problem the CLI reports and exits on, as distinct
    from a programming error."""


@functools.lru_cache(maxsize=1)
def _variance_validator() -> jsonschema.Draft202012Validator:
    schema = json.loads(_VARIANCE_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def parse_repetition_index(path: Path) -> int | None:
    """The repetition index encoded in an envelope's filename, or None if it carries none.

    The index is a filesystem convention rather than a contract field, so this is deliberately the
    single place that knows it: when the schema debt is paid and a run records its own repetition,
    only this function has to change.
    """
    match = _REPETITION_RE.match(path.stem)
    return int(match.group("repetition")) if match else None


def scoring_view(runs_dir: Path, *, exclude_top: tuple[str, ...]) -> tuple[list[Path], list[Path]]:
    """Split every envelope path under `runs_dir` into (scored, excluded_as_probe)."""
    scored: list[Path] = []
    excluded: list[Path] = []
    for path in sorted(runs_dir.rglob("*.json")):
        if path.name in ("results.json", "variance.json"):
            continue
        top = path.relative_to(runs_dir).parts[0]
        (excluded if top in exclude_top else scored).append(path)
    return scored, excluded


def _percentile(sorted_values: list[float], fraction: float) -> float:
    index = int(round(fraction * (len(sorted_values) - 1)))
    return sorted_values[min(len(sorted_values) - 1, max(0, index))]


def bootstrap_band(
    totals_by_repetition: dict[int, tuple[int, int]],
    *,
    draws: int,
    rng: random.Random,
) -> tuple[float, float, float]:
    """Percentile band on the pooled statistic, resampling whole repetitions with replacement.

    `totals_by_repetition` maps a repetition index to that repetition's (numerator, denominator),
    already aggregated across the cell's artifacts. Returns (low, high, standard deviation).
    """
    repetitions = sorted(totals_by_repetition)
    k = len(repetitions)
    values: list[float] = []
    for _ in range(draws):
        numerator = denominator = 0
        for _ in range(k):
            drawn_numerator, drawn_denominator = totals_by_repetition[repetitions[rng.randrange(k)]]
            numerator += drawn_numerator
            denominator += drawn_denominator
        values.append(numerator / denominator if denominator else 0.0)
    values.sort()
    return _percentile(values, 0.025), _percentile(values, 0.975), statistics.pstdev(values)


def _group_scores(
    labelled_paths: list[tuple[str, Path]], corpus_dir: Path, repo_root: Path
) -> dict[CellKey, dict[str, dict[int, list[Any]]]]:
    """cell -> metric -> repetition index -> the artifact scores of that one repetition."""
    manifests = _discover_manifests(corpus_dir)
    by_sha = {m["artifact_sha256"]: m for m in manifests}
    artifact_text_cache: dict[str, str] = {}

    def text_for(manifest: dict[str, Any]) -> str:
        sha = manifest["artifact_sha256"]
        if sha not in artifact_text_cache:
            artifact_text_cache[sha] = _read_artifact_text(repo_root, manifest)
        return artifact_text_cache[sha]

    cells: dict[CellKey, dict[str, dict[int, list[Any]]]] = {}
    for run_set, path in labelled_paths:
        repetition = parse_repetition_index(path)
        if repetition is None:
            raise VarianceError(
                f"{path}: filename carries no repetition index. Envelope filenames are "
                "'<tier>-r<n>.json'; the repetition index is not a contract field, so a run set "
                "written under another convention cannot be decomposed."
            )
        envelope = _load_envelope(path)
        if envelope is None:
            continue
        run = envelope["run"]
        manifest = by_sha.get(run["artifact_sha256"])
        if manifest is None:
            continue  # no corpus artifact matches this envelope; not scorable, as in build_results
        key: CellKey = (run_set, run["skill"], run["skill_version"], run["model"], manifest["domain"])
        text = text_for(manifest)
        per_metric = cells.setdefault(key, {name: defaultdict(list) for name, _, _ in _METRICS})
        for name, scorer, _aggregator in _METRICS:
            per_metric[name][repetition].append(scorer(manifest, envelope, text))
    return cells


def _reproduction_failures(
    cells: dict[CellKey, dict[str, dict[int, list[Any]]]],
    committed_by_key: dict[tuple[str, str, str, str], dict[str, Any]],
) -> tuple[list[str], int, int]:
    """Every cell-metric whose repetitions do not pool back to the committed figure.

    Returns (failures, checked, matched). `checked` is reported so a run that silently matched
    nothing, because no committed entry lined up, cannot be mistaken for a run that verified
    everything.
    """
    failures: list[str] = []
    checked = matched = 0
    for key in sorted(cells):
        run_set, skill, skill_version, model, domain = key
        committed = committed_by_key.get((skill, skill_version, model, domain))
        if committed is None:
            continue  # a cell the committed file does not carry
        for name, _scorer, aggregator in _METRICS:
            per_repetition = cells[key][name]
            pooled = aggregator([s for r in sorted(per_repetition) for s in per_repetition[r]])
            want = committed[name]
            checked += 1
            if (pooled.numerator, pooled.denominator) == (want["numerator"], want["denominator"]):
                matched += 1
            else:
                failures.append(
                    f"[{run_set}] {skill} {skill_version} {model} {domain} {name}: repetitions "
                    f"pool to {pooled.numerator}/{pooled.denominator}, committed says "
                    f"{want['numerator']}/{want['denominator']}"
                )
    return failures, checked, matched


def build_variance(
    corpus_dir: Path,
    run_sets: Sequence[tuple[Path, str]],
    *,
    generated_at: str,
    repo_root: Path | None = None,
    exclude_top: tuple[str, ...] = DEFAULT_EXCLUDED_TOP_LEVEL,
    draws: int = DEFAULT_DRAWS,
    seed: int = DEFAULT_SEED,
    committed_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Decompose every committed run set by repetition and band each cell's pooled figure.

    `run_sets` pairs a run-set directory with the label recorded on its entries. Taking several at
    once is deliberate: `results.json` publishes two, and its documented reproduction recipe
    concatenates two files by hand, which is a step someone has to remember rather than a property
    of the tool.

    Raises `VarianceError` when a decomposition does not sum back to `committed_results`, so a band
    is never published on top of a decomposition that measures something other than what was
    published.
    """
    repo_root = repo_root or Path.cwd()
    labelled: list[tuple[str, Path]] = []
    excluded: list[str] = []
    for runs_dir, label in run_sets:
        scored, probes = scoring_view(runs_dir, exclude_top=exclude_top)
        labelled.extend((label, p) for p in scored)
        excluded.extend(p.relative_to(runs_dir).as_posix() for p in probes)
    cells = _group_scores(labelled, corpus_dir, repo_root)

    verification: dict[str, Any] = {"performed": False}
    if committed_results is not None:
        committed_by_key = {
            (e["skill"], e["skill_version"], e["model"], e["domain"]): e
            for e in committed_results["entries"]
        }
        failures, checked, matched = _reproduction_failures(cells, committed_by_key)
        if failures:
            raise VarianceError(
                "the per-repetition decomposition does not reproduce the committed figures, so no "
                "band is emitted:\n  " + "\n  ".join(failures)
            )
        if not checked:
            raise VarianceError(
                "no cell in these run sets matched an entry in the committed results, so the "
                "decomposition was not verified against anything. Check --corpus and --runs."
            )
        verification = {"performed": True, "cell_metrics_checked": checked, "cell_metrics_matched": matched}

    rng = random.Random(seed)
    entries: list[dict[str, Any]] = []
    for key in sorted(cells):
        run_set, skill, skill_version, model, domain = key
        for name, _scorer, aggregator in _METRICS:
            per_repetition = cells[key][name]
            repetitions = sorted(per_repetition)
            totals = {r: _totals(aggregator(per_repetition[r])) for r in repetitions}
            values = [n / d if d else 0.0 for n, d in totals.values()]
            pooled = aggregator([s for r in repetitions for s in per_repetition[r]])
            low, high, sd = bootstrap_band(totals, draws=draws, rng=rng)
            entries.append(
                {
                    "run_set": run_set,
                    "skill": skill,
                    "skill_version": skill_version,
                    "model": model,
                    "domain": domain,
                    "metric": name,
                    "k": len(repetitions),
                    "pooled": score.round3(pooled.value),
                    "per_repetition": [score.round3(v) for v in values],
                    "repetition_min": score.round3(min(values)),
                    "repetition_max": score.round3(max(values)),
                    "repetition_spread": score.round3(max(values) - min(values)),
                    "band_low": score.round3(low),
                    "band_high": score.round3(high),
                    "band_width": score.round3(high - low),
                    "bootstrap_sd": round(sd, 5),
                }
            )

    document = {
        "variance_version": VARIANCE_VERSION,
        "run_sets": [label for _dir, label in run_sets],
        "generated_at": generated_at,
        "method": {
            "estimator": "bootstrap over whole repetitions, resampled with replacement",
            "interval": "2.5th to 97.5th percentile",
            "draws": draws,
            "seed": seed,
            "repetition_index_source": "envelope filename, '<tier>-r<n>.json'; no contract field records it",
            "covers": "within-run-set repetition variance only, not transport, date, staging or isolation",
            "not_banded": "consistency and clean_fp_rate; score_consistency compares pairs and is undefined for one repetition",
        },
        "verification": verification,
        "envelopes_scored": len(labelled),
        "excluded_as_probe": sorted(excluded),
        "entries": entries,
    }
    errors = sorted(_variance_validator().iter_errors(document), key=str)
    if errors:
        raise VarianceError(f"internal error: assembled variance.json is not schema-valid: {errors[0].message}")
    return document


def _totals(metric: score.MetricValue) -> tuple[int, int]:
    return metric.numerator, metric.denominator


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m bench.variance",
        description="Measure run-to-run variance of committed figures and emit the acceptance band.",
    )
    parser.add_argument("--corpus", required=True, type=Path, help="Corpus root, e.g. bench/corpus")
    parser.add_argument(
        "--runs",
        required=True,
        action="append",
        type=Path,
        help="Run-set root, e.g. bench/results/runs. Repeat to band several run sets into one file.",
    )
    parser.add_argument("--out", required=True, type=Path, help="Where to write variance.json")
    parser.add_argument(
        "--run-set",
        action="append",
        default=None,
        help=(
            "Recorded run_set identifier, paired positionally with --runs. Omit to label each run "
            "set with its own directory name."
        ),
    )
    parser.add_argument(
        "--committed",
        type=Path,
        default=None,
        help=(
            "results.json to check the decomposition against. Strongly recommended: without it no "
            "reproduction check runs and the band is unverified."
        ),
    )
    parser.add_argument(
        "--exclude-top",
        default=",".join(DEFAULT_EXCLUDED_TOP_LEVEL),
        help=(
            "Comma-separated top-level directories under --runs to exclude as probe run sets "
            f"(default: {','.join(DEFAULT_EXCLUDED_TOP_LEVEL)}). Pass an empty string to exclude nothing."
        ),
    )
    parser.add_argument("--draws", type=int, default=DEFAULT_DRAWS, help="Bootstrap resamples.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Bootstrap seed, for reproducibility.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    exclude_top = tuple(s for s in args.exclude_top.split(",") if s)

    labels = args.run_set if args.run_set is not None else [d.name for d in args.runs]
    if len(labels) != len(args.runs):
        print(
            f"usage error: {len(args.runs)} --runs but {len(labels)} --run-set; they are paired "
            "positionally, so give one --run-set per --runs or none at all.",
            file=sys.stderr,
        )
        return 2
    run_sets = list(zip(args.runs, labels))

    committed = None
    if args.committed is not None:
        try:
            committed = json.loads(args.committed.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"error: cannot read {args.committed}: {exc}", file=sys.stderr)
            return 1

    try:
        results = build_variance(
            args.corpus,
            run_sets,
            generated_at=_now_iso(),
            exclude_top=exclude_top,
            draws=args.draws,
            seed=args.seed,
            committed_results=committed,
        )
    except VarianceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(results, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"wrote {args.out} ({len(results['entries'])} entries from {results['envelopes_scored']} envelopes)")
    if results["verification"]["performed"]:
        print(
            f"verified: {results['verification']['cell_metrics_matched']} of "
            f"{results['verification']['cell_metrics_checked']} cell-metrics pool back to the "
            "committed figures exactly"
        )
    else:
        print("warning: no --committed results.json given, so the decomposition was not verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""`python -m bench.report table --results FILE [--target FILE] [--check]`

Renders a `bench/results/results.schema.json`-valid `results.json` into
the markdown results tables `bench/README.md` publishes, replacing the
content between two marker comments in `--target` (default
`bench/README.md`) and leaving everything else in the file untouched.
`--check` recomputes the tables and compares them against what
`--target` currently holds, exiting 1 on drift without writing anything:
"No number appears in any document in this repository that is not present
in a committed `results.json`, and no table is hand-edited"
(bench/README.md, "Results").

`render_block` and `splice` are the library functions this CLI wraps; a
test (or another script) can call them directly.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

START_MARKER = "<!-- bench-results:start -->"
END_MARKER = "<!-- bench-results:end -->"


def _fmt_metric(metric_value: dict[str, Any]) -> str:
    value = metric_value["value"]
    return "n/a" if value is None else f"{value:.3f}"


def _fmt_value(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def render_entries_table(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return "_No run set has been scored yet._"
    header = (
        "| Skill | Version | Model | Domain | Artifact type | Artifact-runs (k=5) | Recall | Precision | "
        "Clean FP rate | Consistency | Consistency (exact) | Unresolvable |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|---|"
    )
    rows = [
        "| {skill} | {version} | {model} | {domain} | {artifact_type} | {n} | {recall} | {precision} | "
        "{fp} | {cons} | {cons_exact} | {unresolved} |".format(
            skill=e["skill"],
            version=e["skill_version"],
            model=e["model"],
            domain=e["domain"],
            artifact_type=e["artifact_type"],
            n=e["artifacts_scored"],
            recall=_fmt_metric(e["recall"]),
            precision=_fmt_metric(e["precision"]),
            fp=_fmt_metric(e["clean_fp_rate"]),
            cons=_fmt_metric(e["consistency"]),
            cons_exact=_fmt_metric(e["consistency_exact"]),
            unresolved=e["unresolvable_claims"],
        )
        for e in sorted(entries, key=lambda e: (e["domain"], e["skill"], e["skill_version"], e["model"]))
    ]
    return "\n".join([header, *rows])


BASELINE_SKILL = "baseline-generic"


def _by_domain_model(
    entries: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[tuple[str, str], dict[str, Any]]]:
    """`(domain, model)` to `(skill, skill_version)` to entry.

    Keyed on `(skill, skill_version)` rather than on the skill name alone
    because `results.json` may legitimately carry two versions of the
    same skill in the same `(domain, model)` cell: a run set that
    re-measures one skill after a calibration iteration holds the before
    and the after side by side, distinguished only by `skill_version`
    (`results.schema.json`: "one entry per (skill, skill_version, model,
    domain) group"). Keying on the name alone silently dropped whichever
    row was inserted first, which would have deleted a published failure
    from the comparison tables rather than showing it beside its fix.
    """
    by_domain_model: dict[tuple[str, str], dict[tuple[str, str], dict[str, Any]]] = {}
    for e in entries:
        by_domain_model.setdefault((e["domain"], e["model"]), {})[(e["skill"], e["skill_version"])] = e
    return by_domain_model


def _find_baseline(skills: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any] | None:
    """The `baseline-generic` entry in one `(domain, model)` cell, whatever
    version it carries. The baseline is frozen, so exactly one is expected;
    the lowest version is taken if a future run set ever holds more."""
    candidates = sorted((k for k in skills if k[0] == BASELINE_SKILL))
    return skills[candidates[0]] if candidates else None


def render_criterion_table(entries: list[dict[str, Any]]) -> str:
    """Each skill's own recall and precision against its own cited
    rubric, by `(domain, model)`. This is not a baseline comparison: a
    claim matches a planted defect only when its criterion string equals
    the defect's, `baseline-generic` carries the fixed criterion
    `BASELINE-GENERIC` (no manifest plants a defect under it, because a
    prompt with no rubric has nothing to cite), so a baseline column here
    would read exactly 0.000 in every row by construction, not by
    measurement, and a verdict column built on that column would be
    vacuous. Neither is rendered. What is meaningful at this level, and
    is rendered, is whether a skill's own criterion-tagged findings land
    on the planted defects, i.e. whether the rubric was operationalized.
    See `render_baseline_comparison_location` for the skill-versus-
    baseline comparison, which is not pinned this way.
    """
    rows: list[str] = []
    for (domain, model), skills in sorted(_by_domain_model(entries).items()):
        for skill_name, skill_version in sorted(skills):
            if skill_name == BASELINE_SKILL:
                continue
            entry = skills[(skill_name, skill_version)]
            rows.append(
                f"| {skill_name} | {skill_version} | {domain} | {model} | {_fmt_metric(entry['recall'])} | "
                f"{_fmt_metric(entry['precision'])} |"
            )

    if not rows:
        return "_No rubric-operationalization figures available yet._"
    header = "| Skill | Version | Domain | Model | Recall | Precision |\n|---|---|---|---|---|---|"
    return "\n".join([header, *rows])


def _tier_label(model: str) -> str:
    """A short tier name for a pinned model ID, for verdict prose only
    (`claude-haiku-4-5-20251001` to `haiku`). Falls back to the full
    model ID for any model this library has not pinned before, so a new
    tier degrades to a longer but still correct label instead of a wrong
    one."""
    lower = model.lower()
    for tier in ("haiku", "sonnet", "opus"):
        if tier in lower:
            return tier
    return model


def _dominance_verdict(
    skill_recall: float | None,
    baseline_recall: float | None,
    skill_precision: float | None,
    baseline_precision: float | None,
) -> str:
    """AC-6's own rule (`bench/results/verdicts.md`, "The gate"): a skill
    passes a tier by beating the baseline's recall at equal-or-better
    precision, or by tying recall and winning precision. Recall alone is
    not enough: `critique-usability` on sonnet wins recall (0.857 against
    0.829) while losing precision (0.169 against 0.181), which is a
    dominance loss even though the recall column alone would read as a
    win (bench/results/README.md, "Core skills, S-05 AC-6"). Anything
    that does not dominate on at least one metric while losing nothing
    on the other reads as a flat loss; anything that wins one metric and
    loses the other reads as a mixed non-pass, distinct from a flat
    loss, so a reader is not told a skill lost everything when it only
    lost precision."""
    if skill_recall is None or baseline_recall is None or skill_precision is None or baseline_precision is None:
        return "n/a"
    if skill_recall > baseline_recall and skill_precision >= baseline_precision:
        return "beats baseline"
    if skill_recall == baseline_recall and skill_precision >= baseline_precision:
        return "ties baseline"
    if skill_recall <= baseline_recall and skill_precision <= baseline_precision:
        return "below baseline"
    return "no pass on this tier"


_QUALIFYING_VERDICTS = ("beats baseline", "ties baseline")


def render_baseline_comparison_location(entries: list[dict[str, Any]]) -> str:
    """The fair skill-versus-baseline comparison: reads `recall_location`
    and `precision_location`, where a claim matches a planted defect when
    its location resolves within the artifact type's tolerance, criterion
    ID ignored entirely (`bench/metrics/score.py`,
    `score_artifact_location`). Unlike the criterion-level cut, the
    baseline is not pinned at 0.000 by construction here, and in several
    cells below it is the baseline, not the skill, that reads the higher
    number.

    The verdict is decided by `_dominance_verdict`, which reads both
    columns, not recall alone: a tier that wins recall but loses
    precision is a mixed non-pass ("no pass on this tier"), not a win.
    When a row reads that way, this function looks at the same skill's
    other pinned tier for the same domain and version; if that tier
    passes, the row is annotated "(qualifies via <tier>)" so a reader
    sees the skill still ships without mistaking the failing tier for a
    pass (`bench/results/README.md`, "Core skills, S-05 AC-6": "passes on
    haiku only, ... not a pass on either reading" for the sonnet cell).
    """
    raw_rows: list[dict[str, Any]] = []
    for (domain, model), skills in sorted(_by_domain_model(entries).items()):
        baseline = _find_baseline(skills)
        if baseline is None:
            continue
        for skill_name, skill_version in sorted(skills):
            if skill_name == BASELINE_SKILL:
                continue
            entry = skills[(skill_name, skill_version)]
            raw_rows.append(
                {
                    "skill": skill_name,
                    "version": skill_version,
                    "domain": domain,
                    "model": model,
                    "recall": entry["recall_location"]["value"],
                    "baseline_recall": baseline["recall_location"]["value"],
                    "precision": entry["precision_location"]["value"],
                    "baseline_precision": baseline["precision_location"]["value"],
                }
            )

    if not raw_rows:
        return "_No baseline comparison available yet._"

    verdicts = {
        (r["skill"], r["version"], r["domain"], r["model"]): _dominance_verdict(
            r["recall"], r["baseline_recall"], r["precision"], r["baseline_precision"]
        )
        for r in raw_rows
    }

    def _qualifying_sibling_tier(row: dict[str, Any]) -> str | None:
        for other in raw_rows:
            if other["model"] == row["model"]:
                continue
            if (other["skill"], other["version"], other["domain"]) != (row["skill"], row["version"], row["domain"]):
                continue
            if verdicts[(other["skill"], other["version"], other["domain"], other["model"])] in _QUALIFYING_VERDICTS:
                return _tier_label(other["model"])
        return None

    rows: list[str] = []
    for r in raw_rows:
        verdict = verdicts[(r["skill"], r["version"], r["domain"], r["model"])]
        if verdict == "no pass on this tier":
            sibling_tier = _qualifying_sibling_tier(r)
            if sibling_tier is not None:
                verdict = f"no pass on this tier (qualifies via {sibling_tier})"
        rows.append(
            f"| {r['skill']} | {r['version']} | {r['domain']} | {r['model']} | "
            f"{_fmt_value(r['recall'])} | {_fmt_value(r['baseline_recall'])} | "
            f"{_fmt_value(r['precision'])} | {_fmt_value(r['baseline_precision'])} | {verdict} |"
        )

    header = (
        "| Skill | Version | Domain | Model | Skill recall (location) | Baseline recall (location) | "
        "Skill precision (location) | Baseline precision (location) | Verdict |"
        "\n|---|---|---|---|---|---|---|---|---|"
    )
    return "\n".join([header, *rows])


def render_block(results: dict[str, Any]) -> str:
    """The full marker-to-marker text `--target` should hold for this
    `results.json`, markers included. An empty `entries[]` (no run set
    scored yet) renders a short placeholder rather than a "Run set
    `none`, generated 1970-01-01..." line built from filler values."""
    entries = results.get("entries", [])
    if not entries:
        return "\n".join(
            [
                START_MARKER,
                "<!-- Generated by `python -m bench.report table`. Do not edit by hand: run "
                "`python -m bench.metrics score` for a run set, then regenerate. -->",
                "",
                "_No run set has been scored yet._",
                END_MARKER,
            ]
        )
    return "\n".join(
        [
            START_MARKER,
            "<!-- Generated by `python -m bench.report table`. Do not edit by hand: edit "
            f"`bench/results/{results.get('run_set', '<run-set>')}/results.json` and regenerate. -->",
            "",
            f"Run set `{results.get('run_set', '?')}`, generated {results.get('generated_at', '?')}.",
            "",
            "**Baseline comparison (location-level, criterion ignored).** The fair cross-condition "
            "comparison, first because it is the one the baseline could actually have failed; not "
            "pinned at 0.000. A skill passes a tier by beating baseline recall at equal-or-better "
            "precision, or by tying recall and winning precision; a tier that wins one metric and "
            "loses the other reads \"no pass on this tier\", annotated with the sibling tier that "
            "qualifies the skill if one does. See bench/results/README.md, \"Baseline comparison\", "
            "and bench/results/verdicts.md, \"The gate\".",
            "",
            render_baseline_comparison_location(entries),
            "",
            "**Full per-run figures.** Every skill, baseline, model, and domain in this run set; "
            "the location-level table above and the rubric-operationalization table below are both "
            "derived from these rows.",
            "",
            render_entries_table(entries),
            "",
            "**Rubric operationalization (criterion-level).** Each skill's own recall and precision "
            "against its own cited criteria; not a baseline comparison. `baseline-generic` has no "
            "rubric to cite, so none of its claims can ever match a planted defect's criterion string "
            "and its criterion-level recall and precision are structurally 0.000 in every row, not "
            "measured; it is omitted from this table rather than shown as a comparison it cannot "
            "lose. See bench/results/README.md, \"Baseline comparison\".",
            "",
            render_criterion_table(entries),
            END_MARKER,
        ]
    )


def splice(target_text: str, block: str) -> str:
    """Replace the marker-to-marker region of `target_text` with `block`
    (which itself starts and ends with the markers), leaving everything
    else untouched. Raises ValueError if the markers are not present."""
    if START_MARKER not in target_text or END_MARKER not in target_text:
        raise ValueError(
            f"{START_MARKER} / {END_MARKER} not found in target; add the pair once before "
            "this command can update it"
        )
    before = target_text.split(START_MARKER, 1)[0]
    after = target_text.split(END_MARKER, 1)[1]
    return before + block + after


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m bench.report", description="Render bench results.json into markdown result tables."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    table_cmd = sub.add_parser("table", help="Render results.json into the markdown results tables.")
    table_cmd.add_argument("--results", required=True, type=Path, help="Path to a results.json")
    table_cmd.add_argument(
        "--target", type=Path, default=Path("bench/README.md"), help="Markdown file to update (default bench/README.md)"
    )
    table_cmd.add_argument(
        "--check", action="store_true", help="Compare against --target instead of writing; exit 1 on drift."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if args.command != "table":
        print(f"usage error: unknown command {args.command!r}", file=sys.stderr)
        return 1

    try:
        results = json.loads(args.results.read_text(encoding="utf-8"))
    except OSError as exc:
        print(f"usage error: cannot read {args.results}: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"usage error: {args.results} is not valid JSON: {exc}", file=sys.stderr)
        return 1

    if not args.target.exists():
        print(f"error: target file {args.target} does not exist", file=sys.stderr)
        return 1
    target_text = args.target.read_text(encoding="utf-8")

    block = render_block(results)
    try:
        new_text = splice(target_text, block)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.check:
        if new_text != target_text:
            print(f"drift: {args.target} does not match the table regenerated from {args.results}", file=sys.stderr)
            return 1
        print("no drift")
        return 0

    with args.target.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(new_text)
    print(f"updated {args.target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""E5: no run.model value outside the two pinned tiers appears under skills/ or examples/,
unless it is a documented sentinel ("none" for no judged lane, "illustrative" for a hand-authored
envelope with a judged-lane finding that no measured model run produced).

Golden fixtures (skills/**/examples/golden-*.json) and the examples/<domain>/envelope.json files
were hand-authored at build time; several carried claude-sonnet-4-5-20250929, a model ID that was
never actually pinned for a run (bench/results/measurement-manifest.json's "models" array is the
only source of truth for what was). This test is what keeps that from drifting back in: it walks
every JSON file under skills/ and examples/, finds every embedded run envelope's run.model value
wherever it sits (top level or nested, for example under expected_envelope), and fails naming each
file whose value is neither a pinned model ID, "none", nor "illustrative".
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]


def find_run_models(root: Path) -> list[tuple[Path, Any]]:
    """Walk every *.json file under `root` and return (file, model_value) for every run.model
    found, at any depth, so a fixture that nests its envelope under a different key (the way a
    golden fixture nests it under expected_envelope) is still discovered."""
    found: list[tuple[Path, Any]] = []
    if not root.is_dir():
        return found
    for path in sorted(root.rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            continue
        for model_value in _models_in(data):
            found.append((path, model_value))
    return found


def _models_in(obj: Any) -> list[Any]:
    values: list[Any] = []
    if isinstance(obj, dict):
        run = obj.get("run")
        if isinstance(run, dict) and "model" in run:
            values.append(run["model"])
        for v in obj.values():
            values.extend(_models_in(v))
    elif isinstance(obj, list):
        for item in obj:
            values.extend(_models_in(item))
    return values


def _pinned_model_ids() -> set[str]:
    manifest_path = REPO_ROOT / "bench" / "results" / "measurement-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    ids = {entry["id"] for entry in manifest["models"]}
    assert ids, "measurement-manifest.json's models[] contributed no pinned model ids"
    return ids


DOCUMENTED_SENTINELS = {"none", "illustrative"}


def test_pinned_model_ids_are_not_vacuous() -> None:
    """A manifest read that silently returned nothing would make the main test below check
    only the two sentinels, passing even if every pinned tier vanished from the allowed set."""
    assert _pinned_model_ids() == {"claude-haiku-4-5-20251001", "claude-sonnet-5"}


def test_walker_finds_a_non_trivial_number_of_envelopes() -> None:
    """A path bug in find_run_models (wrong root, wrong key) must not make the provenance test
    below pass by finding nothing. 35 run envelopes are known to exist under skills/ and
    examples/ as of this test's writing; the floor is set well under that so the test does not
    need to move every time a fixture is added."""
    total = len(find_run_models(REPO_ROOT / "skills")) + len(find_run_models(REPO_ROOT / "examples"))
    assert total >= 30, f"expected at least 30 run envelopes under skills/ and examples/, found {total}"


def test_every_run_model_is_pinned_or_a_documented_sentinel() -> None:
    allowed = _pinned_model_ids() | DOCUMENTED_SENTINELS
    offenders = []
    for subdir in ("skills", "examples"):
        for path, model_value in find_run_models(REPO_ROOT / subdir):
            if model_value not in allowed:
                offenders.append(f"{path.relative_to(REPO_ROOT).as_posix()}: run.model={model_value!r}")
    assert not offenders, "run.model outside the pinned tiers or a documented sentinel:\n" + "\n".join(
        offenders
    )


def test_canary_bad_model_value_is_caught(tmp_path: Path) -> None:
    """Proves the walker actually looks at the value, not just that the key exists: a synthetic
    fixture with an unpinned, undocumented model value must be found, and that value must fail
    the allowed-set check the same way a real offending file would."""
    bad_file = tmp_path / "fixtures" / "golden-99.json"
    bad_file.parent.mkdir(parents=True)
    bad_file.write_text(
        json.dumps(
            {
                "kind": "golden",
                "expected_envelope": {
                    "run": {"model": "gpt-4-not-a-pinned-tier"},
                    "findings": [],
                    "summary": {},
                },
            }
        ),
        encoding="utf-8",
    )

    found = find_run_models(tmp_path)

    assert found == [(bad_file, "gpt-4-not-a-pinned-tier")]
    allowed = _pinned_model_ids() | DOCUMENTED_SENTINELS
    assert "gpt-4-not-a-pinned-tier" not in allowed

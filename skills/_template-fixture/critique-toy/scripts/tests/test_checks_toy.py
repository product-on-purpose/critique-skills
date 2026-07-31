"""Tests for this fixture skill's scripts/checks.py scripted lane:
TOY-ACTIVE, TOY-HEDGE, TOY-ORPHAN.

what-it-is:   the unit suite for the template fixture's scripted lane
what-it-does: exercises each TOY-* check against small in-memory
              artifacts plus the three committed toy corpus documents
why:          the template requires pytest coverage of every scripted
              check, and this fixture is the template's worked example
used-by:      `python -m pytest`, and `scripts/skill-selftest.py`'s own
              pytest check when it validates this directory

The module basename carries the skill's domain (`_toy`) on purpose: two
skills shipping `scripts/tests/test_checks.py` collide at pytest
collection time and abort the whole repository run. See
`scripts/skill-selftest.py`'s `check_test_module_names`.

`critique-toy` (like every real `skills/critique-<domain>/`
directory) has a hyphen in its own directory name, so `checks.py` cannot
be reached with a normal `import` statement: Python identifiers cannot
contain a hyphen, and no dotted path names this directory. It is loaded
here by file path via `importlib.util`, the same technique
`scripts/skill-selftest.py`'s own `_load_module` uses to load a skill's
checks.py for the lane-manifest-consistency check, and the same reason
`scripts/checks.py`'s own bootstrap puts the repository root on
`sys.path` unconditionally rather than assuming pytest already did.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from skills._shared.artifact import Artifact

_CHECKS_PATH = Path(__file__).resolve().parents[1] / "checks.py"


def _find_repo_root(start: Path) -> Path:
    """Walk up to the directory holding library.json, the repository's
    own marker file, rather than counting parents. A fixed parent count
    silently reads the wrong directory the moment the skill moves; this
    is the same rationale as `scripts/checks.py`'s bootstrap.
    """
    for candidate in (start, *start.parents):
        if (candidate / "library.json").is_file():
            return candidate
    raise RuntimeError("could not locate the repository root (no library.json found above this file)")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve())


def _load_checks_module():
    spec = importlib.util.spec_from_file_location("toy_fixture_checks_under_test", _CHECKS_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


checks = _load_checks_module()


def _artifact(text: str) -> Artifact:
    return Artifact(path="fixture.md", text=text, sha256="0" * 64, disk_path=Path("fixture.md"))


CLEAN_TEXT = """# Field operations notice

## Service window

The field crew reviews the meter log before the shift ends. Crews that finish early return the vehicle to the depot and record the mileage.
"""


def test_clean_artifact_has_no_findings():
    findings = checks.check(_artifact(CLEAN_TEXT))
    assert findings == []


def test_hedge_is_flagged():
    text = """# Field operations notice

## Service window

It may possibly be the case that the field crew reviews the meter log before the shift ends. Crews that finish early return the vehicle to the depot and record the mileage.
"""
    findings = checks.check(_artifact(text))
    criteria = [f.criterion for f in findings]
    assert "TOY-HEDGE" in criteria
    assert "TOY-ACTIVE" not in criteria
    hedge = next(f for f in findings if f.criterion == "TOY-HEDGE")
    assert hedge.severity == 2
    assert hedge.lane == "scripted"
    assert hedge.confidence == "high"
    assert "Service window" in hedge.location


def test_passive_recast_is_flagged():
    text = """# Field operations notice

## Service window

The meter log is reviewed before the shift ends. Crews that finish early return the vehicle to the depot and record the mileage.
"""
    findings = checks.check(_artifact(text))
    criteria = [f.criterion for f in findings]
    assert "TOY-ACTIVE" in criteria
    assert "TOY-HEDGE" not in criteria
    active = next(f for f in findings if f.criterion == "TOY-ACTIVE")
    assert active.severity == 2
    assert active.evidence == "The meter log is reviewed before the shift ends."


def test_orphan_heading_is_flagged():
    text = """# Field operations notice

## Service window

The field crew reviews the meter log before the shift ends. Crews that finish early return the vehicle to the depot and record the mileage.

### Escalation
"""
    findings = checks.check(_artifact(text))
    criteria = [f.criterion for f in findings]
    assert "TOY-ORPHAN" in criteria
    orphan = next(f for f in findings if f.criterion == "TOY-ORPHAN")
    assert orphan.severity == 3
    assert "Escalation" in orphan.location


def test_document_title_heading_is_never_flagged_as_orphan():
    """The level-1 document title is always immediately followed by the
    first section heading in the toy grammar (bench/generator/domains/
    toy.py, compose()), with no paragraph of its own beneath it. It must
    not be flagged, or every clean artifact in the corpus would carry a
    false TOY-ORPHAN finding."""
    findings = checks.check(_artifact(CLEAN_TEXT))
    assert all(f.criterion != "TOY-ORPHAN" for f in findings)


def test_a_subheading_with_a_body_is_not_orphan():
    text = """# Field operations notice

## Service window

The field crew reviews the meter log before the shift ends. Crews that finish early return the vehicle to the depot and record the mileage.

### Escalation

The duty engineer closes the rate table before the shift ends. Adjustments raised after that point land in the following cycle.
"""
    findings = checks.check(_artifact(text))
    assert all(f.criterion != "TOY-ORPHAN" for f in findings)


def test_multiple_defects_in_one_artifact_are_all_reported():
    text = """# Field operations notice

## Service window

It may possibly be the case that the field crew reviews the meter log before the shift ends. Crews that finish early return the vehicle to the depot and record the mileage.

## Meter replacement

The meter log is closed within one business day. Crews that finish early return the vehicle to the depot and record the mileage.

### Escalation
"""
    findings = checks.check(_artifact(text))
    criteria = sorted(f.criterion for f in findings)
    assert criteria == ["TOY-ACTIVE", "TOY-HEDGE", "TOY-ORPHAN"]


def test_empty_artifact_has_no_findings():
    findings = checks.check(_artifact(""))
    assert findings == []


def test_real_corpus_clean_recipe_produces_no_findings():
    """bench/corpus/toy/toy-003.md is the toy domain's own clean recipe
    (plants=()); a correct scripted lane finds nothing in it."""
    text = (_REPO_ROOT / "bench" / "corpus" / "toy" / "toy-003.md").read_text(encoding="utf-8")
    findings = checks.check(_artifact(text))
    assert findings == []


def test_real_corpus_seeded_artifacts_recover_the_planted_criteria():
    """Cross-checks the scripted lane against bench/corpus/toy/toy-001.md
    and toy-002.md, whose manifests are this domain's own ground truth
    (bench/corpus/toy/toy-00N.manifest.json). Not a substitute for the
    bench harness's own recall metric; a cheap sanity check that this
    skill's scripted lane is not silently blind to the seeded corpus.
    """
    expectations = {
        "toy-001.md": {"TOY-ACTIVE", "TOY-HEDGE"},
        "toy-002.md": {"TOY-ACTIVE", "TOY-HEDGE", "TOY-ORPHAN"},
    }
    for filename, expected_criteria in expectations.items():
        text = (_REPO_ROOT / "bench" / "corpus" / "toy" / filename).read_text(encoding="utf-8")
        findings = checks.check(_artifact(text))
        found_criteria = {f.criterion for f in findings}
        assert expected_criteria <= found_criteria, (filename, found_criteria)

"""Scripted-lane precision guard for critique-accessibility's bench corpus: on every
live accessibility artifact, the scripted lane's own findings equal the planted
scripted-lane defects, nothing more and nothing less.

what-it-is:   a corpus-level precision guard, run from bench/ rather than from the
              skill's own scripts/tests/, because it reads bench/corpus/ manifests to
              decide what checks.py is allowed to report on each artifact
what-it-does: for every live bench/corpus/accessibility/*.manifest.json (bench/corpus/
              _frozen/ is a separate, never-regenerated snapshot and is out of scope
              here; see bench/corpus/_frozen/README.md), loads checks.py by file path,
              the same technique skills/critique-accessibility/scripts/tests/
              test_checks_accessibility.py uses, and asserts that the multiset of
              criteria it reports on that artifact equals the multiset of planted
              defects whose criterion is in checks.py's own IMPLEMENTED_CRITERIA. A
              Counter, not a set, so a second unplanted finding on an already-planted
              criterion still fails this test even though the set of criteria would
              look unchanged.
why:          E67 (accessibility expansion) found the regression this test exists to
              catch: every live artifact, the clean accessibility-004 included, had an
              email and a phone field with no autocomplete token, so the new
              WCAG-1.3.5 scripted check fired on every artifact once it shipped, not
              only where a defect was actually planted. The corpus fix (the shared
              builder now sets both tokens, gives the status card role="status", and
              gives the promo-code error span aria-live="polite") removed those base
              defects; this test is the regression guard that a future unplanted
              scripted finding, on any criterion, fails loudly here rather than only
              costing precision in a published number.
used-by:      `python -m pytest bench -q`
"""

from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import pytest

from skills._shared.artifact import Artifact


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "library.json").is_file():
            return candidate
    raise RuntimeError("could not locate the repository root (no library.json found above this file)")


REPO_ROOT = _find_repo_root(Path(__file__).resolve())
_CHECKS_PATH = REPO_ROOT / "skills" / "critique-accessibility" / "scripts" / "checks.py"
_CORPUS_DIR = REPO_ROOT / "bench" / "corpus" / "accessibility"


def _load_checks_module():
    spec = importlib.util.spec_from_file_location("accessibility_checks_under_test_bench", _CHECKS_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


checks = _load_checks_module()


def _artifact(path: Path) -> Artifact:
    text = path.read_text(encoding="utf-8")
    return Artifact(path=path.as_posix(), text=text, sha256="0" * 64, disk_path=path)


# Non-recursive by construction: Path.glob("*.manifest.json") never descends into
# bench/corpus/_frozen/, which sits under bench/corpus/, not under this directory.
_LIVE_MANIFEST_PATHS = sorted(_CORPUS_DIR.glob("*.manifest.json"))


def test_live_manifests_were_found():
    assert _LIVE_MANIFEST_PATHS, f"expected at least one live manifest under {_CORPUS_DIR}"


@pytest.mark.parametrize("manifest_path", _LIVE_MANIFEST_PATHS, ids=lambda p: p.stem)
def test_scripted_findings_equal_planted_scripted_defects(manifest_path):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifact_path = REPO_ROOT / manifest["artifact"]

    planted = Counter(
        defect["criterion"] for defect in manifest["defects"] if defect["criterion"] in checks.IMPLEMENTED_CRITERIA
    )
    emitted = Counter(finding.criterion for finding in checks.check(_artifact(artifact_path)))

    assert emitted == planted, (
        f"{manifest_path.name}: checks.py reported {dict(emitted)} but only "
        f"{dict(planted)} is planted and scripted; an unplanted (or over-counted) "
        "scripted finding costs precision against this bench's conservative rule "
        "(bench/README.md, 'Invariants'), the same way the pre-E67 autocomplete gap did"
    )

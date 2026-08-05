# what-it-is:   the guard on every recorded skill-example artifact hash
# what-it-does: recomputes sha256 over each artifact named by a skills/*/examples/*.json fixture
#               and asserts it equals the artifact_sha256 that fixture records
# why:          the hashes are evidence, and a checkout that rewrites line endings silently
#               invalidates all of them while the repository itself stays correct
# used-by:      python -m pytest (the CI unit-python job)
"""Tests that every skill example fixture's ``artifact_sha256`` is true on disk.

These hashes were recorded once, when each fixture was authored, and nothing
verified them afterwards. That left a defect that is invisible from inside the
repository: git stores the artifacts with LF, and a Windows checkout with
``core.autocrlf=true`` expands them to CRLF, so the bytes on disk stop matching
the recorded hash while the bytes in git still match it perfectly. Every one of
the 22 fixtures was in that state before ``.gitattributes`` grew its
``skills/*/examples/** -text`` rule.

The rule is the fix; this test is what keeps the fix. It fails on a checkout
whose line endings have been rewritten, on an artifact edited without
re-recording its hash, and on a fixture pointing at a path that does not exist.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _fixtures() -> list[Path]:
    # Recursive: a nested fixture tree (skills/_template-fixture/critique-toy/examples/) records
    # hashes on the same terms as a top-level skill and must be guarded on the same terms.
    return sorted(REPO_ROOT.glob("skills/**/examples/*.json"))


def _recorded(fixture: Path) -> tuple[str, str] | None:
    """Return (artifact_path, sha256) for a fixture that records one, else None."""
    try:
        data = json.loads(fixture.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    run = (data.get("expected_envelope") or {}).get("run") or {}
    artifact, sha = run.get("artifact"), run.get("artifact_sha256")
    if isinstance(artifact, str) and isinstance(sha, str):
        return artifact, sha
    return None


def test_fixtures_are_discoverable() -> None:
    """A glob that silently matches nothing would make every other test here vacuous."""
    assert _fixtures(), "expected at least one skills/*/examples/*.json fixture"


@pytest.mark.parametrize("fixture", _fixtures(), ids=lambda p: f"{p.parent.parent.name}/{p.name}")
def test_recorded_artifact_hash_matches_disk(fixture: Path) -> None:
    recorded = _recorded(fixture)
    if recorded is None:
        pytest.skip(f"{fixture.name} records no artifact_sha256")
    artifact_rel, expected = recorded

    artifact = REPO_ROOT / artifact_rel
    assert artifact.is_file(), f"{fixture.name} names a missing artifact: {artifact_rel}"

    raw = artifact.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual == expected:
        return

    # A mismatch that disappears under LF normalization is the line-ending defect specifically,
    # not an edited artifact, so say which one it is rather than leaving it to be guessed.
    if hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest() == expected:
        pytest.fail(
            f"{artifact_rel}: the recorded hash matches the LF form but the file on disk has CRLF. "
            "This checkout rewrote line endings. Confirm `.gitattributes` carries "
            "`skills/*/examples/** -text`, then refresh the working tree so the artifacts are "
            "restored byte-for-byte from git."
        )
    pytest.fail(
        f"{artifact_rel}: content does not match the hash recorded in {fixture.name} "
        f"(recorded {expected[:12]}..., actual {actual[:12]}...). If the artifact was changed "
        "deliberately, re-record artifact_sha256 in that fixture."
    )

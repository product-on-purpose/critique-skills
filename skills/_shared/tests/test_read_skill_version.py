"""Tests for skills/_shared/merge.py's read_skill_version, the one reader of a skill's version.

Standard sec 3.7 places the version under `metadata` (the toolkit's U16 makes a top-level one an
error from Standard 0.14). Two callers depend on reading it right: merge.py stamps it into every
envelope a user sees, and bench/run_bench.py files every result under it. The second once defaulted
a missing version to "0.1.0", so a reader that stopped finding the field would have mislabeled
results rather than failed.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from skills._shared.merge import read_skill_version

REPO_ROOT = Path(__file__).resolve().parents[3]


def _skill_md(frontmatter: str, body: str = "# critique-toy\n") -> str:
    return f"---\nname: critique-toy\n{frontmatter}license: Apache-2.0\n---\n\n{body}"


def test_reads_metadata_version() -> None:
    assert read_skill_version(_skill_md("metadata:\n  version: 0.1.1\n")) == "0.1.1"


def test_reads_a_quoted_metadata_version() -> None:
    assert read_skill_version(_skill_md('metadata:\n  version: "0.2.0"\n')) == "0.2.0"


def test_reads_crlf_frontmatter() -> None:
    text = _skill_md("metadata:\n  version: 0.1.1\n").replace("\n", "\r\n")
    assert read_skill_version(text) == "0.1.1"


def test_top_level_version_raises_and_names_the_new_place() -> None:
    with pytest.raises(ValueError, match=r"top level.*metadata\.version"):
        read_skill_version(_skill_md("version: 0.1.1\n"))


def test_absent_version_raises() -> None:
    with pytest.raises(ValueError, match="no metadata.version"):
        read_skill_version(_skill_md(""))


def test_a_body_line_is_never_read_as_the_version() -> None:
    """The old merge.py reader searched the whole file, so a body line starting `version:` counted."""
    with pytest.raises(ValueError, match="no metadata.version"):
        read_skill_version(_skill_md("", body="version: 9.9.9\n"))


def test_a_deeper_key_under_metadata_is_not_the_version() -> None:
    with pytest.raises(ValueError, match="no metadata.version"):
        read_skill_version(_skill_md("metadata:\n  source:\n    version: 9.9.9\n"))


def test_missing_frontmatter_raises() -> None:
    with pytest.raises(ValueError, match="frontmatter"):
        read_skill_version("# no frontmatter\n")


def test_every_registered_skill_version_matches_library_json_and_checks_py() -> None:
    """The version is written in three places per skill: SKILL.md, library.json, and the
    `skill_version=` argument in scripts/checks.py, which stamps every scripted-lane envelope.
    The gate and gen-site compare the first two; before this test nothing compared the third."""
    library = json.loads((REPO_ROOT / "library.json").read_text(encoding="utf-8"))
    skills = library["components"]["skills"]
    assert skills, "library.json lists no skills"
    for entry in skills:
        skill_dir = REPO_ROOT / entry["path"]
        version = read_skill_version((skill_dir / "SKILL.md").read_text(encoding="utf-8"))
        assert version == entry["version"], entry["name"]
        stamped = re.findall(r'skill_version="([^"]+)"', (skill_dir / "scripts" / "checks.py").read_text(encoding="utf-8"))
        assert stamped == [version], f"{entry['name']}: checks.py stamps {stamped}, SKILL.md says {version}"

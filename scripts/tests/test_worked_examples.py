# what-it-is:   the guard on every worked example under examples/
# what-it-does: validates each committed envelope, disposition log and revision brief against the
#               contract, checks every recorded hash against the bytes on disk, and re-runs each
#               README's printed scripted-lane command to compare its output with what is printed
# why:          the examples are evidence a reader uses to decide whether to trust a skill, and
#               nothing checked them: by 2026-11-15 three READMEs printed output from an older
#               skill version, one disposition log named a different artifact from its envelope,
#               and every artifact hash was wrong on a Windows checkout (E83 phase 2)
# used-by:      python -m pytest (the CI unit-python job)
"""Tests that the worked examples under ``examples/`` are still true.

``test_example_artifact_hashes.py`` guards the golden fixtures under ``skills/``. The examples
copy those fixtures into ``examples/<domain>/`` and add an envelope, a disposition log and a
README that prints the scripted lane's real output, and none of that was checked. E83's plan
(best-in-class examples) found it had drifted in three ways, each of which a test below now
catches: a README printing output the command no longer produces, a disposition log bound to a
different artifact path from its envelope, and artifact copies whose bytes changed on checkout.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from contract.validate import validate_document  # noqa: E402

EXAMPLES = REPO_ROOT / "examples"
DOMAINS = sorted(p.parent for p in EXAMPLES.glob("*/envelope.json"))
ENVELOPES = sorted(EXAMPLES.glob("**/envelope.json"))
LOGS = sorted(EXAMPLES.glob("**/dispositions.json"))
BRIEFS = sorted(EXAMPLES.glob("**/revision-brief.json"))

# A README command line that runs a skill's scripted lane on its example artifact.
COMMAND_RE = re.compile(
    r"^python (skills/critique-[a-z]+/scripts/checks\.py) (examples/[a-z]+/artifact\.(?:md|html))$",
    re.M,
)
JSON_BLOCK_RE = re.compile(r"```json\n(.*?)\n```", re.S)


def _rel(p: Path) -> str:
    return p.relative_to(REPO_ROOT).as_posix()


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def test_examples_are_discoverable() -> None:
    """An empty glob would make every other test here pass vacuously."""
    assert len(DOMAINS) >= 7, f"expected seven skill example folders, found {len(DOMAINS)}"
    assert LOGS and BRIEFS


@pytest.mark.parametrize("path", ENVELOPES + LOGS + BRIEFS, ids=_rel)
def test_document_is_contract_valid(path: Path) -> None:
    doc = _load(path)
    referenced = None
    if "envelope" in doc and isinstance(doc["envelope"], dict) and doc["envelope"].get("path"):
        referenced = _load(REPO_ROOT / doc["envelope"]["path"])
    elif path.name != "envelope.json":
        sibling = path.with_name("envelope.json")
        referenced = _load(sibling) if sibling.exists() else None
    result = validate_document(doc, referenced_envelope=referenced)
    assert not result.errors, "\n".join(str(e) for e in result.errors)


@pytest.mark.parametrize("path", ENVELOPES, ids=_rel)
def test_envelope_artifact_hash_matches_disk(path: Path) -> None:
    run = _load(path)["run"]
    # A golden-fixture example names its artifact from the repository root. A live run, such as
    # the E54 recipe's, names it relative to the run's working directory: the envelope's folder.
    artifact = REPO_ROOT / run["artifact"]
    if not artifact.is_file():
        artifact = path.parent / run["artifact"]
    assert artifact.is_file(), f"run.artifact {run['artifact']} does not exist"
    assert _sha256(artifact) == run["artifact_sha256"], (
        f"{run['artifact']} hashes differently from the recorded artifact_sha256; if only this "
        "checkout differs, its line endings were rewritten (see .gitattributes)"
    )


@pytest.mark.parametrize("folder", DOMAINS, ids=lambda p: p.name)
def test_artifact_copy_matches_the_fixture_it_copies(folder: Path) -> None:
    """Each example folder's artifact is a byte-for-byte copy of the fixture its envelope names."""
    run = _load(folder / "envelope.json")["run"]
    copies = sorted(folder.glob("artifact.*"))
    assert len(copies) == 1, f"expected one artifact.* in {_rel(folder)}, found {len(copies)}"
    assert _sha256(copies[0]) == run["artifact_sha256"], (
        f"{_rel(copies[0])} is not a byte-for-byte copy of {run['artifact']}"
    )


@pytest.mark.parametrize("path", LOGS, ids=_rel)
def test_disposition_log_is_bound_to_its_envelope(path: Path) -> None:
    log = _load(path)["envelope"]
    env_path = REPO_ROOT / log["path"] if log.get("path") else path.with_name("envelope.json")
    run = _load(env_path)["run"]
    for key in ("skill", "skill_version", "artifact", "artifact_sha256", "timestamp"):
        assert log.get(key) == run.get(key), f"envelope.{key} is {log.get(key)!r}, the envelope says {run.get(key)!r}"
    if log.get("envelope_sha256"):
        assert _sha256(env_path) == log["envelope_sha256"], "envelope_sha256 no longer matches the envelope's bytes"


@pytest.mark.parametrize("folder", DOMAINS, ids=lambda p: p.name)
def test_disposition_notes_say_they_are_illustrations(folder: Path) -> None:
    """A worked example's dispositions were authored, not decided, and the log itself must say so."""
    for entry in _load(folder / "dispositions.json")["dispositions"]:
        assert entry["note"].startswith("Illustration:"), (
            f"{entry['finding_id']}'s note does not open with 'Illustration:'"
        )


def _printed_scripted_runs() -> list[tuple[Path, str, str, dict]]:
    """Every README that prints a scripted command followed by that command's JSON output."""
    out = []
    for readme in sorted(EXAMPLES.glob("*/README.md")):
        text = readme.read_text(encoding="utf-8")
        m = COMMAND_RE.search(text)
        if not m:
            continue
        for block in JSON_BLOCK_RE.findall(text[m.end():]):
            try:
                doc = json.loads(block)
            except json.JSONDecodeError:
                continue
            if isinstance(doc, dict) and doc.get("run", {}).get("model") == "none":
                out.append((readme, m.group(1), m.group(2), doc))
                break
    return out


def test_printed_runs_are_discoverable() -> None:
    assert len(_printed_scripted_runs()) >= 3


@pytest.mark.parametrize("readme,script,artifact,printed", _printed_scripted_runs(),
                         ids=lambda v: v.parent.name if isinstance(v, Path) else "")
def test_readme_prints_what_the_command_prints(readme: Path, script: str, artifact: str, printed: dict) -> None:
    proc = subprocess.run([sys.executable, script, artifact], cwd=REPO_ROOT, capture_output=True,
                          text=True, encoding="utf-8")
    assert proc.returncode in (0, 1, 2), proc.stderr
    live = json.loads(proc.stdout)
    for doc in (live, printed):
        doc["run"].pop("timestamp", None)
    assert printed == live, (
        f"{_rel(readme)} prints scripted output the command no longer produces; re-run "
        f"`python {script} {artifact}` and update the printed block"
    )

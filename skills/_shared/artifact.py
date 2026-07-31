"""Artifact loading: read a file once, hash the exact bytes read, and
compute the contract-valid relative POSIX path that gets recorded as
`run.artifact` (contract/critique-contract.schema.json, $defs/artifactPath).

A skill's checks.py is conventionally run with the current working
directory set to the repository root, matching the convention already
stated for the bench and contract CLIs ("every command is run from the
repository root", bench/generator/README.md). `repo_root` exists as an
explicit override for the cases where that convention is not followed.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


class ArtifactError(Exception):
    """Raised when an artifact cannot be read, or cannot be expressed as
    a contract-valid path relative to the repository root. Both are
    usage errors, never a defect in the artifact being critiqued."""


@dataclass(frozen=True, slots=True)
class Artifact:
    """A loaded artifact, ready to hand to a skill's check function.

    `path` is what gets written to `run.artifact`: a relative POSIX
    path, forward slashes only, regardless of the platform this ran on.
    `sha256` is computed over the raw bytes actually read, before any
    decoding, so it is the artifact's true identity per the contract's
    own description of `artifact_sha256`.
    """

    path: str
    text: str
    sha256: str
    disk_path: Path


def load_artifact(path: str, *, repo_root: str | Path | None = None) -> Artifact:
    """Read `path` from disk and return an Artifact.

    `path` may be relative (resolved against the current working
    directory, matching how a shell invokes `python .../checks.py
    <path>`) or absolute. `repo_root` is what `path` gets relativized
    against to produce the recorded `run.artifact` value; it defaults to
    the current working directory.

    Raises ArtifactError if the file cannot be read, is not valid UTF-8,
    or does not resolve to a location inside `repo_root` (the contract
    has no way to represent a path outside the tree).
    """
    root = Path(repo_root).resolve() if repo_root is not None else Path.cwd().resolve()
    disk_path = Path(path)
    disk_path = disk_path if disk_path.is_absolute() else (Path.cwd() / disk_path)
    disk_path = disk_path.resolve()

    try:
        raw = disk_path.read_bytes()
    except OSError as exc:
        raise ArtifactError(f"cannot read artifact '{path}': {exc}") from exc

    try:
        # utf-8-sig tolerates (and strips) a leading BOM on input while
        # decoding identically to plain utf-8 when none is present. The
        # sha256 below is still taken over `raw`, BOM included, because
        # that is what "the artifact bytes as critiqued" means.
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ArtifactError(f"artifact '{path}' is not valid UTF-8: {exc}") from exc

    try:
        relative = disk_path.relative_to(root)
    except ValueError as exc:
        raise ArtifactError(
            f"artifact '{disk_path}' is not inside repo root '{root}'; "
            "pass --repo-root to override which root paths are relativized against"
        ) from exc

    recorded_path = PurePosixPath(*relative.parts).as_posix()
    if not recorded_path or recorded_path in (".", ""):
        raise ArtifactError(f"artifact '{path}' resolves to an empty path relative to '{root}'")

    return Artifact(
        path=recorded_path,
        text=text,
        sha256=hashlib.sha256(raw).hexdigest(),
        disk_path=disk_path,
    )

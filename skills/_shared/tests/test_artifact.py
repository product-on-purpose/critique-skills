"""Tests for skills/_shared/artifact.py."""

from __future__ import annotations

import hashlib
import os

import pytest

from skills._shared.artifact import ArtifactError, load_artifact


def test_load_artifact_reads_text_and_hashes_raw_bytes(tmp_path):
    target = tmp_path / "sub" / "doc.md"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"Hello, artifact.\n")

    artifact = load_artifact(str(target), repo_root=tmp_path)

    assert artifact.text == "Hello, artifact.\n"
    assert artifact.sha256 == hashlib.sha256(b"Hello, artifact.\n").hexdigest()


def test_load_artifact_records_a_posix_relative_path(tmp_path):
    target = tmp_path / "sub" / "doc.md"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"content")

    artifact = load_artifact(str(target), repo_root=tmp_path)

    assert artifact.path == "sub/doc.md"
    assert "\\" not in artifact.path


def test_load_artifact_strips_a_bom_from_text_but_hashes_raw_bytes(tmp_path):
    target = tmp_path / "doc.md"
    raw = b"\xef\xbb\xbfHello.\n"
    target.write_bytes(raw)

    artifact = load_artifact(str(target), repo_root=tmp_path)

    assert artifact.text == "Hello.\n"
    assert artifact.sha256 == hashlib.sha256(raw).hexdigest()


def test_load_artifact_missing_file_raises_artifact_error(tmp_path):
    with pytest.raises(ArtifactError):
        load_artifact(str(tmp_path / "does-not-exist.md"), repo_root=tmp_path)


def test_load_artifact_invalid_utf8_raises_artifact_error(tmp_path):
    target = tmp_path / "bad.md"
    target.write_bytes(b"\xff\xfe\x00not utf-8")

    with pytest.raises(ArtifactError):
        load_artifact(str(target), repo_root=tmp_path)


def test_load_artifact_outside_repo_root_raises_artifact_error(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    target = outside / "doc.md"
    target.write_bytes(b"content")
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    with pytest.raises(ArtifactError):
        load_artifact(str(target), repo_root=repo_root)


def test_load_artifact_relative_path_resolves_against_cwd(tmp_path, monkeypatch):
    target = tmp_path / "doc.md"
    target.write_bytes(b"content")
    monkeypatch.chdir(tmp_path)

    artifact = load_artifact("doc.md", repo_root=tmp_path)

    assert artifact.path == "doc.md"
    assert os.path.isabs(str(artifact.disk_path))

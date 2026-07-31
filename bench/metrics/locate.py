"""Dispatch to the right resolver by `artifact_type`
(manifest.schema.json's closed set: `markdown-prose`, `markdown-tree`,
`html`, `string-list`).

Parsing an artifact's structure is separated from resolving a location
against it (`parse_artifact` then `resolve_location`) so a caller scoring
many claims against one artifact parses that artifact exactly once.
"""

from __future__ import annotations

from typing import Any

from bench.metrics import resolve_html, resolve_markdown, resolve_stringlist
from bench.metrics.markdown_blocks import Document, parse_markdown
from bench.metrics.resolve_html import HtmlDoc, parse_html
from bench.metrics.resolve_stringlist import StringListDoc, parse_string_list

ParsedArtifact = tuple[str, Document | HtmlDoc | StringListDoc]

_MARKDOWN_TYPES = ("markdown-prose", "markdown-tree")
_KNOWN_TYPES = _MARKDOWN_TYPES + ("html", "string-list")


def parse_artifact(artifact_type: str, artifact_text: str) -> ParsedArtifact:
    if artifact_type in _MARKDOWN_TYPES:
        return "markdown", parse_markdown(artifact_text)
    if artifact_type == "html":
        return "html", parse_html(artifact_text)
    if artifact_type == "string-list":
        return "string-list", parse_string_list(artifact_text)
    raise ValueError(f"unknown artifact_type {artifact_type!r}; expected one of {_KNOWN_TYPES}")


def resolve_location(
    parsed: ParsedArtifact, artifact_type: str, location_text: str, *, artifact_path: str | None = None
) -> Any:
    kind, doc = parsed
    if kind == "markdown":
        assert isinstance(doc, Document)
        return resolve_markdown.resolve(
            doc, location_text, tree=(artifact_type == "markdown-tree"), own_artifact_path=artifact_path
        )
    if kind == "html":
        assert isinstance(doc, HtmlDoc)
        return resolve_html.resolve(doc, location_text)
    if kind == "string-list":
        assert isinstance(doc, StringListDoc)
        return resolve_stringlist.resolve(doc, location_text)
    raise ValueError(f"unknown parsed artifact kind {kind!r}")


def is_hit(parsed: ParsedArtifact, artifact_type: str, resolved: Any, truth: dict) -> bool:
    kind, doc = parsed
    if kind == "markdown":
        assert isinstance(doc, Document)
        return resolve_markdown.is_hit(doc, resolved, truth, tree=(artifact_type == "markdown-tree"))
    if kind == "html":
        assert isinstance(doc, HtmlDoc)
        return resolve_html.is_hit(doc, resolved, truth)
    if kind == "string-list":
        return resolve_stringlist.is_hit(resolved, truth)
    raise ValueError(f"unknown parsed artifact kind {kind!r}")


def self_match(parsed: ParsedArtifact, artifact_type: str, a: Any, b: Any) -> bool:
    """Whether two findings' resolved locations name the same place
    (used for consistency, which has no manifest truth to compare
    against). `artifact_type` is accepted for a uniform signature but
    unused: the markdown resolver behaves identically for
    `markdown-prose` and `markdown-tree` here, because consistency
    compares two runs of the same skill on the same single artifact, so
    the page-anchor check both runs would apply identically cancels out.
    """
    kind, doc = parsed
    if kind == "markdown":
        return resolve_markdown.self_match(a, b)
    if kind == "html":
        assert isinstance(doc, HtmlDoc)
        return resolve_html.self_match(doc, a, b)
    if kind == "string-list":
        return resolve_stringlist.self_match(a, b)
    raise ValueError(f"unknown parsed artifact kind {kind!r}")


def canonical_key(resolved: Any) -> str:
    return resolved.canonical_key

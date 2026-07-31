"""Recall, precision, consistency, and the location resolvers.

Computes exactly what `bench/README.md`'s "Metrics" and "Location
tolerance" sections define, from a manifest plus one or more contract-valid
run envelopes for the artifact the manifest describes, and nothing else
(S-03: "The metrics module reads manifests and run envelopes and nothing
else; a claim that cannot be computed from those two is not a benchmark
claim.").

This package does not import `bench.generator`. The corpus generator and
the scorer are built and owned independently; the only thing they must
agree on is the artifact bytes and the manifest schema, both of which are
files, not code, so no import dependency is needed to keep them in sync.

Modules:

- `ordinals`: the frozen ordinal-word table (`first` through `twentieth`,
  plus `last`), copied from `bench/generator/text.py`.
- `text_util`: NFC/casefold/whitespace normalization shared by every
  resolver.
- `markdown_blocks`: the normative block parser for `markdown-prose` and
  `markdown-tree` (bench/README.md, "The block parser (normative)").
- `resolve_markdown`, `resolve_html`, `resolve_stringlist`: per-artifact-type
  location resolution and tolerance, one module per artifact type.
- `locate`: dispatches to the right resolver by `artifact_type`.
- `claims`: turns a run envelope's `findings[]` into the claim list
  recall, precision, and consistency are computed over.
- `match`: greedy assignment of claims to planted defects (recall,
  precision), and the symmetric greedy assignment consistency uses.
- `score`: the top-level metric computations and the `results.json`
  assembly, exposed as `python -m bench.metrics score ...`.
"""

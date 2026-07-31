"""Small text helpers shared by domain modules.

Pure functions only: no randomness, no locale, no wall clock. `split_sentences`
is deliberately naive, because domain modules only ever call it on prose their
own `compose` function generated from a known template (see
`bench/generator/README.md`, "Transforms operate on a grammar you own"), never
on arbitrary text.
"""

from __future__ import annotations

import re

# A frozen table, first through twentieth. Matches the ordinal vocabulary
# `bench/README.md`'s location-tolerance resolver parses on the scoring
# side; the generator uses it only to render a location's `text` field in
# the same words a correct finding would plausibly use.
ORDINALS: dict[int, str] = {
    1: "first",
    2: "second",
    3: "third",
    4: "fourth",
    5: "fifth",
    6: "sixth",
    7: "seventh",
    8: "eighth",
    9: "ninth",
    10: "tenth",
    11: "eleventh",
    12: "twelfth",
    13: "thirteenth",
    14: "fourteenth",
    15: "fifteenth",
    16: "sixteenth",
    17: "seventeenth",
    18: "eighteenth",
    19: "nineteenth",
    20: "twentieth",
}

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])[ \t]+")


def split_sentences(text: str) -> list[str]:
    """Split prose into sentences on a run of whitespace immediately after
    a sentence-ending mark. No abbreviation handling, no locale: this is
    intended for text a domain module's own `compose` generated from a
    template it owns, not for arbitrary prose."""
    stripped = text.strip()
    if not stripped:
        return []
    return [s for s in _SENTENCE_BOUNDARY.split(stripped) if s]

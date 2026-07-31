"""The frozen ordinal-word vocabulary used to parse a finding's free-text
location (bench/README.md, "`markdown-prose` and `markdown-tree`":
"`<ordinal>` is a frozen table: `first` through `twentieth`, plus `last`.
No locale, no inflection library.").

Copied field for field from `bench/generator/text.py`'s `ORDINALS` table so
this package has no import dependency on `bench.generator` (see
`bench/metrics/__init__.py`). Both copies must list the same twenty words
in the same order; keep them in sync by hand until a drift check exists,
mirroring the one `bench/generator/manifest.schema.json` runs against the
critique contract.

`"last"` is deliberately not in the table as a fixed integer: what it
resolves to depends on the size of whatever set is being addressed (the
last paragraph in a section, the last item in a list, the last element of
a kind), so `ordinal_to_int` resolves it against a caller-supplied total
rather than a table lookup.
"""

from __future__ import annotations

ORDINAL_WORDS: dict[int, str] = {
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

WORD_TO_ORDINAL: dict[str, int] = {word: n for n, word in ORDINAL_WORDS.items()}

LAST = "last"


def ordinal_to_int(word: str, *, total: int) -> int | None:
    """Resolve an ordinal word, including "last", against a known total
    count of the set being addressed. 1-based. Returns None when the word
    is not a recognized ordinal, when it names a position beyond `total`,
    or when `total` is 0 (there is nothing to be the last of).
    """
    if total <= 0:
        return None
    key = word.strip().lower()
    if key == LAST:
        return total
    n = WORD_TO_ORDINAL.get(key)
    if n is None or n > total:
        return None
    return n

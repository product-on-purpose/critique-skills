"""Text normalization shared by every location resolver.

Two normalizers, matching bench/README.md, "Location tolerance": heading
comparison normalizes "NFC, casefold, collapse internal whitespace to
single spaces, trim, then strip trailing characters in `.,:;!?`"; every
other free-text comparison (a finding's location text, a quoted content
match) uses the same steps without the trailing-punctuation strip.
"""

from __future__ import annotations

import re
import unicodedata

_WHITESPACE = re.compile(r"\s+")
_TRAILING_PUNCT = ".,:;!?"


def normalize_loose(text: str) -> str:
    """NFC, casefold, collapse whitespace, trim. Used for comparing free
    location text and quoted content against the artifact."""
    t = unicodedata.normalize("NFC", text)
    t = t.casefold()
    t = _WHITESPACE.sub(" ", t).strip()
    return t


def normalize_heading(text: str) -> str:
    """`normalize_loose` plus stripping trailing `.,:;!?`, for comparing
    heading titles (bench/README.md, "Heading comparison")."""
    return normalize_loose(text).rstrip(_TRAILING_PUNCT)

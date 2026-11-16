"""Write a JSON document to stdout as UTF-8, whatever the platform's default encoding.

Every shared CLI here prints JSON with ``ensure_ascii=False``, so a finding that quotes an arrow,
a mathematical symbol or most non-Latin text reaches stdout as that character. Python encodes
stdout with the locale code page when stdout is a pipe on Windows (cp1252 on most installs), and a
character outside that code page raised ``UnicodeEncodeError``: the skill got a traceback instead
of an envelope. Claude Code's Bash tool sets neither ``PYTHONUTF8`` nor ``PYTHONIOENCODING``, so
this was the normal state of a skill run on Windows. E84 (Windows output encoding) has the
evidence.

Writing UTF-8 is the fix. It changes no byte of any output on Linux or macOS, where stdout is
already UTF-8. On Windows it also changes how characters inside cp1252, such as curly quotes, are
encoded, from cp1252 bytes to UTF-8 bytes. That is the encoding every reader of these documents
expects.
"""

from __future__ import annotations

import json
import sys
from typing import Any


def write_json(document: Any, *, sort_keys: bool = False) -> None:
    """Print ``document`` as two-space-indented JSON plus a newline, encoded as UTF-8."""
    stream = sys.stdout
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is not None and (getattr(stream, "encoding", "") or "").lower().replace("-", "") != "utf8":
        try:
            reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            # A stream that cannot be reconfigured (already detached, or a test double) is left as
            # it is; the write below then behaves exactly as it did before this helper existed.
            pass
    stream.write(json.dumps(document, ensure_ascii=False, indent=2, sort_keys=sort_keys) + "\n")

"""critique-usability envelope assembly: pass 4 of the protocol.

A sibling of `checks.py`, deliberately. `checks.py` is invoked as `python3 scripts/checks.py` from
this skill's own directory and has resolved correctly in every shipped release. The assembler was
first placed at `skills/_shared/merge.py` and referenced by a repo-relative and then a
parent-relative path, and a live session on 2026-08-09 got it wrong three times in three different
ways: `critique-skills/_shared/merge.py`, a call with no arguments, and a call with nothing on
stdin. Each time it fell back to hand assembly and emitted a prose report instead of an envelope.

So the path problem is removed rather than explained: this file sits exactly where `checks.py`
sits, takes the same kind of arguments, and knows its own skill name from its own location, which
is one fewer thing for a caller to get right. All logic lives in `skills/_shared/merge.py`; this is
the entry point, not a second implementation.

Usage, from this skill's directory:
    python3 scripts/merge.py --artifact <path> --findings <path>
"""

import sys
from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "library.json").is_file():
            return candidate
    raise RuntimeError("could not locate the repository root (no library.json found above this file)")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve())
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from skills._shared import merge  # noqa: E402

# scripts/merge.py -> scripts -> <skill>
SKILL = Path(__file__).resolve().parent.parent.name


if __name__ == "__main__":
    argv = sys.argv[1:]
    if "--skill" not in argv:
        argv = ["--skill", SKILL, *argv]
    raise SystemExit(merge.main(argv))

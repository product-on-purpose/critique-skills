"""Gate exit-code semantics and contract validation, re-exported from
`contract/validate.py` rather than reimplemented.

This is the load-bearing file for S-04 AC-4: "`scripts/checks.py --gate`
implements S-02 exit-code semantics identically across skills (shared
library, not six copies)." Nothing in this module computes an exit code
or validates a document on its own; it names the one function each job
resolves to, so a skill's checks.py never has the option of drifting
from `contract/validate.py`'s definition.

`contract` is a sibling top-level package. A skill's checks.py is
conventionally invoked directly (`python skills/critique-clarity/scripts
/checks.py <artifact>`), not via `python -m`, so nothing puts the
repository root on `sys.path` automatically; see
docs/internal/skill-template.md, "Wiring scripts/checks.py", for the
bootstrap every checks.py runs before importing `skills._shared`. By the
time this module is imported, the repository root is already on
`sys.path`, and this module adds nothing further.
"""

from __future__ import annotations

from contract.validate import (  # noqa: F401  (re-exported, not used here)
    Issue,
    ValidationResult,
    gate_exit_code,
    load_document,
    validate_document,
)

__all__ = [
    "Issue",
    "ValidationResult",
    "gate_exit_code",
    "load_document",
    "validate_document",
]

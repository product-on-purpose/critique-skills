# what-it-is:   the package marker for scripts/
# what-it-does: nothing at runtime; makes scripts/ a package so pytest's rootdir
#               insertion walks past it to the repository root
# why:          the test modules under scripts/tests/ import contract.* and skills.*,
#               which resolve only when the repository root is on sys.path
# used-by:      pytest collection
"""Marker package. `scripts/skill-selftest.py` is a hyphenated CLI entry
point and is never imported as `scripts.skill_selftest` (Python module
names cannot contain a hyphen); its tests load it by file path via
`importlib.util`. This `__init__.py` exists only so pytest's rootdir
insertion walks past `scripts/` to the repository root the same way it
already does for `contract/`, `bench/`, and `skills/`.
"""

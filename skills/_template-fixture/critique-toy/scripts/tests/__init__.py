"""Package marker for the template fixture's scripted-lane tests.

what-it-is:   the test package marker for skills/_template-fixture/critique-toy
what-it-does: nothing at runtime; it exists so this directory is a
              package rather than a bare directory pytest adds to sys.path
why:          the template requires it of every skill's scripts/tests/,
              so the fixture models the required shape exactly
used-by:      pytest collection
"""

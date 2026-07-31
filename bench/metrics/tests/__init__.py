"""Tests for bench.metrics: recall, precision, consistency, and the
location resolvers. Covers S-03 AC-4's five named scenarios (perfect run,
empty run, duplicate findings, location-tolerance edge, clean-artifact
false positive) plus unit coverage for each resolver and the assignment
algorithms they sit on.
"""

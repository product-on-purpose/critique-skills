"""The bench generator: a deterministic seeded-defect corpus generator.

Home of the domain-plugin API (`api.py`), the seeded PRNG (`rng.py`), the
domain registry (`registry.py`), the shared markdown composition model
(`markdown.py`), the six-stage generation pipeline (`pipeline.py`), the
leak check (`leak.py`), the corpus writer (`build.py`), and the
regenerate-and-diff checker (`verify.py`). See `bench/generator/README.md`
for the frozen design this package implements.
"""

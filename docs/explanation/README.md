---
title: Explanation
description: Understanding-oriented discussion of why critique-skills is built the way it is
audience: both
level: intermediate
---

# Explanation

Understanding-oriented discussion: methodology rationale, severity-scale design, scope
trade-offs.

## Inventory

- [`architecture.md`](architecture.md) - The five moving parts and how one critique flows through
  them. Start here if you want the shape before the reasoning.
- [`architecture-detail.md`](architecture-detail.md) - Why the two-lane split, how the frozen
  contract couples the parts, how measurement is kept independent, and where the extension points
  are.
- [`the-benchmark-harness.md`](the-benchmark-harness.md) - What `bench/run_bench.py` is, why it
  exists, and why using this plugin never requires an API key. Read it if you saw an API key
  mentioned anywhere and wondered whether it applied to you. It does not.
- [`methodology.md`](methodology.md) - How this library decides what belongs in it, how its
  skills produce findings, and how those findings are measured.

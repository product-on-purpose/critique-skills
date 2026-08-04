---
title: agents
---

# agents

The clean-context critic subagent every `critique-<domain>` skill delegates to where a subagent
tool is available (methodology sec 7, "Clean-context critique"). One subagent, shared by all six
skills, rather than one per domain, so the clean-context guarantee is implemented once.

## Inventory

- `critique-critic.md` - runs a critique of a supplied artifact against a named
  `critique-<domain>` skill's rubric in a context that never saw the artifact being authored, and
  returns exactly one contract-valid run envelope. See
  [ADR 0004](../docs/internal/decisions/0004-plugin-surface-skills-and-critic-subagent.md).

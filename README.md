# critique-skills

Rubric-cited, machine-parseable critique skills: structured review of interfaces, documents, and
writing that reports measured, evidence-graded findings against a defect rubric, instead of
freeform opinion.

**Status: early scaffold.** This repo currently carries the plugin skeleton (manifests, checks,
docs tree) and no skills yet. The v0.1.0 release plan targets three core critique skills
(usability, accessibility, clarity) plus three gated stretch skills, each shipped with a published,
measured benchmark result rather than an unverified claim. Nothing here should be read as "this
works" until a skill exists and its results are published.

## Quickstart

Once skills ship, invoke one directly (e.g. `critique-usability`) or via the `critique-critic`
subagent. Until then, see `AGENTS.md` for how to validate the scaffold itself.

## Conformance

This plugin targets the Advanced Skill Library Standard (`tier: universal` to start). Validate it
with the conformance gate:

```
node scripts/check.mjs
```

See `AGENTS.md` for the full command reference. Tier climbs toward Silver (`convergent`) are a
roadmap item, not a v0.1.0 launch requirement.

## License

Apache-2.0 (repo). Bench corpus content, once published, is CC-BY-4.0. See `LICENSE`.

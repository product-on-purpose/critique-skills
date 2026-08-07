# INDEX - critique-skills

> Generated from `library.json` + component frontmatter by `gen-index` and
> drift-checked (G4). Edit the source, not this file. Overview and positioning are
> in [`README.md`](README.md); agent guidance is in [`AGENTS.md`](AGENTS.md).

**Tier:** Silver (convergent). Standard 0.12. Version 0.1.2. Self-validating: `node scripts/check.mjs`.

## Components

### Skills (6)

- [`critique-accessibility`](skills/critique-accessibility/) - Reviews HTML pages and fragments (markdown where mappable) against WCAG 2.2 AA: contrast, alt text, heading hierarchy for screen readers, link text, and keyboard and screen-reader access. Judges conformance against WCAG, not an interface's general usability, flow, or controls (critique-usability covers that). Use when the user asks for an accessibility review, feedback, a second opinion, a red-line pass, an a11y audit, or a pre-launch quality check on a page or component.
- [`critique-argument`](skills/critique-argument/) - Reviews argumentative prose - essays, proposals, position papers, recommendation memos, strategy docs, and op-eds - against the Toulmin model of argument: whether the claim, grounds, warrant, backing, qualifier, and rebuttal are present, explicit, and actually hold together. Judges the argument's structure, not prose readability or sentence mechanics (critique-clarity covers that). Use when the user asks for a review, feedback, a second opinion, a red-line pass, a quality check, or a critique of whether an argument holds up before it goes out.
- [`critique-clarity`](skills/critique-clarity/) - Reviews markdown or plain-text prose for clarity against the Federal Plain Language Guidelines and Williams' Style: readability, passive voice, sentence length, and nominalization density. Judges sentence- and passage-level readability, not whether an argument's claim is supported or its structure holds together (critique-argument covers that). Use when the user asks for feedback, a second opinion, a red-line pass, or a quality check on a memo, PRD, proposal, or any prose document before it goes out.
- [`critique-docs`](skills/critique-docs/) - Reviews technical documentation pages and page trees written in markdown against the Diataxis framework: tutorial, how-to, reference, and explanation mode fit, plus heading structure, orphaned pages, cross-mode linking, and navigation-list length. Use when the user asks for a review, feedback, a second opinion, a red-line pass, or a quality check on a docs site, a README tree, a knowledge base, or any markdown documentation before it ships.
- [`critique-microcopy`](skills/critique-microcopy/) - Reviews error messages, empty states, and other short microcopy strings, including screens annotated with placement, container, timing, and behavior context, against NN/g's error-message guidelines: plain language, specificity, constructive next steps, neutral tone, and recovery grace. Judges the message text itself, not the surrounding screen's flow, controls, or confirmation behavior (critique-usability covers that). Use when the user asks for a review, feedback, a second opinion, a red-line pass, or a quality check on error copy, empty-state copy, form validation messages, or other short UI text before it ships.
- [`critique-usability`](skills/critique-usability/) - Reviews HTML or markdown UI specs, wireframe write-ups, and page mockups against Nielsen's 10 usability heuristics: system status, user control and exits, consistency, error prevention and recovery, recognition over recall, and minimalist design. Judges the interface's flow, controls, and states, not the wording of error or empty-state message text (critique-microcopy covers that), and not conformance against accessibility standards such as contrast or screen-reader access (critique-accessibility covers that). Use when the user asks for a usability review, design feedback, a second opinion, a red-line pass, a heuristic evaluation, or a quality check on a screen, a flow, or an interface spec before it goes to build. Covers static specs and mockups, not live running applications.

### Subagents (1, Claude-only)

- [`critique-critic`](agents/critique-critic.md) - Runs a clean-context critique of a supplied artifact against a named critique-<domain> skill's rubric and returns exactly one contract-valid run envelope. Use when the user asks for an independent critique, an unbiased review, or a quality gate on a document, interface, or piece of writing, or when a critique-<domain> skill's own SKILL.md delegates its protocol here for clean-context execution.

### Commands (0)

- none

## Manifests

- [`library.json`](library.json) - authored canonical cross-agent manifest (the source of truth).
- [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) - Claude Code native manifest (generated; do not hand-edit).

## Documentation and governance

- [`README.md`](README.md) - overview, positioning, quickstart.
- [`CHANGELOG.md`](CHANGELOG.md) - full technical history; [`RELEASE-NOTES.md`](RELEASE-NOTES.md) - curated, user-facing notes.
- [`docs/`](docs/) - Diataxis docs (reference, how-to, explanation).
- [`docs/internal/decisions/`](docs/internal/decisions/) - ADRs.
- [`scripts/`](scripts/) - the Node validation spine (conformance checks, generators, gate, evaluate).

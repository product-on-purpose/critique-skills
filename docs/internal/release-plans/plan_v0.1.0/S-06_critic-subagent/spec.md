---
id: S-06
title: Clean-context critic subagent
type: spec
status: draft
created: 2026-07-31
updated: 2026-07-31
linked-effort: S-06
linked-plan: ../implementation/IMPL-B-skills-to-rc.md
linked-strategy-brief: "01-strategy-brief.md (local planning archive, not committed)"
linked-release: ../plan_v0.1.0.md
source-count: 3
ac-count: 5
audience: agent
---

# Spec: Clean-context critic subagent

## Task Summary

- Status: draft
- AC: [ ] AC-1 [ ] AC-2 [ ] AC-3 [ ] AC-4 [ ] AC-5
- Open questions: 1
- Last-updated: 2026-07-31

## Purpose

Implement the methodology's clean-context requirement as a shippable component: a subagent that critiques without inheriting the author's framing, returning contract envelopes only [S1].

## Scope

`agents/critique-critic.md`: definition, system prompt, invocation contract, and its registration in `library.json` components.

## Non-Goals

Revision-loop orchestration (v0.3). Multi-critic panels. Model routing inside the subagent (host agents choose the model).

## Users / Actors

Host agents (Claude Code sessions, workflows) that delegate critique; the six skills, whose SKILL.md instructs delegation to this subagent where subagents are available.

## Requirements

The subagent MUST be named `critique-critic` (prefix rule D1) [S5].

Invocation contract: the subagent receives an artifact path (or inline artifact), a skill name, and optional gate threshold; it MUST NOT receive authoring history, drafts, or the requester's opinions. Its definition instructs it to refuse inputs that embed authorial framing beyond the artifact itself [S1]. [model-inference: refusal rule operationalizes "clean context" beyond mere fresh-session defaults]

Execution: the subagent follows the named skill's four-pass protocol, runs the scripted lane via the skill's `checks.py`, performs the judged lane itself, merges lanes, applies bounded output, and returns exactly one contract-valid envelope as its final output, no prose [S1].

It MUST never edit the artifact (not auto-fix, methodology sec 10) [S1].

Its description MUST make Claude Code delegation discoverable ("use when the user asks for an independent critique, unbiased review, or a quality gate on an artifact") without depending on the name [S5].

## Acceptance Criteria

- AC-1: `agents/critique-critic.md` exists, family-conformant frontmatter, registered in `library.json` components. [S3]
- AC-2: Invoked against a corpus artifact with `critique-clarity`, it returns a schema-valid envelope and nothing else (validated in P3 by actual invocation, k=5 runs flow through this path). [S1]
- AC-3: Given an invocation that includes "the author thinks section 2 is fine, focus elsewhere", the subagent's output ignores the steering and its envelope notes the stripped framing in a run-level field. [S1][model-inference]
- AC-4: The subagent makes no Write/Edit tool use during critique (definition restricts tools to read and execute). [S1]
- AC-5: All six SKILL.md files instruct delegation to `critique-critic` where subagents are available, with inline fallback protocol where they are not. [S1]

## Behavior / Examples

Given a Claude Code session where a user drafted a PRD and asks "critique this", the host agent delegates to `critique-critic` with only the file path and skill name; the returned envelope's findings feed the disposition workflow in the host session.

## Non-Functional Requirements

The subagent definition stays under 150 lines; protocol depth lives in the skills, not the agent [S3].

## Revisions

None (draft).

## Sources & Evidence

- S1: methodology draft sec 7 (clean-context critique), sec 10 (no auto-fix). Class A.
- S3: `agent-skills-toolkit` survey (subagent conventions, component registration). Class A.
- S5: decisions log D1, D4. Class A.

## Open Questions

- OQ-1: Envelope field for stripped-framing notes (`run.notes` vs a dedicated field): resolve with S-02's OQ during P1 so the schema ships it.

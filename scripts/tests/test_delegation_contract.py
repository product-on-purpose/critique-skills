# what-it-is:   the contract between a critique skill and the critic subagent it delegates to
# what-it-does: asserts every command the subagent is told to run is built from the skill directory
#               it is passed, and that the skill passes it
# why:          the subagent starts in the caller's working directory, so a repo-relative command is
#               unrunnable there; twice now that has shipped, and prose is the only place it lives
# used-by:      python -m pytest (the CI unit-python job)
"""Tests for the delegation contract in agents/critique-critic.md and every SKILL.md.

There is no code to test here. The contract is prose, read by a model at run time, and the last two
times it broke it broke in prose: v0.1.5 moved the envelope assembler beside `scripts/checks.py`
"because that path resolves" and rewrote six `SKILL.md` files, while `agents/critique-critic.md`
kept telling the subagent to run `skills/_shared/merge.py`, the path those four live runs had just
proven unreachable. Separately, its Tools section told the subagent to run
`skills/<skill>/scripts/checks.py`, which resolves only from the repository root.

Measured 2026-08-16, the consequence was not a clear failure. A delegated run went looking for the
plugin, escalated to `find /e -maxdepth 3` and `find /c -maxdepth 4`, and never returned, so every
benchmark cell on that tier timed out at 900 seconds having produced nothing.

These assertions target the **hot path**: the fenced commands a run actually copies, not the prose
beside them. That distinction is the v0.1.5 lesson, where a fix that edited the commentary next to a
step and not the step itself shipped inert.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CRITIC = REPO_ROOT / "agents" / "critique-critic.md"

SKILL_FILES = sorted(REPO_ROOT.glob("skills/critique-*/SKILL.md"))

# Path shapes that only resolve when the working directory happens to be the repository root.
REPO_RELATIVE_COMMANDS = (
    "skills/_shared/merge.py",
    "skills/<skill>/scripts/",
    "skills/<skill-name>/scripts/",
    "-m contract.validate",
)


def fenced_blocks(text: str) -> list[str]:
    """Every fenced code block, which is what a run copies and runs."""
    return re.findall(r"```[a-z]*\n(.*?)```", text, re.DOTALL)


def test_there_are_six_skills_to_check() -> None:
    """Guards the glob: a test that silently checked nothing would pass forever."""
    assert len(SKILL_FILES) == 6, [p.parent.name for p in SKILL_FILES]


# ---------------------------------------------------------------------------
# The subagent's own instructions
# ---------------------------------------------------------------------------


def test_the_critic_is_passed_the_skill_directory() -> None:
    text = CRITIC.read_text(encoding="utf-8")
    assert "`skill_dir`" in text
    assert "absolute path" in text


@pytest.mark.parametrize("forbidden", REPO_RELATIVE_COMMANDS)
def test_no_command_the_critic_runs_is_repo_relative(forbidden: str) -> None:
    """The prose may name these to warn against them. A fenced command may not contain them."""
    blocks = fenced_blocks(CRITIC.read_text(encoding="utf-8"))
    offenders = [b for b in blocks if forbidden in b]
    assert offenders == [], f"a runnable block in critique-critic.md contains {forbidden!r}: {offenders}"


def test_the_critics_commands_are_built_from_the_skill_directory() -> None:
    blocks = fenced_blocks(CRITIC.read_text(encoding="utf-8"))
    runnable = [b for b in blocks if "checks.py" in b or "merge.py" in b]
    assert runnable, "critique-critic.md names no scripted-lane or assembler command at all"
    for block in runnable:
        for line in block.splitlines():
            if "checks.py" in line or "merge.py" in line:
                assert "<skill_dir>/" in line, f"command not rooted at the skill directory: {line!r}"


def test_the_critic_is_told_not_to_search_for_its_skill() -> None:
    """The observed failure mode was a filesystem hunt, so refusing is stated, not implied."""
    text = CRITIC.read_text(encoding="utf-8")
    assert "Never go looking for it" in text


# ---------------------------------------------------------------------------
# What each skill hands over
# ---------------------------------------------------------------------------


def delegation_section(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    start = text.index("## Delegation")
    end = text.find("\n## ", start + 1)
    return text[start:] if end == -1 else text[start:end]


@pytest.mark.parametrize("skill_md", SKILL_FILES, ids=lambda p: p.parent.name)
def test_each_skill_passes_the_critic_its_own_directory(skill_md: Path) -> None:
    section = delegation_section(skill_md)
    assert "absolute path" in section, f"{skill_md.parent.name} does not pass a path"
    assert "this skill's own directory" in section


@pytest.mark.parametrize("skill_md", SKILL_FILES, ids=lambda p: p.parent.name)
def test_each_skill_says_the_directory_is_required(skill_md: Path) -> None:
    """A caller that treats it as optional reproduces the failure, so "optional" is ruled out in
    the same place the instruction lives."""
    section = delegation_section(skill_md)
    assert "not optional" in section

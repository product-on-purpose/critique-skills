"""CLI: `python -m bench.generator <command> ...`.

Commands, frozen in `bench/generator/README.md`, "Commands":

    validate     Domain.validate() for every registered domain, no output written
    build        generate the full corpus and its manifests
    verify       regenerate to a temporary tree and compare every sha256
    diff         show the clean composition against the seeded one, for review
    leak-check   run the leak rules over an existing corpus

Every path is repository-relative and every command is run from the
repository root.
"""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

from bench.generator.api import Domain, DomainValidationError, Recipe
from bench.generator.build import build as build_corpus
from bench.generator.leak import leak_check_corpus
from bench.generator.pipeline import GenerationError, generate
from bench.generator.registry import load_domains
from bench.generator.verify import verify_corpus


def _select_domains(domains: tuple[Domain, ...], name: str | None) -> tuple[Domain, ...] | None:
    if name is None:
        return domains
    selected = tuple(d for d in domains if d.name == name)
    return selected or None


def _cmd_validate(args: argparse.Namespace) -> int:
    domains = _select_domains(load_domains(), args.domain)
    if domains is None:
        print(f"no such domain: {args.domain!r}", file=sys.stderr)
        return 4
    problems: list[str] = []
    for domain in domains:
        try:
            domain.validate()
        except DomainValidationError as exc:
            problems.append(str(exc))
    if problems:
        for p in problems:
            print(p, file=sys.stderr)
        return 1
    print(f"valid: {len(domains)} domain(s)")
    return 0


def _cmd_build(args: argparse.Namespace) -> int:
    domains = _select_domains(load_domains(), args.domain)
    if domains is None:
        print(f"no such domain: {args.domain!r}", file=sys.stderr)
        return 4
    for domain in domains:
        try:
            domain.validate()
        except DomainValidationError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    try:
        result = build_corpus(Path(args.out), domains)
    except GenerationError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"built {len(result.generated)} artifact(s) under {args.out}")
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    result = verify_corpus(Path(args.corpus))
    print(result.report())
    return 0 if result.ok else 1


def _cmd_leak_check(args: argparse.Namespace) -> int:
    problems = leak_check_corpus(Path(args.corpus))
    if problems:
        for p in problems:
            print(p, file=sys.stderr)
        return 1
    print("leak check OK")
    return 0


def _cmd_diff(args: argparse.Namespace) -> int:
    domains = load_domains()
    owner: Domain | None = None
    recipe: Recipe | None = None
    for domain in domains:
        for r in domain.recipes:
            if r.id == args.recipe_id:
                owner, recipe = domain, r
                break
        if owner is not None:
            break
    if owner is None or recipe is None:
        print(f"no such recipe: {args.recipe_id!r}", file=sys.stderr)
        return 4

    seeded = generate(owner, recipe)
    clean_recipe = Recipe(id=recipe.id, shape=recipe.shape, plants=())
    clean = generate(owner, clean_recipe)

    diff = difflib.unified_diff(
        clean.artifact_bytes.decode("utf-8").splitlines(keepends=True),
        seeded.artifact_bytes.decode("utf-8").splitlines(keepends=True),
        fromfile=f"{recipe.id} (clean composition)",
        tofile=f"{recipe.id} (seeded)",
    )
    sys.stdout.writelines(diff)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m bench.generator",
        description="The bench generator: a deterministic seeded-defect corpus generator.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="Domain.validate() for every registered domain.")
    p_validate.add_argument("--domain", default=None, help="Validate only this domain.")
    p_validate.set_defaults(func=_cmd_validate)

    p_build = sub.add_parser("build", help="Generate the full corpus and its manifests.")
    p_build.add_argument("--out", required=True, help="Corpus output directory, e.g. bench/corpus")
    p_build.add_argument("--domain", default=None, help="Build only this domain.")
    p_build.set_defaults(func=_cmd_build)

    p_verify = sub.add_parser("verify", help="Regenerate and compare every sha256.")
    p_verify.add_argument("--corpus", required=True, help="Committed corpus directory to check.")
    p_verify.set_defaults(func=_cmd_verify)

    p_diff = sub.add_parser("diff", help="Show the clean composition against the seeded one.")
    p_diff.add_argument("recipe_id", help="Recipe id, e.g. toy-001")
    p_diff.set_defaults(func=_cmd_diff)

    p_leak = sub.add_parser("leak-check", help="Run the leak rules over an existing corpus.")
    p_leak.add_argument("--corpus", required=True, help="Corpus directory to check.")
    p_leak.set_defaults(func=_cmd_leak_check)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

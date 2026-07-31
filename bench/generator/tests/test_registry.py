"""Tests for bench.generator.registry: domain discovery."""

from __future__ import annotations

import pytest

from bench.generator.api import Domain
from bench.generator.registry import DOMAIN_MODULES, load_domains


def test_domain_modules_is_an_explicit_tuple():
    assert isinstance(DOMAIN_MODULES, tuple)
    assert DOMAIN_MODULES == (
        "bench.generator.domains.toy",
        "bench.generator.domains.argument",
        "bench.generator.domains.docs",
        "bench.generator.domains.microcopy",
    )


def test_load_domains_returns_domain_instances():
    domains = load_domains()
    assert len(domains) == 4
    assert all(isinstance(d, Domain) for d in domains)
    assert [d.name for d in domains] == [
        "toy", "argument", "docs", "microcopy",
    ]


def test_load_domains_rejects_a_module_missing_domain(tmp_path, monkeypatch):
    import sys
    import types

    fake_module = types.ModuleType("bench_generator_test_fake_domain_no_domain")
    monkeypatch.setitem(sys.modules, fake_module.__name__, fake_module)
    with pytest.raises(TypeError, match="DOMAIN"):
        load_domains((fake_module.__name__,))


def test_load_domains_rejects_duplicate_domain_names(monkeypatch):
    import sys
    import types

    from bench.generator.api import Domain as DomainType

    def make_fake(module_name: str) -> None:
        module = types.ModuleType(module_name)
        module.DOMAIN = DomainType(
            name="duplicate",
            artifact_type="markdown-prose",
            extension=".md",
            namespaces=("DUP",),
            compose=lambda rng, shape: None,
            render=lambda composed: "",
            address=lambda composed, slot, sentence=None: None,
            injectors={},
            recipes=(),
        )
        monkeypatch.setitem(sys.modules, module_name, module)

    make_fake("bench_generator_test_fake_domain_a")
    make_fake("bench_generator_test_fake_domain_b")

    with pytest.raises(ValueError, match="registered twice"):
        load_domains(
            ("bench_generator_test_fake_domain_a", "bench_generator_test_fake_domain_b")
        )

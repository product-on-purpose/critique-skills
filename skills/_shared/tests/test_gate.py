"""Tests for skills/_shared/gate.py: confirms the module re-exports
contract.validate's own objects rather than shadowing or wrapping them.
"""

from __future__ import annotations

import contract.validate as contract_validate

from skills._shared import gate


def test_gate_exit_code_is_the_same_function_object_as_contract_validate():
    assert gate.gate_exit_code is contract_validate.gate_exit_code


def test_validate_document_is_the_same_function_object_as_contract_validate():
    assert gate.validate_document is contract_validate.validate_document


def test_gate_exit_code_zero_for_a_clean_summary():
    summary = {"by_severity": {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0}, "severity_3_threshold": 0}

    assert gate.gate_exit_code(summary) == 0


def test_gate_exit_code_one_for_any_severity_4():
    summary = {"by_severity": {"0": 0, "1": 0, "2": 0, "3": 0, "4": 1}, "severity_3_threshold": 0}

    assert gate.gate_exit_code(summary) == 1


def test_gate_exit_code_two_for_severity_3_above_threshold():
    summary = {"by_severity": {"0": 0, "1": 0, "2": 0, "3": 1, "4": 0}, "severity_3_threshold": 0}

    assert gate.gate_exit_code(summary) == 2

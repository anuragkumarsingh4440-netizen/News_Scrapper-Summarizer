"""Tests for the LLM-callable tools."""

from src.tools.calculator import calculator
from src.tools.web_search import web_search


def test_calculator_basic():
    result = calculator("2 + 2")
    assert result["success"] is True
    assert result["result"] == 4


def test_calculator_order_of_operations():
    assert calculator("10 * 5 + 3")["result"] == 53


def test_calculator_rejects_code_injection():
    # Should not execute arbitrary code; returns an error instead.
    result = calculator("__import__('os').system('echo hi')")
    assert result["success"] is False


def test_calculator_handles_garbage():
    assert calculator("not math")["success"] is False


def test_web_search_returns_results():
    result = web_search("AI news", num_results=3)
    assert result["success"] is True
    assert len(result["results"]) == 3

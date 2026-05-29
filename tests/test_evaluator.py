"""Tests for the evaluation metric calculations."""

from src.evaluation.evaluator import FilterEvaluator


def _result(expected: bool, predicted: bool) -> dict:
    return {
        "expected": expected,
        "predicted": predicted,
        "correct": expected == predicted,
    }


def test_perfect_classifier():
    results = [_result(True, True), _result(False, False)]
    m = FilterEvaluator._calculate_metrics(results)
    assert m["accuracy"] == 1.0
    assert m["precision"] == 1.0
    assert m["recall"] == 1.0
    assert m["f1_score"] == 1.0


def test_metrics_with_errors():
    # 2 TP, 1 FP, 1 FN
    results = [
        _result(True, True),
        _result(True, True),
        _result(False, True),  # FP
        _result(True, False),  # FN
    ]
    m = FilterEvaluator._calculate_metrics(results)
    assert m["precision"] == 2 / 3
    assert m["recall"] == 2 / 3
    assert round(m["f1_score"], 3) == round(2 / 3, 3)


def test_empty_results_do_not_divide_by_zero():
    m = FilterEvaluator._calculate_metrics([])
    assert m["accuracy"] == 0.0
    assert m["f1_score"] == 0.0

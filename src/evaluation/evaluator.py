"""Evaluate the NewsFilterAgent against a hand-labeled golden dataset.

Computes accuracy, precision, recall, and F1 for the binary
relevant / not-relevant decision and writes a markdown report.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from src.agents.news_filter_agent import NewsFilterAgent


class FilterEvaluator:
    """Runs the filter agent over golden cases and scores its predictions."""

    def __init__(self, golden_dataset_path: str) -> None:
        self.golden_dataset_path = Path(golden_dataset_path)
        self.agent = NewsFilterAgent()
        self.relevance_threshold = NewsFilterAgent.RELEVANCE_THRESHOLD

    async def evaluate(self) -> dict[str, Any]:
        dataset = json.loads(self.golden_dataset_path.read_text(encoding="utf-8"))
        test_cases = dataset["test_cases"]
        print(f"📊 Evaluating on {len(test_cases)} test cases...")

        results: list[dict] = []
        for case in test_cases:
            print(f"   [{case['id']}/{len(test_cases)}] {case['title'][:50]}...")
            judgment = self.agent._judge_relevance(
                {"title": case["title"], "summary": case["summary"]}
            )
            predicted = (
                judgment["relevant"]
                and judgment["relevance_score"] >= self.relevance_threshold
            )
            expected = case["expected_relevant"]
            correct = predicted == expected
            results.append(
                {
                    "test_case_id": case["id"],
                    "title": case["title"],
                    "expected": expected,
                    "predicted": predicted,
                    "correct": correct,
                    "score": judgment["relevance_score"],
                    "reasoning": judgment["reasoning"],
                }
            )
            print(
                f"      {'✅' if correct else '❌'} expected={expected} predicted={predicted}"
            )

        return {
            "results": results,
            "metrics": self._calculate_metrics(results),
            "test_cases": len(test_cases),
        }

    @staticmethod
    def _calculate_metrics(results: list[dict]) -> dict[str, float | int]:
        total = len(results)
        correct = sum(1 for r in results if r["correct"])
        tp = sum(1 for r in results if r["expected"] and r["predicted"])
        fp = sum(1 for r in results if not r["expected"] and r["predicted"])
        fn = sum(1 for r in results if r["expected"] and not r["predicted"])

        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (
            2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        )
        return {
            "accuracy": correct / total if total else 0.0,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "correct": correct,
            "total": total,
        }

    async def save_report(self, evaluation: dict[str, Any], output_path: str) -> None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        metrics = evaluation["metrics"]
        with open(out, "w", encoding="utf-8") as f:
            f.write("# News Filter Agent - Evaluation Report\n\n")
            f.write("## Overall Metrics\n\n")
            f.write(f"- **Accuracy:** {metrics['accuracy']:.1%}\n")
            f.write(f"- **Precision:** {metrics['precision']:.1%}\n")
            f.write(f"- **Recall:** {metrics['recall']:.1%}\n")
            f.write(f"- **F1 Score:** {metrics['f1_score']:.3f}\n")
            f.write(
                f"- **Test Cases:** {metrics['correct']}/{metrics['total']} correct\n\n"
            )
            f.write("## Test Results\n\n")
            for r in evaluation["results"]:
                status = "✅ PASS" if r["correct"] else "❌ FAIL"
                f.write(f"### [{r['test_case_id']}] {status}\n\n")
                f.write(f"**Title:** {r['title']}\n\n")
                f.write(
                    f"- Expected: {'Relevant' if r['expected'] else 'Not Relevant'}\n"
                )
                f.write(
                    f"- Predicted: {'Relevant' if r['predicted'] else 'Not Relevant'} "
                    f"(score: {r['score']})\n"
                )
                f.write(f"- Reasoning: {r['reasoning']}\n\n")
                f.write("---\n\n")
        print(f"💾 Evaluation report saved to {out}")


async def run_evaluation() -> None:
    print("=" * 60)
    print("  News Filter Agent Evaluation")
    print("=" * 60)
    evaluator = FilterEvaluator("data/evaluation/golden_dataset.json")
    evaluation = await evaluator.evaluate()
    m = evaluation["metrics"]
    print("\n📊 Results:")
    print(f"   Accuracy:  {m['accuracy']:.1%}")
    print(f"   Precision: {m['precision']:.1%}")
    print(f"   Recall:    {m['recall']:.1%}")
    print(f"   F1 Score:  {m['f1_score']:.3f}")
    await evaluator.save_report(evaluation, "data/evaluation/evaluation_report.md")
    print("\n✅ Evaluation complete!")


if __name__ == "__main__":
    asyncio.run(run_evaluation())

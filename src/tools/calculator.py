"""Calculator tool for LLM function calling."""

from __future__ import annotations

import ast
import operator
from typing import Any

# Safe arithmetic evaluator — supports + - * / // % ** and unary minus only.
_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval(node.operand))
    raise ValueError("Unsupported expression")


def calculator(expression: str) -> dict[str, Any]:
    """Safely evaluate a mathematical expression.

    Uses an AST walker instead of ``eval`` so only arithmetic is permitted.
    """
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval(tree.body)
        return {"success": True, "result": result, "expression": expression}
    except Exception as exc:
        return {"success": False, "error": str(exc), "expression": expression}


# OpenAI / LiteLLM tool schema.
CALCULATOR_SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Evaluate mathematical expressions. Use for arithmetic calculations.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Math expression to evaluate (e.g. '2 + 2', '10 * 5')",
                }
            },
            "required": ["expression"],
        },
    },
}


if __name__ == "__main__":
    print(calculator("2 + 2"))
    print(calculator("10 * 5 + 3"))
    print(calculator("invalid"))

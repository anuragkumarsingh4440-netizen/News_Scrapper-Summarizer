"""Base class for all AI agents.

Implements the Template Method pattern: :meth:`execute` fixes the
load → process → save lifecycle, while subclasses implement each step. Also
provides LLM helpers (plain completion and a tool-calling loop) shared by every
agent.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from litellm import completion


class BaseAgent(ABC):
    """Common lifecycle and LLM plumbing for agents."""

    def __init__(
        self,
        model: str | None = None,
        tools: list[dict] | None = None,
    ) -> None:
        self.model = model or os.getenv("LITELLM_MODEL")
        if not self.model:
            raise ValueError(
                "No model configured. Set LITELLM_MODEL in .env "
                "or pass `model=` to the agent constructor."
            )
        self.tools = tools or []
        self.tool_functions: dict[str, Callable] = {}

    # ---- Template Method lifecycle -------------------------------------

    async def execute(self, input_path: str, output_path: str) -> dict[str, Any]:
        """Run the agent: load context, process it, save the result."""
        print(f"\n🤖 {self.__class__.__name__} starting...")
        context = await self._load_context(input_path)
        result = await self._process(context)
        await self._save_result(result, output_path)
        print(f"✅ {self.__class__.__name__} complete")
        return {
            "input_path": input_path,
            "output_path": output_path,
            "success": True,
        }

    @abstractmethod
    async def _load_context(self, input_path: str) -> dict[str, Any]:
        """Read and parse this agent's input."""
        raise NotImplementedError

    @abstractmethod
    async def _process(self, context: dict[str, Any]) -> dict[str, Any]:
        """Do the agent-specific work."""
        raise NotImplementedError

    @abstractmethod
    async def _save_result(self, result: dict[str, Any], output_path: str) -> None:
        """Persist the agent's output."""
        raise NotImplementedError

    # ---- LLM helpers ----------------------------------------------------

    def register_tool_function(self, name: str, function: Callable) -> None:
        """Bind a Python function to a tool schema name."""
        self.tool_functions[name] = function

    def _call_llm(self, prompt: str, system: str | None = None) -> str:
        """Call the configured LLM and return its text response."""
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = completion(model=self.model, messages=messages)
            return response.choices[0].message.content
        except Exception as exc:
            print(f"❌ LLM call failed: {exc}")
            raise

    def _call_llm_with_tools(self, prompt: str, system: str | None = None) -> str:
        """Call the LLM, executing tool calls in a loop until it returns text.

        Protocol: send prompt + tool schemas; if the model emits ``tool_calls``,
        run each locally, append the assistant turn and each tool result, then
        call again — up to 10 rounds.
        """
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        for _ in range(10):
            response = completion(
                model=self.model,
                messages=messages,
                tools=self.tools or None,
            )
            msg = response.choices[0].message

            if not getattr(msg, "tool_calls", None):
                return msg.content

            messages.append(msg.model_dump())

            for tool_call in msg.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments or "{}")
                print(f"   🔧 Tool call: {name}({args})")

                if name not in self.tool_functions:
                    raise ValueError(f"Tool {name!r} not registered")

                result = self.tool_functions[name](**args)
                print(f"   📊 Tool result: {result}")

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": name,
                        "content": json.dumps(result),
                    }
                )

        raise RuntimeError("Tool-call loop exceeded 10 rounds — model is stuck.")

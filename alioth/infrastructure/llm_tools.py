from __future__ import annotations

# pyright: reportMissingImports=false

from collections.abc import Callable, Iterator
from typing import TypeVar

from astrbot.api.star import Context
from astrbot.core.agent.tool import FunctionTool


ToolT = TypeVar("ToolT", bound=type[object])


class LLMToolRegistry:
    def __init__(self) -> None:
        self._tool_classes: list[type[object]] = []

    def register(self, tool_class: type[object]) -> type[object]:
        if tool_class not in self._tool_classes:
            self._tool_classes.append(tool_class)
        return tool_class

    def build_all(self) -> list[FunctionTool]:
        tools: list[FunctionTool] = []
        for tool_class in self._tool_classes:
            tool = tool_class()
            if not isinstance(tool, FunctionTool):
                raise TypeError(
                    f"Registered LLM tool '{tool_class.__name__}' is not a FunctionTool."
                )
            tools.append(tool)
        return tools

    def clear(self) -> None:
        self._tool_classes.clear()

    def __iter__(self) -> Iterator[type[object]]:
        return iter(self._tool_classes)


_llm_tool_registry = LLMToolRegistry()


def llm_tool() -> Callable[[ToolT], ToolT]:
    def decorator(tool_class: ToolT) -> ToolT:
        _llm_tool_registry.register(tool_class)
        return tool_class

    return decorator


def get_llm_tool_registry() -> LLMToolRegistry:
    return _llm_tool_registry


def register_all_llm_tools(context: Context) -> None:
    tools = _llm_tool_registry.build_all()
    if tools:
        context.add_llm_tools(*tools)

from __future__ import annotations

from app.core.errors import NotFoundError
from app.providers.llm.base import ToolSpec
from app.tools.base import Tool


class ToolRegistry:
    """Process-wide registry of available tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> Tool:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered.")
        self._tools[tool.name] = tool
        return tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise NotFoundError(f"Unknown tool '{name}'.")
        return self._tools[name]

    def all(self) -> list[Tool]:
        return list(self._tools.values())

    def visible_to(self, allowed: set[str] | None) -> list[Tool]:
        """Tools an agent may use (None = all)."""
        if allowed is None:
            return self.all()
        return [t for t in self._tools.values() if t.name in allowed]

    def specs_for(self, allowed: set[str] | None) -> list[ToolSpec]:
        return [
            ToolSpec(name=t.name, description=t.description, parameters=t.parameters)
            for t in self.visible_to(allowed)
        ]


registry = ToolRegistry()

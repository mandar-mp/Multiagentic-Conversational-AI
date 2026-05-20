"""Tool registry used by the generic tool execution agent."""

from typing import Dict, Iterable, Optional
import logging

from src.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Small in-memory registry for executable tools."""

    def __init__(self, tools: Optional[Iterable[BaseTool]] = None):
        self._tools: Dict[str, BaseTool] = {}
        for tool in tools or []:
            self.register(tool)

    def register(self, tool: BaseTool) -> None:
        """Register or replace a tool by name."""
        self._tools[tool.name] = tool
        logger.info("Registered tool: %s", tool.name)

    def get(self, name: str) -> Optional[BaseTool]:
        """Return a tool by name."""
        return self._tools.get(name)

    def has(self, name: str) -> bool:
        """Return whether a tool is registered."""
        return name in self._tools

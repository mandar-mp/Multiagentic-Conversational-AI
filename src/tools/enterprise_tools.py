"""Initial enterprise tools.

These tools are intentionally conservative placeholders. They make the first
LangGraph workflow executable while keeping room for real integrations such as
SQL databases, document stores, schedulers, payment gateways, and remote agents.
"""

from typing import Any, Dict

from src.tools.base_tool import BaseTool


class CapabilityPlaceholderTool(BaseTool):
    """Returns a structured "not configured yet" result for a capability."""

    def __init__(self, name: str, description: str):
        super().__init__(name=name, description=description)

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Return a stable response shape for future capability integrations."""
        return {
            "status": "not_configured",
            "message": (
                f"The {self.name} capability was selected, but its production "
                "integration is not configured yet."
            ),
            "input": input_data,
        }


class GeneralAssistantTool(BaseTool):
    """Fallback tool for requests that do not need a specialized integration."""

    def __init__(self):
        super().__init__(
            name="general_assistant",
            description="Handles general enterprise assistant requests.",
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "success",
            "message": "General assistant handled the request.",
            "input": input_data,
        }


def build_default_tool_registry() -> "ToolRegistry":
    """Create tools for all phase-one capabilities."""
    from src.tools.tool_registry import ToolRegistry

    registry = ToolRegistry()
    registry.register(GeneralAssistantTool())
    registry.register(CapabilityPlaceholderTool("bi_analytics", "Structured data analytics tool."))
    registry.register(CapabilityPlaceholderTool("document_intelligence", "Document intelligence tool."))
    registry.register(CapabilityPlaceholderTool("scheduler_notification", "Scheduler and notification tool."))
    registry.register(CapabilityPlaceholderTool("export_report", "Report export tool."))
    registry.register(CapabilityPlaceholderTool("remote_agent", "Remote agent connector tool."))
    registry.register(CapabilityPlaceholderTool("payment", "Payment workflow tool."))
    return registry

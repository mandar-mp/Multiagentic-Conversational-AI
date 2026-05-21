"""Registry for enterprise agent capabilities.

The registry is intentionally data-driven. New agents can be added by
registering another capability record, without changing the orchestrator's
routing logic.
"""

from typing import Dict, Iterable, List, Optional
import logging

from src.models.agent import AgentCapability

logger = logging.getLogger(__name__)


class AgentRegistry:
    """In-memory capability registry for the first platform phase."""

    def __init__(self, capabilities: Optional[Iterable[AgentCapability]] = None):
        self._capabilities: Dict[str, AgentCapability] = {}
        initial_capabilities = default_capabilities() if capabilities is None else capabilities
        for capability in initial_capabilities:
            self.register(capability)

    def register(self, capability: AgentCapability) -> None:
        """Register or replace a capability."""
        self._capabilities[capability.name] = capability
        logger.info("Registered capability: %s", capability.name)

    def get(self, name: str) -> Optional[AgentCapability]:
        """Return a capability by name."""
        return self._capabilities.get(name)

    def list_enabled(self) -> List[AgentCapability]:
        """Return enabled capabilities."""
        return [item for item in self._capabilities.values() if item.enabled]

    def find_by_intent(self, intent: str) -> List[AgentCapability]:
        """Return capabilities that explicitly support an intent."""
        normalized = intent.lower().strip()
        return [
            capability
            for capability in self.list_enabled()
            if normalized in [item.lower() for item in capability.intents]
        ]


def default_capabilities() -> List[AgentCapability]:
    """Capabilities available in phase one.

    BI, document intelligence, and scheduling are intentionally registered as
    capabilities rather than hard-coded workflow branches. Payment and remote
    agent connectors are included but high-risk or external by default.
    """
    return [
        AgentCapability(
            name="general_assistant",
            display_name="General Assistant",
            category="core",
            description="Handles general enterprise questions and fallback chat.",
            intents=["general_question", "unknown"],
            keywords=["help", "explain", "summarize", "what is", "how do"],
            required_permissions=[],
            risk_level="low",
        ),
        AgentCapability(
            name="bi_analytics",
            display_name="BI Analytics",
            category="analytics",
            description="Answers business questions from structured data sources.",
            intents=["analytics", "reporting", "kpi"],
            keywords=[
                "sales",
                "revenue",
                "growth",
                "yoy",
                "wow",
                "mom",
                "margin",
                "kpi",
                "dashboard",
                "chart",
                "trend",
            ],
            required_permissions=["analytics:read"],
            risk_level="low",
        ),
        AgentCapability(
            name="database_analytics",
            display_name="Database Analytics",
            category="analytics",
            description="Answers analytical questions by generating safe read-only SQL, executing it, and visualizing results.",
            intents=["analytics", "database_query", "reporting", "kpi"],
            keywords=[
                "database",
                "sql",
                "table",
                "query",
                "sales",
                "revenue",
                "orders",
                "customers",
                "growth",
                "trend",
                "chart",
                "graph",
                "top",
                "count",
                "average",
                "sum",
                "compare",
            ],
            required_permissions=["analytics:read", "database:read"],
            risk_level="low",
        ),
        AgentCapability(
            name="document_intelligence",
            display_name="Document Intelligence",
            category="knowledge",
            description="Searches and answers from documents, PDFs, images, and files.",
            intents=["document_search", "knowledge_search"],
            keywords=["pdf", "document", "policy", "contract", "invoice", "image", "word", "file"],
            required_permissions=["documents:read"],
            risk_level="low",
        ),
        AgentCapability(
            name="scheduler_notification",
            display_name="Scheduler and Notification",
            category="automation",
            description="Schedules alerts, reminders, recurring jobs, and notifications.",
            intents=["schedule", "notification"],
            keywords=["schedule", "alert", "remind", "every monday", "email", "notify"],
            required_permissions=["scheduler:write", "notifications:send"],
            risk_level="medium",
        ),
        AgentCapability(
            name="export_report",
            display_name="Report Export",
            category="reporting",
            description="Exports results to PDF, Excel, CSV, or presentations.",
            intents=["export"],
            keywords=["export", "pdf", "excel", "csv", "powerpoint", "download"],
            required_permissions=["reports:export"],
            risk_level="medium",
        ),
        AgentCapability(
            name="payment",
            display_name="Payment",
            category="finance",
            description="Initiates or checks payments through controlled payment tools.",
            intents=["payment"],
            keywords=["pay", "payment", "refund", "invoice payment", "transfer"],
            required_permissions=["payments:write"],
            risk_level="high",
        ),
        AgentCapability(
            name="remote_agent",
            display_name="Remote Agent Connector",
            category="integration",
            description="Delegates tasks to approved remote agents or enterprise services.",
            intents=["remote_agent"],
            keywords=["remote agent", "external agent", "mcp", "delegate"],
            required_permissions=["remote_agents:invoke"],
            risk_level="medium",
        ),
    ]

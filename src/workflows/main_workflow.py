"""Main LangGraph workflow for the enterprise agent platform."""

from typing import Optional
import logging

from src.agents.platform_agents import (
    AuditLoggingAgent,
    AuthorizationAgent,
    CapabilityMatchingAgent,
    ConversationContextAgent,
    GuardrailAgent,
    IntentRouterAgent,
    PlanningAgent,
    ResponseGenerationAgent,
    ToolExecutionAgent,
)
from src.models.state import GraphState
from src.services.agent_registry import AgentRegistry
from src.tools.enterprise_tools import build_default_tool_registry
from src.tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


def create_main_workflow(
    llm_service: Optional[object] = None,
    agent_registry: Optional[AgentRegistry] = None,
    tool_registry: Optional[ToolRegistry] = None,
):
    """
    Create the core enterprise LangGraph workflow.

    The graph is intentionally capability-driven:
    user query -> intent -> capability match -> plan -> auth -> guardrails
    -> execution -> response.

    Capability agents such as BI, document intelligence, payments, and
    schedulers can be added by registering capabilities and tools, without
    changing the core graph topology.
    """
    try:
        from langgraph.graph import END, StateGraph
    except ImportError as exc:
        logger.error("LangGraph is not installed or not importable: %s", exc)
        raise

    registry = agent_registry or AgentRegistry()
    tools = tool_registry or build_default_tool_registry()

    context_agent = ConversationContextAgent()
    intent_router = IntentRouterAgent()
    capability_matcher = CapabilityMatchingAgent(registry)
    planner = PlanningAgent(registry)
    authorization = AuthorizationAgent(registry)
    guardrails = GuardrailAgent()
    executor = ToolExecutionAgent(tools)
    responder = ResponseGenerationAgent(llm_service)
    audit_logger = AuditLoggingAgent()

    workflow = StateGraph(GraphState)
    workflow.add_node("conversation_context", context_agent.process)
    workflow.add_node("intent_router", intent_router.process)
    workflow.add_node("capability_matcher", capability_matcher.process)
    workflow.add_node("planner", planner.process)
    workflow.add_node("authorization", authorization.process)
    workflow.add_node("guardrails", guardrails.process)
    workflow.add_node("executor", executor.process)
    workflow.add_node("response_generator", responder.process)
    workflow.add_node("audit_logger", audit_logger.process)

    workflow.set_entry_point("conversation_context")
    workflow.add_edge("conversation_context", "intent_router")
    workflow.add_edge("intent_router", "capability_matcher")
    workflow.add_edge("capability_matcher", "planner")
    workflow.add_edge("planner", "authorization")
    workflow.add_edge("authorization", "guardrails")
    workflow.add_edge("guardrails", "executor")
    workflow.add_edge("executor", "response_generator")
    workflow.add_edge("response_generator", "audit_logger")
    workflow.add_edge("audit_logger", END)

    compiled = workflow.compile()
    logger.info("Enterprise agent workflow compiled successfully")
    return compiled

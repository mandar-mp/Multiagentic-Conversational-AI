"""Main LangGraph workflow for the enterprise agent platform."""

from typing import Any, Optional
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
from src.agents.database_agents import (
    DatabaseExecutionAgent,
    ResultInterpretationAgent,
    SQLGenerationAgent,
    SQLPlanningAgent,
    SQLValidationAgent,
    VisualizationAgent,
)
from config.settings import settings
from src.models.state import GraphState
from src.services.agent_registry import AgentRegistry
from src.services.prompt_service import PromptService
from src.services.database_analytics_service import DatabaseAnalyticsService
from src.tools.enterprise_tools import build_default_tool_registry
from src.tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


def create_main_workflow(
    llm_service: Optional[object] = None,
    agent_registry: Optional[AgentRegistry] = None,
    tool_registry: Optional[ToolRegistry] = None,
    prompt_service: Optional[PromptService] = None,
    db_service: Optional[DatabaseAnalyticsService] = None,
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
    prompt_service = prompt_service or PromptService()
    analytics_db_url = settings.analytics_db_url if hasattr(settings, 'analytics_db_url') and settings.analytics_db_url else None
    db_service = db_service or DatabaseAnalyticsService(
        db_url=analytics_db_url,
        dialect=settings.analytics_db_dialect if hasattr(settings, 'analytics_db_dialect') else None,
        allowed_tables=settings.analytics_allowed_tables if hasattr(settings, 'analytics_allowed_tables') else None,
        blocked_tables=settings.analytics_blocked_tables if hasattr(settings, 'analytics_blocked_tables') else None,
        max_rows=settings.analytics_max_rows if hasattr(settings, 'analytics_max_rows') else 200,
        query_timeout=settings.analytics_query_timeout if hasattr(settings, 'analytics_query_timeout') else 30,
        echo=settings.analytics_enable_sql_echo if hasattr(settings, 'analytics_enable_sql_echo') else False,
    )

    context_agent = ConversationContextAgent()
    intent_router = IntentRouterAgent()
    capability_matcher = CapabilityMatchingAgent(registry)
    planner = PlanningAgent(registry)
    authorization = AuthorizationAgent(registry)
    guardrails = GuardrailAgent()
    sql_planning = SQLPlanningAgent(prompt_service, llm_service, db_service)
    sql_generation = SQLGenerationAgent(prompt_service, llm_service, db_service)
    sql_validation = SQLValidationAgent(prompt_service, llm_service, db_service)
    db_executor = DatabaseExecutionAgent(db_service)
    visualization = VisualizationAgent(prompt_service, llm_service)
    data_interpreter = ResultInterpretationAgent(prompt_service, llm_service)
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
    workflow.add_node("sql_planning", sql_planning.process)
    workflow.add_node("sql_generation", sql_generation.process)
    workflow.add_node("sql_validation", sql_validation.process)
    workflow.add_node("db_execution", db_executor.process)
    workflow.add_node("visualization", visualization.process)
    workflow.add_node("data_interpretation", data_interpreter.process)
    workflow.add_node("executor", executor.process)
    workflow.add_node("response_generator", responder.process)
    workflow.add_node("audit_logger", audit_logger.process)

    workflow.set_entry_point("conversation_context")
    workflow.add_edge("conversation_context", "intent_router")
    workflow.add_edge("intent_router", "capability_matcher")
    workflow.add_edge("capability_matcher", "planner")
    workflow.add_edge("planner", "authorization")
    workflow.add_edge("authorization", "guardrails")

    def _route_after_guardrails(state: Any) -> str:
        data = state if isinstance(state, dict) else getattr(state, "model_dump", lambda: state)()
        guardrails_state = data.get("guardrails") or {}
        if not guardrails_state.get("passed", False):
            return "response_generator"
        selected = None
        capability_matches = data.get("capability_matches") or []
        if capability_matches:
            first_match = capability_matches[0]
            selected = first_match.get("capability_name") if isinstance(first_match, dict) else getattr(first_match, "capability_name", None)
        if selected == "database_analytics":
            return "sql_planning"
        return "executor"

    workflow.add_conditional_edges("guardrails", _route_after_guardrails)
    workflow.add_edge("sql_planning", "sql_generation")
    workflow.add_edge("sql_generation", "sql_validation")
    workflow.add_edge("sql_validation", "db_execution")
    workflow.add_edge("db_execution", "visualization")
    workflow.add_edge("visualization", "data_interpretation")
    workflow.add_edge("data_interpretation", "response_generator")
    workflow.add_edge("executor", "response_generator")
    workflow.add_edge("response_generator", "audit_logger")
    workflow.add_edge("audit_logger", END)

    compiled = workflow.compile()
    logger.info("Enterprise agent workflow compiled successfully")
    
    compiled.get_graph().draw_mermaid_png(output_file_path="workflow_image.png")
    # graph_image = compiled.get_graph().draw_png()
    # with open("workflow_image.png", "wb") as f:
    #     f.write(graph_image)
    return compiled

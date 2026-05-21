"""Application state model for LangGraph."""

from typing import Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field

from src.models.agent import CapabilityMatch, IntentResult, PlanStep


class GraphState(TypedDict, total=False):
    """LangGraph-compatible state schema.

    Older LangGraph releases are most predictable with TypedDict schemas. The
    Pydantic AppState below remains useful for validation, tests, and API-facing
    documentation.
    """

    conversation_id: str
    current_input: str
    conversation_history: List[Dict[str, str]]
    user_id: Optional[str]
    user_context: Dict[str, Any]
    intent_result: Dict[str, Any]
    capability_matches: List[Dict[str, Any]]
    plan: List[Dict[str, Any]]
    authorization: Dict[str, Any]
    guardrails: Dict[str, Any]
    execution_results: List[Dict[str, Any]]
    analytics_plan: Dict[str, Any]
    generated_sql: str
    sql_generation_assumptions: List[str]
    sql_generation_confidence: float
    sql_validation: Dict[str, Any]
    sql_execution: Dict[str, Any]
    visualization: Dict[str, Any]
    data_interpretation: Dict[str, Any]
    agent_responses: Dict[str, Any]
    routing_decision: Optional[str]
    pending_clarification: Optional[str]
    final_response: Optional[str]
    metadata: Dict[str, Any]
    errors: List[str]


class AppState(BaseModel):
    """
    Application state for the enterprise agent graph.

    The fields from the original chatbot are kept for compatibility, while the
    newer fields model a generic enterprise workflow that can route to BI,
    documents, payments, schedulers, remote agents, or future capabilities.
    """
    
    conversation_id: str
    current_input: str
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    user_id: Optional[str] = None
    user_context: Dict[str, Any] = Field(default_factory=dict)

    intent_result: Optional[IntentResult] = None
    capability_matches: List[CapabilityMatch] = Field(default_factory=list)
    plan: List[PlanStep] = Field(default_factory=list)
    authorization: Dict[str, Any] = Field(default_factory=dict)
    guardrails: Dict[str, Any] = Field(default_factory=dict)
    execution_results: List[Dict[str, Any]] = Field(default_factory=list)

    agent_responses: Dict[str, Any] = Field(default_factory=dict)
    routing_decision: Optional[str] = None
    pending_clarification: Optional[str] = None
    final_response: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)

    analytics_plan: Dict[str, Any] = Field(default_factory=dict)
    generated_sql: Optional[str] = None
    sql_generation_assumptions: List[str] = Field(default_factory=list)
    sql_generation_confidence: float = 0.0
    sql_validation: Dict[str, Any] = Field(default_factory=dict)
    sql_execution: Dict[str, Any] = Field(default_factory=dict)
    visualization: Dict[str, Any] = Field(default_factory=dict)
    data_interpretation: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True

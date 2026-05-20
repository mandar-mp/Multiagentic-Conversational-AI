"""Schemas shared by the enterprise agent platform."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentCapability(BaseModel):
    """Describes one capability that can be routed to by the orchestrator."""

    name: str
    display_name: str
    description: str
    category: str
    intents: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    required_permissions: List[str] = Field(default_factory=list)
    risk_level: str = Field(default="low", description="low, medium, high")
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    remote_endpoint: Optional[str] = None


class IntentResult(BaseModel):
    """Normalized intent classification output."""

    intent: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    entities: Dict[str, Any] = Field(default_factory=dict)
    needs_clarification: bool = False
    clarification_question: Optional[str] = None


class CapabilityMatch(BaseModel):
    """A candidate capability selected for the current request."""

    capability_name: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reason: str


class PlanStep(BaseModel):
    """One executable step in a multi-agent plan."""

    step_id: str
    agent_name: str
    action: str
    input: Dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = False
    status: str = "pending"


class AgentExecutionResult(BaseModel):
    """Standard result returned by every executable agent or tool."""

    agent_name: str
    status: str
    output: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

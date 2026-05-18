"""
Application state model for LangGraph
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AppState(BaseModel):
    """
    Application state for LangGraph workflow
    Represents the current state across the agent network
    """
    
    conversation_id: str
    current_input: str
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    agent_responses: Dict[str, Any] = Field(default_factory=dict)
    routing_decision: Optional[str] = None
    final_response: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True

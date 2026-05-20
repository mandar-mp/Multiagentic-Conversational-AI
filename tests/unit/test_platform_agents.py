"""Tests for the generic enterprise platform agents."""

import pytest

from src.agents.platform_agents import (
    AuthorizationAgent,
    CapabilityMatchingAgent,
    IntentRouterAgent,
    PlanningAgent,
)
from src.services.agent_registry import AgentRegistry


@pytest.mark.asyncio
async def test_intent_router_detects_analytics_request():
    agent = IntentRouterAgent()

    result = await agent.process(
        {
            "conversation_id": "test",
            "current_input": "Show week on week sales growth by region",
            "conversation_history": [],
        }
    )

    assert result["intent_result"]["intent"] == "analytics"
    assert result["routing_decision"] == "analytics"


@pytest.mark.asyncio
async def test_capability_matching_selects_bi_analytics():
    registry = AgentRegistry()
    agent = CapabilityMatchingAgent(registry)

    result = await agent.process(
        {
            "current_input": "Show YoY revenue comparison",
            "intent_result": {"intent": "analytics", "confidence": 0.9},
        }
    )

    assert result["capability_matches"][0]["capability_name"] == "bi_analytics"


@pytest.mark.asyncio
async def test_planning_marks_scheduler_as_approval_required():
    registry = AgentRegistry()
    agent = PlanningAgent(registry)

    result = await agent.process(
        {
            "current_input": "Schedule an email alert every Monday",
            "capability_matches": [
                {
                    "capability_name": "scheduler_notification",
                    "confidence": 0.9,
                    "reason": "test",
                }
            ],
        }
    )

    assert result["plan"][0]["agent_name"] == "scheduler_notification"
    assert result["plan"][0]["requires_approval"] is True


@pytest.mark.asyncio
async def test_authorization_allows_low_risk_without_configured_auth():
    registry = AgentRegistry()
    agent = AuthorizationAgent(registry)

    result = await agent.process(
        {
            "plan": [
                {
                    "step_id": "step_1",
                    "agent_name": "bi_analytics",
                    "action": "execute_bi_analytics",
                    "input": {},
                    "requires_approval": False,
                    "status": "pending",
                }
            ],
            "user_context": {},
        }
    )

    assert result["authorization"]["allowed"] is True

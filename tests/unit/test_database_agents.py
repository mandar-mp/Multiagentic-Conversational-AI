"""Tests for the database analytics agent pipeline."""

import pytest

from src.agents.database_agents import SQLGenerationAgent, SQLValidationAgent
from src.services.database_analytics_service import DatabaseAnalyticsService
from src.services.prompt_service import PromptService


class DummyLLM:
    def __init__(self, response: str):
        self.response = response

    async def generate(self, prompt: str, **kwargs):
        return self.response

    async def generate_with_history(self, messages, **kwargs):
        return "ok"


@pytest.mark.asyncio
async def test_sql_generation_agent_parses_sql_from_llm_output():
    llm = DummyLLM(
        '{"sql": "SELECT account_id, SUM(amount) AS total_amount FROM transactions GROUP BY account_id LIMIT 10", "assumptions": ["Using transactions table"], "confidence": 0.92}'
    )
    agent = SQLGenerationAgent(PromptService(), llm, DatabaseAnalyticsService(db_url=None))

    result = await agent.process(
        {
            "current_input": "Top accounts by transaction amount",
            "analytics_plan": {"ready": True},
        }
    )

    assert result["generated_sql"].startswith("SELECT account_id")
    assert result["sql_generation_confidence"] == 0.92
    assert "assumptions" in result


@pytest.mark.asyncio
async def test_sql_validation_agent_blocks_non_select_sql():
    llm = DummyLLM('{"approved": false, "reason": "Non-read-only SQL detected."}')
    agent = SQLValidationAgent(PromptService(), llm, DatabaseAnalyticsService(db_url=None))

    result = await agent.process({"generated_sql": "DELETE FROM users"})

    assert result["sql_validation"]["approved"] is False
    assert "forbidden" in result["sql_validation"]["reason"].lower() or "read-only" in result["sql_validation"]["reason"].lower()

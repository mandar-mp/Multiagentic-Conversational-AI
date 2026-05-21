"""Database analytics agents for SQL planning, validation, execution, and visualization."""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Union

from src.models.state import AppState
from src.services.database_analytics_service import DatabaseAnalyticsService
from src.services.prompt_service import PromptService

logger = logging.getLogger(__name__)


def _as_dict(state: Union[AppState, Dict[str, Any]]) -> Dict[str, Any]:
    if isinstance(state, dict):
        return state
    if hasattr(state, "model_dump"):
        return state.model_dump()
    if hasattr(state, "dict"):
        return state.dict()
    raise TypeError(f"Unsupported state type: {type(state)}")


def _parse_json_response(raw: str) -> Dict[str, Any]:
    if not raw:
        return {}

    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            candidate = raw[start:end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass
    logger.debug("Unable to parse JSON response from LLM: %s", raw)
    return {}


class SQLPlanningAgent:
    """Builds a grounded analytics plan from the user question."""

    def __init__(
        self,
        prompt_service: PromptService,
        llm_service: Any,
        db_service: DatabaseAnalyticsService,
    ):
        self.prompt_service = prompt_service
        self.llm_service = llm_service
        self.db_service = db_service

    async def process(self, state: Union[AppState, Dict[str, Any]]) -> Dict[str, Any]:
        data = _as_dict(state)
        question = (data.get("current_input") or "").strip()
        schema_context = self.db_service.get_schema_context()
        conversation_context = data.get("conversation_history") or []

        prompt = self.prompt_service.render(
            "sql_planning_prompt.txt",
            question=question,
            conversation_context=json.dumps(conversation_context, indent=2),
            schema_context=json.dumps(schema_context, indent=2),
            analytics_plan="",
        )

        raw = await self.llm_service.generate(prompt)
        plan = _parse_json_response(raw)
        if not plan:
            plan = {
                "ready": False,
                "metric": None,
                "dimensions": [],
                "filters": [],
                "time_grain": None,
                "sort": None,
                "limit": 50,
                "visualization": {
                    "required": False,
                    "type": "table",
                    "x": None,
                    "y": None,
                    "series": None,
                    "title": "Analytics result",
                },
                "clarification_question": "I need more detail to determine the right analytics query. Can you clarify your request?",
            }

        output: Dict[str, Any] = {"analytics_plan": plan}
        if plan.get("clarification_question"):
            output["pending_clarification"] = plan["clarification_question"]
        return output


class SQLGenerationAgent:
    """Converts an analytics plan into safe SQL."""

    def __init__(
        self,
        prompt_service: PromptService,
        llm_service: Any,
        db_service: DatabaseAnalyticsService,
    ):
        self.prompt_service = prompt_service
        self.llm_service = llm_service
        self.db_service = db_service

    async def process(self, state: Union[AppState, Dict[str, Any]]) -> Dict[str, Any]:
        data = _as_dict(state)
        question = (data.get("current_input") or "").strip()
        analytics_plan = data.get("analytics_plan") or {}
        schema_context = self.db_service.get_schema_context()

        prompt = self.prompt_service.render(
            "sql_generation_prompt.txt",
            question=question,
            analytics_plan=json.dumps(analytics_plan, indent=2),
            schema_context=json.dumps(schema_context, indent=2),
            dialect=self.db_service.get_dialect(),
            max_rows=self.db_service.max_rows,
        )

        raw = await self.llm_service.generate(prompt)
        parsed = _parse_json_response(raw)
        sql = parsed.get("sql") if isinstance(parsed.get("sql"), str) else ""
        return {
            "generated_sql": sql,
            "sql_generation_assumptions": parsed.get("assumptions", []),
            "sql_generation_confidence": float(parsed.get("confidence", 0.0)) if parsed.get("confidence") is not None else 0.0,
        }


class SQLValidationAgent:
    """Validates generated SQL against schema and safety guardrails."""

    def __init__(
        self,
        prompt_service: PromptService,
        llm_service: Any,
        db_service: DatabaseAnalyticsService,
    ):
        self.prompt_service = prompt_service
        self.llm_service = llm_service
        self.db_service = db_service

    async def process(self, state: Union[AppState, Dict[str, Any]]) -> Dict[str, Any]:
        data = _as_dict(state)
        generated_sql = (data.get("generated_sql") or "").strip()
        analytics_plan = data.get("analytics_plan") or {}
        schema_context = self.db_service.get_schema_context()

        if not generated_sql:
            return {
                "sql_validation": {
                    "approved": False,
                    "reason": "No SQL could be generated from the analytics plan.",
                    "corrected_sql": None,
                }
            }

        service_validation = self.db_service.validate_sql(generated_sql)
        if not service_validation.valid:
            return {
                "sql_validation": {
                    "approved": False,
                    "reason": service_validation.reason or "Generated SQL failed safe validation.",
                    "corrected_sql": None,
                }
            }

        prompt = self.prompt_service.render(
            "sql_validation_prompt.txt",
            generated_sql=generated_sql,
            schema_context=json.dumps(schema_context, indent=2),
            analytics_plan=json.dumps(analytics_plan, indent=2),
        )

        raw = await self.llm_service.generate(prompt)
        parsed = _parse_json_response(raw)
        approved = parsed.get("approved") is not False
        corrected_sql = parsed.get("corrected_sql") or generated_sql
        if corrected_sql and corrected_sql != generated_sql:
            corrected_validation = self.db_service.validate_sql(corrected_sql)
            if not corrected_validation.valid:
                return {
                    "sql_validation": {
                        "approved": False,
                        "reason": corrected_validation.reason or "Corrected SQL failed validation.",
                        "corrected_sql": None,
                    }
                }
            generated_sql = corrected_sql
        if not approved:
            return {
                "sql_validation": {
                    "approved": False,
                    "reason": parsed.get("reason", "SQL validation declined the query."),
                    "corrected_sql": None,
                }
            }

        return {
            "sql_validation": {
                "approved": True,
                "reason": parsed.get("reason", "SQL approved for execution."),
                "corrected_sql": generated_sql,
            }
        }


class DatabaseExecutionAgent:
    """Executes approved analytics SQL and returns query results."""

    def __init__(self, db_service: DatabaseAnalyticsService):
        self.db_service = db_service

    async def process(self, state: Union[AppState, Dict[str, Any]]) -> Dict[str, Any]:
        data = _as_dict(state)
        validation = data.get("sql_validation") or {}
        if not validation.get("approved"):
            return {
                "sql_execution": {
                    "status": "blocked",
                    "message": validation.get("reason") or "SQL execution is blocked.",
                    "sql": (validation.get("corrected_sql") or data.get("generated_sql") or ""),
                    "rows": [],
                    "columns": [],
                }
            }

        sql = validation.get("corrected_sql") or data.get("generated_sql")
        if not sql:
            return {
                "sql_execution": {
                    "status": "error",
                    "message": "No SQL query is available for execution.",
                    "sql": "",
                    "rows": [],
                    "columns": [],
                }
            }

        result = self.db_service.execute_sql(sql)
        return {"sql_execution": result}


class VisualizationAgent:
    """Creates a frontend-friendly chart specification from analytics results."""

    def __init__(
        self,
        prompt_service: PromptService,
        llm_service: Any,
    ):
        self.prompt_service = prompt_service
        self.llm_service = llm_service

    async def process(self, state: Union[AppState, Dict[str, Any]]) -> Dict[str, Any]:
        data = _as_dict(state)
        question = (data.get("current_input") or "").strip()
        analytics_plan = data.get("analytics_plan") or {}
        query_result = data.get("sql_execution") or {}

        prompt = self.prompt_service.render(
            "visualization_prompt.txt",
            question=question,
            analytics_plan=json.dumps(analytics_plan, indent=2),
            query_result=json.dumps(query_result, indent=2),
        )

        raw = await self.llm_service.generate(prompt)
        chart = _parse_json_response(raw)
        if not chart.get("type"):
            chart = {
                "type": "table",
                "title": "Query result",
                "description": "Raw query result data.",
                "xKey": None,
                "yKey": None,
                "seriesKey": None,
                "columns": query_result.get("columns", []),
                "rows": query_result.get("rows", []),
            }

        return {"visualization": chart}


class ResultInterpretationAgent:
    """Generates a business-friendly summary of the database query result."""

    def __init__(
        self,
        prompt_service: PromptService,
        llm_service: Any,
    ):
        self.prompt_service = prompt_service
        self.llm_service = llm_service

    async def process(self, state: Union[AppState, Dict[str, Any]]) -> Dict[str, Any]:
        data = _as_dict(state)
        question = (data.get("current_input") or "").strip()
        sql = (data.get("sql_validation") or {}).get("corrected_sql") or data.get("generated_sql")
        analytics_plan = data.get("analytics_plan") or {}
        query_result = data.get("sql_execution") or {}

        prompt = self.prompt_service.render(
            "data_interpretation_prompt.txt",
            question=question,
            sql=sql,
            query_result=json.dumps(query_result, indent=2),
            analytics_plan=json.dumps(analytics_plan, indent=2),
        )

        raw = await self.llm_service.generate(prompt)
        parsed = _parse_json_response(raw)
        if not parsed.get("answer"):
            parsed = {
                "answer": query_result.get("message", "The query executed successfully."),
                "key_points": [],
                "limitations": [],
                "confidence": 0.0,
            }

        return {"data_interpretation": parsed}

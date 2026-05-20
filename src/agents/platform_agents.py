"""Core agents for the generic enterprise assistant platform."""

from typing import Any, Dict, List, Optional, Union
import logging
import re

from src.models.agent import CapabilityMatch, IntentResult, PlanStep
from src.models.state import AppState
from src.services.agent_registry import AgentRegistry
from src.tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


def _as_dict(state: Any) -> Dict[str, Any]:
    """Normalize LangGraph state into a plain dictionary."""
    if isinstance(state, dict):
        return state
    if hasattr(state, "model_dump"):
        return state.model_dump()
    if hasattr(state, "dict"):
        return state.dict()
    raise TypeError(f"Unsupported state type: {type(state)}")


def _history_with_current(state: Dict[str, Any]) -> List[Dict[str, str]]:
    """Return conversation history suitable for an LLM call."""
    history = list(state.get("conversation_history") or [])
    current_input = state.get("current_input")
    if current_input and (not history or history[-1].get("content") != current_input):
        history.append({"role": "user", "content": current_input})
    return history


class IntentRouterAgent:
    """Classifies a request into a broad enterprise intent."""

    _INTENT_PATTERNS = {
        "payment": [r"\bpay\b", r"\bpayment\b", r"\brefund\b", r"\btransfer\b"],
        "schedule": [r"\bschedule\b", r"\bremind\b", r"\bevery\s+\w+", r"\brecurring\b"],
        "notification": [r"\bnotify\b", r"\bsend\b.*\bemail\b", r"\balert\b"],
        "export": [r"\bexport\b", r"\bdownload\b", r"\bpdf\b", r"\bexcel\b", r"\bcsv\b"],
        "document_search": [r"\bpdf\b", r"\bdocument\b", r"\bcontract\b", r"\bpolicy\b", r"\bfile\b"],
        "remote_agent": [r"\bremote agent\b", r"\bmcp\b", r"\bdelegate\b"],
        "analytics": [
            r"\bsales\b",
            r"\brevenue\b",
            r"\bgrowth\b",
            r"\byoy\b",
            r"\bwow\b",
            r"\btrend\b",
            r"\bkpi\b",
            r"\bdashboard\b",
            r"\bchart\b",
        ],
    }

    async def process(self, state: Union[AppState, Dict[str, Any]]) -> Dict[str, Any]:
        data = _as_dict(state)
        query = (data.get("current_input") or "").strip()
        lowered = query.lower()

        matched_intent = "general_question"
        confidence = 0.45
        for intent, patterns in self._INTENT_PATTERNS.items():
            if any(re.search(pattern, lowered) for pattern in patterns):
                matched_intent = intent
                confidence = 0.82
                break

        needs_clarification = False
        clarification_question: Optional[str] = None
        if matched_intent in {"payment", "schedule"} and len(query.split()) < 5:
            needs_clarification = True
            clarification_question = "Please provide the target, amount or timing, and any required recipient details."

        intent_result = IntentResult(
            intent=matched_intent,
            confidence=confidence,
            entities={"raw_query": query},
            needs_clarification=needs_clarification,
            clarification_question=clarification_question,
        )
        return {
            "intent_result": intent_result.model_dump(),
            "routing_decision": matched_intent,
            "pending_clarification": clarification_question,
        }


class ConversationContextAgent:
    """Prepares compact conversation context for downstream agents."""

    async def process(self, state: Union[AppState, Dict[str, Any]]) -> Dict[str, Any]:
        data = _as_dict(state)
        history = data.get("conversation_history") or []
        user_context = dict(data.get("user_context") or {})

        user_context.setdefault("recent_message_count", len(history))
        if history:
            user_context.setdefault("last_role", history[-1].get("role"))

        return {"user_context": user_context}


class CapabilityMatchingAgent:
    """Matches an intent and request text to registered capabilities."""

    def __init__(self, registry: AgentRegistry):
        self.registry = registry

    async def process(self, state: Union[AppState, Dict[str, Any]]) -> Dict[str, Any]:
        data = _as_dict(state)
        query = (data.get("current_input") or "").lower()
        intent = (data.get("intent_result") or {}).get("intent", "unknown")

        matches: List[CapabilityMatch] = []
        for capability in self.registry.list_enabled():
            score = 0.0
            reasons: List[str] = []
            if intent.lower() in [item.lower() for item in capability.intents]:
                score += 0.65
                reasons.append(f"supports intent '{intent}'")

            keyword_hits = [keyword for keyword in capability.keywords if keyword.lower() in query]
            if keyword_hits:
                score += min(0.3, 0.08 * len(keyword_hits))
                reasons.append(f"matched keywords: {', '.join(keyword_hits[:3])}")

            if score > 0:
                matches.append(
                    CapabilityMatch(
                        capability_name=capability.name,
                        confidence=min(score, 0.95),
                        reason="; ".join(reasons),
                    )
                )

        if not matches:
            matches.append(
                CapabilityMatch(
                    capability_name="general_assistant",
                    confidence=0.45,
                    reason="fallback for requests without a specialized capability match",
                )
            )

        matches.sort(key=lambda item: item.confidence, reverse=True)
        return {"capability_matches": [match.model_dump() for match in matches[:3]]}


class PlanningAgent:
    """Creates a small executable plan from selected capabilities."""

    def __init__(self, registry: AgentRegistry):
        self.registry = registry

    async def process(self, state: Union[AppState, Dict[str, Any]]) -> Dict[str, Any]:
        data = _as_dict(state)
        matches = data.get("capability_matches") or []
        query = data.get("current_input") or ""
        plan: List[PlanStep] = []

        for index, match in enumerate(matches, start=1):
            capability_name = match.get("capability_name") if isinstance(match, dict) else match.capability_name
            capability = self.registry.get(capability_name)
            if not capability:
                continue

            plan.append(
                PlanStep(
                    step_id=f"step_{index}",
                    agent_name=capability.name,
                    action=f"execute_{capability.name}",
                    input={"query": query, "capability": capability.model_dump()},
                    requires_approval=capability.risk_level in {"medium", "high"},
                )
            )

        return {"plan": [step.model_dump() for step in plan]}


class AuthorizationAgent:
    """Checks user permissions before any tool or remote agent executes."""

    def __init__(self, registry: AgentRegistry):
        self.registry = registry

    async def process(self, state: Union[AppState, Dict[str, Any]]) -> Dict[str, Any]:
        data = _as_dict(state)
        user_context = data.get("user_context") or {}
        permissions = user_context.get("permissions")
        permission_set = set(permissions or [])
        decisions: Dict[str, Any] = {"allowed": True, "steps": {}}

        for step in data.get("plan") or []:
            step_dict = step if isinstance(step, dict) else step.model_dump()
            capability = self.registry.get(step_dict["agent_name"])
            if not capability:
                decisions["steps"][step_dict["step_id"]] = {
                    "allowed": False,
                    "reason": "Capability is not registered.",
                }
                decisions["allowed"] = False
                continue

            missing = [item for item in capability.required_permissions if item not in permission_set]
            if permissions is None and capability.risk_level == "low":
                # Development-friendly default: low-risk read style capabilities
                # can run until a real auth provider supplies permissions.
                missing = []

            allowed = not missing
            decisions["steps"][step_dict["step_id"]] = {
                "allowed": allowed,
                "missing_permissions": missing,
                "required_permissions": capability.required_permissions,
            }
            decisions["allowed"] = decisions["allowed"] and allowed

        return {"authorization": decisions}


class GuardrailAgent:
    """Applies enterprise safety checks before execution."""

    async def process(self, state: Union[AppState, Dict[str, Any]]) -> Dict[str, Any]:
        data = _as_dict(state)
        auth = data.get("authorization") or {}
        plan = data.get("plan") or []
        approved_actions = set((data.get("metadata") or {}).get("approved_actions") or [])
        blocked_steps: List[Dict[str, str]] = []

        for step in plan:
            step_dict = step if isinstance(step, dict) else step.model_dump()
            auth_step = (auth.get("steps") or {}).get(step_dict["step_id"], {})

            if not auth_step.get("allowed", False):
                blocked_steps.append(
                    {
                        "step_id": step_dict["step_id"],
                        "reason": "Missing required permissions.",
                    }
                )
                continue

            if step_dict.get("requires_approval") and step_dict["step_id"] not in approved_actions:
                blocked_steps.append(
                    {
                        "step_id": step_dict["step_id"],
                        "reason": "This action requires human approval before execution.",
                    }
                )

        pending = None
        if blocked_steps:
            pending = blocked_steps[0]["reason"]

        return {
            "guardrails": {"passed": not blocked_steps, "blocked_steps": blocked_steps},
            "pending_clarification": data.get("pending_clarification") or pending,
        }


class ToolExecutionAgent:
    """Executes approved plan steps through a controlled tool registry."""

    def __init__(self, tools: ToolRegistry):
        self.tools = tools

    async def process(self, state: Union[AppState, Dict[str, Any]]) -> Dict[str, Any]:
        data = _as_dict(state)
        guardrails = data.get("guardrails") or {}
        if not guardrails.get("passed", False):
            return {"execution_results": []}

        results: List[Dict[str, Any]] = []
        for step in data.get("plan") or []:
            step_dict = step if isinstance(step, dict) else step.model_dump()
            tool = self.tools.get(step_dict["agent_name"])
            if not tool:
                results.append(
                    {
                        "agent_name": step_dict["agent_name"],
                        "status": "error",
                        "error": "No tool registered for this capability.",
                    }
                )
                continue

            try:
                output = await tool.execute(step_dict.get("input") or {})
                results.append(
                    {
                        "agent_name": step_dict["agent_name"],
                        "status": output.get("status", "success"),
                        "output": output,
                    }
                )
            except Exception as exc:
                logger.exception("Tool execution failed for %s", step_dict["agent_name"])
                results.append(
                    {
                        "agent_name": step_dict["agent_name"],
                        "status": "error",
                        "error": str(exc),
                    }
                )

        return {"execution_results": results}


class ResponseGenerationAgent:
    """Creates the final user-facing response."""

    def __init__(self, llm_service: Optional[Any] = None):
        self.llm_service = llm_service

    async def process(self, state: Union[AppState, Dict[str, Any]]) -> Dict[str, Any]:
        data = _as_dict(state)
        pending = data.get("pending_clarification")
        if pending:
            return {"final_response": pending}

        intent = (data.get("intent_result") or {}).get("intent", "unknown")
        matches = data.get("capability_matches") or []
        selected = matches[0].get("capability_name") if matches else "general_assistant"
        results = data.get("execution_results") or []

        if selected == "general_assistant" and self.llm_service is not None:
            try:
                response = await self.llm_service.generate_with_history(_history_with_current(data))
                return {"final_response": response}
            except Exception as exc:
                logger.warning("General assistant LLM response failed: %s", exc)

        if not results:
            return {
                "final_response": (
                    f"I understood this as a '{intent}' request and selected "
                    f"'{selected}', but execution is waiting on permissions, approval, "
                    "or required configuration."
                )
            }

        first = results[0]
        output = first.get("output") or {}
        if first.get("status") == "not_configured":
            return {
                "final_response": (
                    f"I routed your request to the '{selected}' capability. "
                    f"{output.get('message')} Next step: connect the real enterprise "
                    "tool behind this capability."
                )
            }

        return {
            "final_response": output.get("message")
            or f"The '{selected}' capability completed the request."
        }


class AuditLoggingAgent:
    """Writes a structured audit log for enterprise traceability."""

    async def process(self, state: Union[AppState, Dict[str, Any]]) -> Dict[str, Any]:
        data = _as_dict(state)
        audit_event = {
            "conversation_id": data.get("conversation_id"),
            "user_id": data.get("user_id"),
            "intent": (data.get("intent_result") or {}).get("intent"),
            "routing_decision": data.get("routing_decision"),
            "capability_matches": data.get("capability_matches") or [],
            "plan": data.get("plan") or [],
            "authorization": data.get("authorization") or {},
            "guardrails": data.get("guardrails") or {},
            "execution_statuses": [
                {
                    "agent_name": result.get("agent_name"),
                    "status": result.get("status"),
                }
                for result in data.get("execution_results") or []
            ],
        }
        logger.info("agent_audit_event=%s", audit_event)
        metadata = dict(data.get("metadata") or {})
        metadata["audit_logged"] = True
        return {"metadata": metadata}

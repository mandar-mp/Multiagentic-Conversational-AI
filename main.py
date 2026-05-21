"""
Main application entry point
Multi-Agentic Conversational AI Chatbot using LangGraph
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config.settings import settings
from src.db.session import init_db
from src.models.message import Message
from src.services.conversation_service import ConversationService
from src.services.llm_service import LLMService
from src.services.prompt_service import PromptService
from src.services.database_analytics_service import DatabaseAnalyticsService
from src.utils.logger import setup_logger
from src.workflows.main_workflow import create_main_workflow

# Setup logging
logger = setup_logger(__name__)

conversation_service = ConversationService()
llm_service = LLMService(
    provider=settings.llm_provider,
    api_key=settings.llm_api_key,
    model=settings.llm_model,
    temperature=settings.llm_temperature,
    max_tokens=settings.llm_max_tokens,
    timeout=settings.llm_timeout,
)
analytics_db_url = settings.analytics_db_url or settings.db_url
analytics_service = DatabaseAnalyticsService(
    db_url=analytics_db_url,
    dialect=settings.analytics_db_dialect,
    allowed_tables=settings.analytics_allowed_tables,
    blocked_tables=settings.analytics_blocked_tables,
    max_rows=settings.analytics_max_rows,
    query_timeout=settings.analytics_query_timeout,
    echo=settings.analytics_enable_sql_echo,
)
agent_workflow = create_main_workflow(
    llm_service=llm_service,
    prompt_service=PromptService(),
    db_service=analytics_service,
)

# Configure root logger
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    environment: str


class ReadyResponse(BaseModel):
    """Readiness check response"""
    ready: bool
    message: str


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    user_context: dict = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Chat response model"""
    status: str
    response: str
    conversation_id: str
    metadata: dict = Field(default_factory=dict)


def _workflow_result_to_dict(result):
    """Normalize LangGraph output across versions."""
    if isinstance(result, dict):
        return result
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if hasattr(result, "dict"):
        return result.dict()
    return {}


def _round_confidence(value: Any) -> Optional[float]:
    """Return a compact confidence value for API metadata."""
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def _summarize_plan(plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Keep plan metadata useful without exposing full internal inputs."""
    summarized = []
    for step in plan or []:
        summarized.append(
            {
                "step_id": step.get("step_id"),
                "agent_name": step.get("agent_name"),
                "action": step.get("action"),
                "requires_approval": bool(step.get("requires_approval")),
                "status": step.get("status", "pending"),
            }
        )
    return summarized


def _summarize_execution_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Summarize tool results for explainability panels."""
    summarized = []
    for result in results or []:
        output = result.get("output") or {}
        summarized.append(
            {
                "agent_name": result.get("agent_name"),
                "status": result.get("status"),
                "message": output.get("message"),
                "error": result.get("error"),
            }
        )
    return summarized


def _build_agent_steps(workflow_result: Dict[str, Any]) -> List[Dict[str, str]]:
    """Build a user-safe trace of the workflow agents that participated."""
    guardrails = workflow_result.get("guardrails") or {}
    execution_results = workflow_result.get("execution_results") or []
    audit_logged = (workflow_result.get("metadata") or {}).get("audit_logged")

    return [
        {
            "name": "ConversationContextAgent",
            "role": "Prepared recent conversation context.",
            "status": "completed",
            "detail": "Added compact context such as recent message count.",
        },
        {
            "name": "IntentRouterAgent",
            "role": "Detected the user's intent.",
            "status": "completed" if workflow_result.get("intent_result") else "skipped",
            "detail": f"Intent: {(workflow_result.get('intent_result') or {}).get('intent', 'unknown')}",
        },
        {
            "name": "CapabilityMatchingAgent",
            "role": "Matched the request to enterprise capabilities.",
            "status": "completed" if workflow_result.get("capability_matches") else "skipped",
            "detail": "Ranked capabilities by intent and keyword matches.",
        },
        {
            "name": "PlanningAgent",
            "role": "Created executable plan steps.",
            "status": "completed" if workflow_result.get("plan") else "skipped",
            "detail": f"Plan steps: {len(workflow_result.get('plan') or [])}",
        },
        {
            "name": "AuthorizationAgent",
            "role": "Checked required permissions.",
            "status": "completed" if workflow_result.get("authorization") else "skipped",
            "detail": "Access allowed." if (workflow_result.get("authorization") or {}).get("allowed") else "Access blocked or not fully authorized.",
        },
        {
            "name": "GuardrailAgent",
            "role": "Applied approval and safety checks.",
            "status": "completed" if guardrails.get("passed") else "blocked",
            "detail": "No guardrail blocks." if guardrails.get("passed") else "One or more steps were blocked.",
        },
        {
            "name": "ToolExecutionAgent",
            "role": "Executed approved tools.",
            "status": "completed" if execution_results else "skipped",
            "detail": f"Tool results: {len(execution_results)}",
        },
        {
            "name": "ResponseGenerationAgent",
            "role": "Prepared the final user-facing answer.",
            "status": "completed" if workflow_result.get("final_response") else "skipped",
            "detail": "Generated response from workflow context and tool outputs.",
        },
        {
            "name": "AuditLoggingAgent",
            "role": "Recorded the workflow audit event.",
            "status": "completed" if audit_logged else "skipped",
            "detail": "Audit metadata was added." if audit_logged else "Audit flag was not returned.",
        },
    ]


def _build_response_trace(
    workflow_result: Dict[str, Any],
    history_payload: List[Dict[str, str]],
    duration_ms: int,
    workflow_fallback: bool = False,
) -> Dict[str, Any]:
    """Create explainability metadata suitable for enterprise chat users."""
    intent_result = workflow_result.get("intent_result") or {}
    capability_matches = workflow_result.get("capability_matches") or []
    selected_capability = (
        capability_matches[0].get("capability_name")
        if capability_matches
        else "general_assistant"
    )
    execution_results = workflow_result.get("execution_results") or []

    answer_source = "workflow"
    if workflow_fallback:
        answer_source = "direct_llm_fallback"
    elif selected_capability == "general_assistant" and not execution_results:
        answer_source = "general_llm"
    elif execution_results:
        answer_source = "tool_or_capability"

    if workflow_fallback:
        agent_steps = [
            {
                "name": "DirectLLMFallback",
                "role": "Generated an answer after workflow execution failed.",
                "status": "completed",
                "detail": "The main agent workflow raised an exception.",
            }
        ]
    else:
        agent_steps = _build_agent_steps(workflow_result)

    return {
        "summary": {
            "intent": intent_result.get("intent"),
            "intent_confidence": _round_confidence(intent_result.get("confidence")),
            "routing_decision": workflow_result.get("routing_decision"),
            "selected_capability": selected_capability,
            "answer_source": answer_source,
            "duration_ms": duration_ms,
        },
        "agents": agent_steps,
        "capability_matches": [
            {
                "capability_name": match.get("capability_name"),
                "confidence": _round_confidence(match.get("confidence")),
                "reason": match.get("reason"),
            }
            for match in capability_matches
        ],
        "plan": _summarize_plan(workflow_result.get("plan") or []),
        "authorization": workflow_result.get("authorization") or {},
        "guardrails": workflow_result.get("guardrails") or {},
        "execution_results": _summarize_execution_results(execution_results),
        "conversation_context": {
            "history_messages_used": len(history_payload),
            "used_prior_context": len(history_payload) > 1,
        },
        "model": {
            "provider": settings.llm_provider,
            "name": settings.llm_model,
        },
        "audit_logged": bool((workflow_result.get("metadata") or {}).get("audit_logged")),
        "workflow_fallback": workflow_fallback,
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management
    Startup and shutdown logic
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info("Initializing database schema")
    init_db()

    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multi-Agentic Conversational AI Chatbot",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for load balancers
    Always returns 200 if service is running
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment
    )


@app.get("/ready", response_model=ReadyResponse)
async def readiness_check():
    """
    Readiness check endpoint
    Verifies all dependencies are available
    """
    try:
        # Add checks for dependencies:
        # - Database connection
        # - LLM service
        # - Cache service
        # - etc.
        
        return ReadyResponse(
            ready=True,
            message="Application is ready to serve requests"
        )
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return ReadyResponse(
            ready=False,
            message=f"Application not ready: {str(e)}"
        )


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint
    Processes user messages through the multi-agent system
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message must not be empty")

    logger.info(f"Processing chat request: {request.message[:100]}")

    conversation_id = request.conversation_id
    conversation = None
    
    if conversation_id:
        conversation = conversation_service.get_conversation(conversation_id)
        if conversation is None:
            logger.warning(f"Conversation not found: {conversation_id}. Creating a new one.")
            conversation = conversation_service.create_conversation()
            conversation_id = conversation.conversation_id
            logger.info(f"Conversation created with id: {conversation_id}")
    else:
        conversation = conversation_service.create_conversation()
        conversation_id = conversation.conversation_id
        logger.info(f"Conversation id newly created: {conversation_id}")
    user_message = Message(role="user", content=request.message)
    conversation_service.add_message(conversation_id, user_message)

    history = conversation_service.get_conversation_history(conversation_id, limit=10)
    history_payload = [
        {"role": msg.role, "content": msg.content}
        for msg in history
    ]

    workflow_state = {
        "conversation_id": conversation_id,
        "current_input": request.message,
        "conversation_history": history_payload,
        "user_id": request.user_id,
        "user_context": request.user_context or {},
        "metadata": {
            "provider": settings.llm_provider,
            "model": settings.llm_model,
        },
    }

    started_at = time.perf_counter()

    try:
        workflow_result = _workflow_result_to_dict(await agent_workflow.ainvoke(workflow_state))
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        response_text = workflow_result.get("final_response") or ""
        trace = _build_response_trace(
            workflow_result=workflow_result,
            history_payload=history_payload,
            duration_ms=duration_ms,
        )
        response_metadata = {
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "intent": (workflow_result.get("intent_result") or {}).get("intent"),
            "intent_confidence": (workflow_result.get("intent_result") or {}).get("confidence"),
            "routing_decision": workflow_result.get("routing_decision"),
            "capability_matches": workflow_result.get("capability_matches", []),
            "plan": _summarize_plan(workflow_result.get("plan") or []),
            "authorization": workflow_result.get("authorization", {}),
            "guardrails": workflow_result.get("guardrails", {}),
            "execution_results": _summarize_execution_results(workflow_result.get("execution_results") or []),
            "sql_execution": workflow_result.get("sql_execution", {}),
            "chart": workflow_result.get("visualization"),
            "audit_logged": bool((workflow_result.get("metadata") or {}).get("audit_logged")),
            "duration_ms": duration_ms,
            "trace": trace,
        }
    except Exception as e:
        logger.exception("Agent workflow failed; falling back to direct LLM call: %s", str(e))
        response_text = await llm_service.generate_with_history(
            history_payload,
            provider=settings.llm_provider,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        fallback_result = {
            "final_response": response_text,
            "metadata": {"workflow_fallback": True},
        }
        response_metadata = {
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "workflow_fallback": True,
            "duration_ms": duration_ms,
            "trace": _build_response_trace(
                workflow_result=fallback_result,
                history_payload=history_payload,
                duration_ms=duration_ms,
                workflow_fallback=True,
            ),
        }

    assistant_message = Message(
        role="assistant",
        content=response_text,
        metadata=response_metadata,
    )
    conversation_service.add_message(conversation_id, assistant_message)

    return ChatResponse(
        status="success",
        response=response_text,
        conversation_id=conversation_id,
        metadata=response_metadata,
    )


@app.get("/api/v1/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Retrieve conversation history
    """
    try:
        logger.info(f"Retrieving conversation: {conversation_id}")
        
        conversation = conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {
            "conversation_id": conversation_id,
            "messages": [
                {
                    "role": message.role,
                    "content": message.content,
                    "timestamp": message.timestamp.isoformat(),
                    "agent_name": message.agent_name,
                    "metadata": message.metadata,
                }
                for message in conversation.messages
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )

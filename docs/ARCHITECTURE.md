# Architecture Documentation

This project is a FastAPI-backed, LangGraph-orchestrated conversational AI platform. It began as a multi-agent chatbot scaffold and now uses a capability-driven enterprise assistant design: incoming chat messages are persisted, routed through a fixed graph of platform agents, matched to registered capabilities, checked for authorization and guardrails, optionally executed through registered tools, and returned to the client as a normal chat response.

## System Overview

```text
User
  |
  | HTTP
  v
Client UI
  |-- Angular app in frontend/
  |-- Streamlit app in streamlit_ui/
  |
  | POST /api/v1/chat
  v
FastAPI API Layer (main.py)
  |
  | creates/loads conversation
  | stores user message
  | builds workflow state
  v
LangGraph Workflow (src/workflows/main_workflow.py)
  |
  +--> ConversationContextAgent
  +--> IntentRouterAgent
  +--> CapabilityMatchingAgent
  +--> PlanningAgent
  +--> AuthorizationAgent
  +--> GuardrailAgent
  +--> ToolExecutionAgent
  +--> ResponseGenerationAgent
  +--> AuditLoggingAgent
  |
  v
FastAPI API Layer
  |
  | stores assistant message
  v
Client UI
```

## Runtime Components

### API Layer

`main.py` owns the HTTP boundary and application lifecycle.

Key responsibilities:

- Initializes FastAPI, CORS, logging, database schema, `ConversationService`, `LLMService`, and the compiled LangGraph workflow.
- Exposes health and readiness endpoints:
  - `GET /health`
  - `GET /ready`
- Exposes chat and history endpoints:
  - `POST /api/v1/chat`
  - `GET /api/v1/conversations/{conversation_id}`
- Validates empty chat messages before workflow execution.
- Creates a new conversation when no `conversation_id` is supplied or the supplied ID does not exist.
- Persists the user message before workflow execution and the assistant response after workflow execution.
- Falls back to a direct LLM call if the LangGraph workflow raises an exception.

### Configuration

`config/settings.py` defines the application settings with `pydantic-settings`.

Important settings:

- App/API: `APP_NAME`, `APP_VERSION`, `ENVIRONMENT`, `DEBUG`, `API_HOST`, `API_PORT`, `API_PREFIX`
- LLM: `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`, `LLM_TEMPERATURE`, `LLM_MAX_TOKENS`, `LLM_TIMEOUT`
- Database: `DB_TYPE`, `DB_URL`
- Optional infrastructure placeholders: Redis and vector store settings
- Logging and security: `LOG_LEVEL`, `LOG_DIR`, `SECRET_KEY`, `CORS_ORIGINS`

`.env.example` shows the expected environment variables.

### Persistence Layer

The current persistence layer is SQLAlchemy-backed and defaults to SQLite at `sqlite:///./app.db`.

Files:

- `src/db/session.py`: SQLAlchemy engine, session factory, and `init_db()`
- `src/db/models.py`: database tables
- `src/db/crud.py`: persistence helpers
- `src/services/conversation_service.py`: service API used by `main.py`

Current tables:

```text
conversations
  id
  conversation_id
  created_at
  updated_at
  metadata

messages
  id
  conversation_id
  role
  content
  created_at
  agent_name
  metadata
```

`ConversationService` converts SQLAlchemy rows into Pydantic `Conversation` and `Message` models so the rest of the app does not work directly with ORM objects.

### LLM Service

`src/services/llm_service.py` provides one provider-neutral interface:

- `generate(prompt, **kwargs)`
- `generate_with_history(messages, **kwargs)`

Supported provider branches:

- `gemini` through `google-genai`
- `openai` through the OpenAI Python client
- `anthropic` through the Anthropic Python client

The workflow uses the LLM mainly in `ResponseGenerationAgent` for general assistant fallback. `main.py` also uses it directly if graph execution fails.

## LangGraph Workflow

`src/workflows/main_workflow.py` builds the main graph with `StateGraph(GraphState)`.

The graph topology is intentionally stable:

```text
conversation_context
  -> intent_router
  -> capability_matcher
  -> planner
  -> authorization
  -> guardrails
  -> executor
  -> response_generator
  -> audit_logger
  -> END
```

The architecture is capability-driven rather than branch-heavy. To add a new enterprise function, register a capability and matching tool. The graph usually does not need a new node.

## Workflow State

`src/models/state.py` contains two state shapes:

- `GraphState`: a `TypedDict` used by LangGraph for compatibility with the currently pinned LangGraph version.
- `AppState`: a Pydantic model used for validation, tests, and documentation.

Important state fields:

```text
conversation_id
current_input
conversation_history
user_id
user_context
intent_result
capability_matches
plan
authorization
guardrails
execution_results
routing_decision
pending_clarification
final_response
metadata
errors
```

## Platform Agents

The active platform agents live in `src/agents/platform_agents.py`.

### ConversationContextAgent

Adds compact context into `user_context`, such as recent message count and last message role.

### IntentRouterAgent

Classifies the current input using deterministic pattern matching. Current intents include:

- `payment`
- `schedule`
- `notification`
- `export`
- `document_search`
- `remote_agent`
- `analytics`
- `general_question`

For short payment or scheduling requests, it can set `pending_clarification`.

### CapabilityMatchingAgent

Compares the detected intent and input keywords against enabled capabilities in `AgentRegistry`. It returns the top capability matches with confidence and reason text.

### PlanningAgent

Turns matched capabilities into executable `PlanStep` records. Medium-risk and high-risk capabilities are marked as requiring approval.

### AuthorizationAgent

Checks `user_context.permissions` against each capability's required permissions. Low-risk capabilities are development-friendly: when no permissions are supplied, they are allowed.

### GuardrailAgent

Blocks steps when authorization fails or when a step requires human approval and its `step_id` is not present in `metadata.approved_actions`.

### ToolExecutionAgent

Executes approved plan steps through `ToolRegistry`. Each step uses the capability name as the tool name.

### ResponseGenerationAgent

Builds the final user-facing answer:

- Returns clarification or approval/permission messages when the workflow is blocked.
- Uses `LLMService.generate_with_history()` for `general_assistant` when possible.
- Converts placeholder tool results into a clear "integration not configured yet" response.

### AuditLoggingAgent

Writes a structured audit event to the application logger and marks `metadata.audit_logged = true`.

## Capability Registry

`src/services/agent_registry.py` contains the in-memory registry for routable capabilities.

Default capabilities:

```text
general_assistant        low risk
bi_analytics             low risk, requires analytics:read
document_intelligence    low risk, requires documents:read
scheduler_notification   medium risk, requires scheduler:write and notifications:send
export_report            medium risk, requires reports:export
payment                  high risk, requires payments:write
remote_agent             medium risk, requires remote_agents:invoke
```

Each capability is an `AgentCapability` model from `src/models/agent.py` with:

- Name and display metadata
- Supported intents
- Keywords
- Required permissions
- Risk level
- Optional schemas and remote endpoint
- Enabled flag

## Tool Registry

`src/tools/tool_registry.py` maps tool names to `BaseTool` instances.

`src/tools/enterprise_tools.py` builds the default registry:

- `GeneralAssistantTool`
- Placeholder tools for BI analytics, document intelligence, scheduler/notification, export, remote agent, and payment

The placeholder tools make the workflow executable before real enterprise integrations are connected. They return a stable `not_configured` response shape.

## Request Lifecycle

1. A client sends `POST /api/v1/chat` with `message`, optional `conversation_id`, optional `user_id`, and optional `user_context`.
2. `main.py` validates that the message is not empty.
3. `ConversationService` creates or loads the conversation.
4. The user message is persisted.
5. Recent history is loaded and normalized into `{"role": ..., "content": ...}` records.
6. `main.py` builds the LangGraph state with conversation data, user context, and model metadata.
7. The compiled graph runs each platform agent in order.
8. `main.py` extracts `final_response` and selected workflow metadata.
9. If graph execution fails, `main.py` calls `LLMService.generate_with_history()` directly.
10. The assistant response is persisted.
11. The API returns `status`, `response`, `conversation_id`, and metadata.

## Client Applications

### Angular UI

The Angular application lives in `frontend/`.

Important files:

- `frontend/src/app/app.component.*`: chat UI
- `frontend/src/app/chat.service.ts`: API client for `/api/v1/chat`
- `frontend/src/app/models/chat-message.ts`: UI message model
- `frontend/src/environments/environment.ts`: `apiUrl`
- `frontend/proxy.conf.json`: local proxy to `http://localhost:8000`

### Streamlit UI

The Streamlit application lives in `streamlit_ui/`.

Important files:

- `streamlit_ui/app.py`: Streamlit chat interface
- `streamlit_ui/api_client.py`: health check, chat, and conversation API calls
- `streamlit_ui/config.py`: UI configuration from environment variables

## Deployment

Deployment assets live under `deployment/`.

- `deployment/docker/Dockerfile`: multi-stage Python 3.11 FastAPI image
- `deployment/docker/docker-compose.yml`: app, PostgreSQL, Redis, and Milvus stack
- `deployment/k8s/`: Kubernetes manifests and secrets template

Note: the application settings currently read `DB_URL` and `REDIS_*` style variables. Review compose/Kubernetes environment variable names before production use so they match `config/settings.py`.

## Testing

Tests live in `tests/`.

Current test coverage focuses on:

- Pydantic message and state models
- Utility helpers and validators
- Platform agents for intent routing, capability matching, planning, and authorization

Run tests with:

```bash
pytest
```

or:

```bash
make test
```

## Extension Guide

### Add a New Capability

1. Add an `AgentCapability` entry in `default_capabilities()` or inject a custom `AgentRegistry`.
2. Add useful intents and keywords so `CapabilityMatchingAgent` can select it.
3. Choose a `risk_level` and `required_permissions`.
4. Register a matching tool with the same name in `ToolRegistry`.
5. Add or update tests for routing, planning, authorization, and execution behavior.

### Add a Real Tool Integration

1. Create a `BaseTool` subclass in `src/tools/`.
2. Implement `async execute(input_data)`.
3. Return a dictionary with at least a stable `status` and user-usable `message`.
4. Register it in `build_default_tool_registry()` or supply a custom registry to `create_main_workflow()`.

### Add a New LLM Provider

1. Add the dependency to `requirements.txt`.
2. Add a provider branch in `LLMService.generate()`.
3. Implement a provider-specific `_generate_*` method.
4. Update `.env.example` with provider-specific examples.
5. Add tests or mocks for provider selection and error handling.

## Current Limitations

- Intent routing is deterministic pattern matching, not an LLM classifier.
- Most specialized enterprise capabilities use placeholder tools until real integrations are added.
- Redis and vector store settings exist, but active caching/vector retrieval are not wired into the workflow.
- `src/agents/coordinator_agent.py` is an older coordinator scaffold; the active workflow uses `src/agents/platform_agents.py`.
- Approval is represented through `metadata.approved_actions`; there is no full human approval UI yet.

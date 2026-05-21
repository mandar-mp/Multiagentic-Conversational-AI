# Project Structure

This file maps the repository as it exists now and explains where the main design decisions live. Read it together with `docs/ARCHITECTURE.md` when learning or extending the system.

## Top-Level Layout

```text
Multiagentic Conversational AI/
|-- main.py                         # FastAPI entry point and chat API
|-- config/
|   `-- settings.py                 # Environment-driven application settings
|-- src/
|   |-- agents/                     # Platform agents and older coordinator scaffold
|   |-- db/                         # SQLAlchemy persistence layer
|   |-- models/                     # Pydantic and TypedDict schemas
|   |-- services/                   # Conversation, LLM, and capability registry services
|   |-- tools/                      # Tool abstractions, placeholders, and registry
|   |-- utils/                      # Logging, validation, and helper utilities
|   `-- workflows/                  # LangGraph workflow construction
|-- prompts/                        # Prompt templates for future or externalized agent prompts
|-- frontend/                       # Angular chat client
|-- streamlit_ui/                   # Streamlit chat client
|-- tests/                          # Unit tests
|-- docs/                           # Project documentation
|-- deployment/                     # Docker and Kubernetes deployment assets
|-- scripts/                        # Setup scripts
|-- data/                           # Runtime data directories
|-- logs/                           # Runtime logs
|-- requirements.txt                # Python dependencies
|-- Makefile                        # Common development commands
|-- pytest.ini                      # Pytest configuration
|-- .env.example                    # Environment variable template
`-- STRUCTURE.md                    # This repository map
```

Generated/runtime folders such as `__pycache__/`, `frontend/node_modules/`, `frontend/.angular/`, `.pytest_cache/`, local database files, and local logs are not part of the source architecture.

## Core Backend Files

### `main.py`

FastAPI application entry point.

Responsibilities:

- Creates the FastAPI app and CORS middleware.
- Initializes the database on startup with `init_db()`.
- Instantiates `ConversationService`, `LLMService`, and the LangGraph workflow.
- Provides:
  - `GET /`
  - `GET /health`
  - `GET /ready`
  - `POST /api/v1/chat`
  - `GET /api/v1/conversations/{conversation_id}`
- Persists user and assistant messages.
- Converts workflow results into API metadata.
- Falls back to direct LLM generation if graph execution fails.

### `config/settings.py`

Central configuration loaded from environment variables and `.env`.

Important groups:

- App and API settings
- LLM provider/model settings
- Database URL/type
- Redis and vector store placeholders
- Logging, security, timeout, and history limit settings

## Source Package

### `src/agents/`

```text
src/agents/
|-- base_agent.py
|-- coordinator_agent.py
`-- platform_agents.py
```

- `base_agent.py`: abstract base class and config model for older agent-style implementations.
- `coordinator_agent.py`: older coordinator scaffold. It is not the active graph router today.
- `platform_agents.py`: active platform workflow agents:
  - `ConversationContextAgent`
  - `IntentRouterAgent`
  - `CapabilityMatchingAgent`
  - `PlanningAgent`
  - `AuthorizationAgent`
  - `GuardrailAgent`
  - `ToolExecutionAgent`
  - `ResponseGenerationAgent`
  - `AuditLoggingAgent`

### `src/workflows/`

```text
src/workflows/
`-- main_workflow.py
```

`create_main_workflow()` builds and compiles the LangGraph workflow:

```text
conversation_context -> intent_router -> capability_matcher -> planner
-> authorization -> guardrails -> executor -> response_generator
-> audit_logger -> END
```

The workflow accepts optional `llm_service`, `agent_registry`, and `tool_registry` arguments, which makes tests and future custom deployments easier.

### `src/models/`

```text
src/models/
|-- agent.py
|-- message.py
`-- state.py
```

- `agent.py`: capability and planning schemas:
  - `AgentCapability`
  - `IntentResult`
  - `CapabilityMatch`
  - `PlanStep`
  - `AgentExecutionResult`
- `message.py`: chat persistence schemas:
  - `Message`
  - `Conversation`
- `state.py`: workflow state schemas:
  - `GraphState` for LangGraph
  - `AppState` for validation, tests, and documentation

### `src/services/`

```text
src/services/
|-- agent_registry.py
|-- conversation_service.py
`-- llm_service.py
```

- `agent_registry.py`: in-memory capability registry. Default capabilities include general assistant, BI analytics, document intelligence, scheduler/notification, export, payment, and remote agent connector.
- `conversation_service.py`: database-backed conversation and message service.
- `llm_service.py`: provider-neutral LLM facade for Gemini, OpenAI, and Anthropic.

### `src/tools/`

```text
src/tools/
|-- base_tool.py
|-- enterprise_tools.py
`-- tool_registry.py
```

- `base_tool.py`: abstract `BaseTool` contract.
- `tool_registry.py`: in-memory tool registry keyed by tool name.
- `enterprise_tools.py`: default tool registry with `GeneralAssistantTool` and conservative placeholder tools for specialized capabilities.

The current specialized tools are intentionally placeholders. They confirm routing and workflow behavior while making clear that production integrations still need to be connected.

### `src/db/`

```text
src/db/
|-- crud.py
|-- models.py
`-- session.py
```

- `session.py`: SQLAlchemy engine/session setup and table initialization.
- `models.py`: `ConversationModel` and `MessageModel`.
- `crud.py`: create/load conversations, add messages, and load recent message history.

The default database is `app.db` through `DB_URL=sqlite:///./app.db`.

### `src/utils/`

```text
src/utils/
|-- helpers.py
|-- logger.py
`-- validators.py
```

- `helpers.py`: ID generation and response formatting helpers.
- `logger.py`: logging setup.
- `validators.py`: simple input validation helpers used by tests and older scaffolding.

## Prompt Templates

```text
prompts/
|-- audit_logging_prompt.txt
|-- authorization_prompt.txt
|-- capability_matching_prompt.txt
|-- conversation_context_prompt.txt
|-- coordinator_prompt.txt
|-- guardrail_prompt.txt
|-- intent_router_prompt.txt
|-- planning_prompt.txt
|-- response_generation_prompt.txt
|-- system_prompt.txt
`-- tool_execution_prompt.txt
```

The active platform agents currently use deterministic Python logic. These prompt files document likely prompt boundaries for future LLM-backed versions of the same stages.

## Client Applications

### Angular Client: `frontend/`

```text
frontend/
|-- package.json
|-- proxy.conf.json
|-- angular.json
`-- src/
    |-- app/
    |   |-- app.component.html
    |   |-- app.component.scss
    |   |-- app.component.ts
    |   |-- chat.service.ts
    |   `-- models/chat-message.ts
    |-- environments/environment.ts
    |-- main.ts
    |-- styles.scss
    `-- index.html
```

The Angular app is a standalone chat UI. It sends messages through `ChatService` to `${environment.apiUrl}/chat`; local development proxies `/api` to the FastAPI backend on port 8000.

Useful commands from `frontend/`:

```bash
npm start
npm run build
npm test
```

### Streamlit Client: `streamlit_ui/`

```text
streamlit_ui/
|-- app.py
|-- api_client.py
|-- config.py
|-- requirements.txt
|-- Dockerfile
`-- README.md
```

The Streamlit app provides a second chat client. It supports a configurable backend URL through `CHAT_API_URL`, checks backend health, sends chat messages, and stores UI state in Streamlit session state.

## Tests

```text
tests/
|-- conftest.py
`-- unit/
    |-- test_models.py
    |-- test_platform_agents.py
    `-- test_utils.py
```

Current tests cover:

- Message, conversation, and app state models
- Utility helpers and validators
- Platform agent behavior for intent routing, capability matching, planning, and authorization

Run:

```bash
pytest
```

or:

```bash
make test
```

## Deployment

```text
deployment/
|-- docker/
|   |-- Dockerfile
|   |-- docker-compose.yml
|   `-- .dockerignore
`-- k8s/
    |-- deployment.yaml
    `-- secrets.yaml
```

- Dockerfile builds the FastAPI backend on Python 3.11.
- Docker Compose defines app, PostgreSQL, Redis, and Milvus services.
- Kubernetes files provide deployment and secrets templates.

Before using Docker Compose or Kubernetes in production, verify environment variable names against `config/settings.py`. The application currently expects `DB_URL`, not `DATABASE_URL`.

## Development Commands

Common commands are wrapped in the root `Makefile`:

```bash
make install      # pip install -r requirements.txt
make run          # uvicorn main:app --reload
make test         # pytest
make test-cov     # pytest --cov=src tests/
make lint         # flake8 and mypy
make format       # black and isort
make docker-build # build backend image
make docker-up    # start docker compose stack
make docker-down  # stop docker compose stack
```

## How the Main Pieces Fit Together

```text
main.py
  |
  | uses
  v
ConversationService ----> src/db/*
  |
  | builds state for
  v
create_main_workflow()
  |
  | uses
  +--> platform agents
  +--> AgentRegistry
  +--> ToolRegistry
  +--> LLMService
  |
  v
final_response + metadata
  |
  v
main.py stores assistant message and returns API response
```

## Where to Make Common Changes

- Add a new route: `main.py`
- Add or change workflow order: `src/workflows/main_workflow.py`
- Add a new capability: `src/services/agent_registry.py`
- Add a real integration behind a capability: `src/tools/`
- Change chat state shape: `src/models/state.py`
- Change persisted data model: `src/db/models.py` and `src/db/crud.py`
- Change LLM provider behavior: `src/services/llm_service.py`
- Change Angular UI: `frontend/src/app/`
- Change Streamlit UI: `streamlit_ui/`

## Current Design Notes

- The active architecture is capability-driven, not a collection of hard-coded domain agent branches.
- The graph is deliberately linear so governance stages like authorization, guardrails, and audit logging are always applied.
- Real enterprise tools are not connected yet for most specialized capabilities; placeholder tools preserve stable execution behavior.
- The older `CoordinatorAgent` remains in the codebase but is not used by `create_main_workflow()`.
- Redis and vector store settings are present for future work but are not currently part of request execution.

# Multi-Agentic Conversational AI Chatbot

A production-ready multi-agentic chatbot application built with LangGraph for orchestrating specialized AI agents.

## Features

- **Multi-Agent Architecture**: Specialized agents for different tasks
- **LangGraph Orchestration**: Sophisticated workflow management
- **Production Ready**: Docker, Kubernetes, and comprehensive configurations
- **Scalable**: Designed for horizontal scaling
- **Extensible**: Easy to add new agents and tools

## Project Structure

```
.
├── src/
│   ├── agents/           # Agent implementations
│   ├── models/           # Data models
│   ├── services/         # Business logic services
│   ├── tools/            # Agent tools
│   ├── utils/            # Utility functions
│   └── workflows/        # LangGraph workflows
├── config/               # Configuration files
├── prompts/              # Prompt templates
├── tests/                # Test suite
├── deployment/           # Docker & K8s configs
├── docs/                 # Documentation
└── scripts/              # Utility scripts
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized deployment)
- API keys for LLM providers (OpenAI, Anthropic, etc.)

### Installation

1. Clone the repository
```bash
git clone <repo-url>
cd "Multiagentic Conversational AI"
```

2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure environment
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

## Configuration

All configuration is managed through:
- Environment variables (`.env` file)
- `config/settings.py` for default values

Key settings:
- `ENVIRONMENT`: development, staging, production
- `LLM_PROVIDER`: openai, anthropic, etc.
- `LLM_API_KEY`: Your LLM provider API key
- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis cache connection (optional)

## Running the Application

### Development

#### Backend API

Start the FastAPI server with auto-reload:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Swagger UI: `http://localhost:8000/swagger.json`

#### Frontend UI (Angular)

From the `frontend/` directory, install dependencies and start the development server:

```bash
cd frontend
npm install
npm start
```

The Angular UI will be available at `http://localhost:4200`

#### Running Both Simultaneously

Open two separate terminals from the workspace root:

**Terminal 1 (Backend):**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm start
```

#### Alternative Frontend Startup (if `npm start` fails)

```bash
cd frontend
npx @angular/cli serve --host 0.0.0.0 --port 4200 --proxy-config proxy.conf.json
```

#### Streamlit UI (Alternative Interface)

Run the lightweight Streamlit chatbot interface:

```bash
python -m pip install -r streamlit_ui/requirements.txt
streamlit run streamlit_ui/app.py
```

The Streamlit UI will be available at `http://localhost:8501`

### Docker

```bash
docker-compose up
```

### Kubernetes

```bash
kubectl apply -f deployment/k8s/
```

## Development

### Running Tests

```bash
pytest              # Run all tests
pytest tests/unit   # Run unit tests
pytest -v          # Verbose output
pytest --cov       # With coverage
```

### Code Quality

```bash
black src/         # Format code
flake8 src/        # Lint code
mypy src/          # Type checking
```

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Architecture

### Multi-Agent System

The application uses a coordinator agent that routes requests to specialized agents:

1. **Coordinator Agent**: Routes incoming requests
2. **Specialized Agents**: Handle specific domains
3. **Tools**: External services and data access
4. **LangGraph Workflow**: Orchestrates agent interactions

### Workflow

```
User Input → Coordinator Agent → Route Decision
                                    ↓
                        Specialized Agent(s)
                                    ↓
                        Response Aggregation
                                    ↓
                            Final Response
```

## Deployment

### Production Checklist

- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=false`
- [ ] Configure production database
- [ ] Set up Redis for caching
- [ ] Configure secrets properly
- [ ] Set up monitoring and logging
- [ ] Configure CORS appropriately
- [ ] Set up rate limiting
- [ ] Configure backups

### Monitoring

- Logs: `logs/` directory
- Health checks: `/health` endpoint
- Metrics: Prometheus-compatible endpoints

## Security

- All secrets stored in environment variables
- No credentials in code
- CORS properly configured
- Rate limiting enabled
- Input validation on all endpoints

## Contributing

1. Create a feature branch
2. Make changes
3. Run tests
4. Submit pull request

## License

[Your License Here]

## Support

For issues and questions, please open an issue on the repository.

# Setup Guide

## Prerequisites

- Python 3.11 or higher
- pip or conda
- Docker & Docker Compose (for containerized deployment)
- Git
- API keys for LLM providers (OpenAI, Anthropic, etc.)

## Development Setup

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
# Add your API keys:
# - LLM_API_KEY: Your OpenAI/Anthropic key
# - VECTORSTORE_API_KEY: Your vector DB key
# - DATABASE_URL: Your database connection string
```

### 4. Database Setup

```bash
# Initialize database (if using SQLAlchemy migrations)
alembic upgrade head
```

### 5. Verify Installation

```bash
# Run tests
pytest

# Check imports
python -c "import langgraph; import langchain; print('Setup successful!')"
```

## Docker Setup

### 1. Build Docker Image

```bash
docker build -f deployment/docker/Dockerfile -t multi-agent-chatbot:latest .
```

### 2. Run with Docker Compose

```bash
# Start all services
docker-compose -f deployment/docker/docker-compose.yml up

# Run in background
docker-compose -f deployment/docker/docker-compose.yml up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### 3. Access Services

- Application: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

## Kubernetes Setup

### 1. Prerequisites

- Kubernetes cluster running (minikube, EKS, GKE, etc.)
- kubectl configured
- Docker image pushed to registry

### 2. Configure Secrets

```bash
# Create secrets from environment variables
kubectl create secret generic app-secrets \
  --from-literal=database-url='postgresql://user:pass@db:5432/chatbot' \
  --from-literal=llm-api-key='your-api-key' \
  --from-literal=vectorstore-api-key='your-key'
```

### 3. Deploy Application

```bash
# Apply K8s manifests
kubectl apply -f deployment/k8s/

# Verify deployment
kubectl get deployments
kubectl get pods
kubectl get svc

# Check logs
kubectl logs -f deployment/multi-agent-chatbot
```

### 4. Access Application

```bash
# Port forward to local machine
kubectl port-forward service/multi-agent-chatbot-service 8000:80

# Access at http://localhost:8000
```

## Production Deployment Checklist

### Pre-Deployment

- [ ] Update `.env` for production environment
- [ ] Set `ENVIRONMENT=production` and `DEBUG=false`
- [ ] Configure production database
- [ ] Set up Redis/cache
- [ ] Configure all API keys securely
- [ ] Review security settings
- [ ] Set up monitoring and logging
- [ ] Configure backups
- [ ] Plan rollback strategy

### Deployment

- [ ] Build and test Docker image
- [ ] Push image to registry
- [ ] Apply Kubernetes manifests
- [ ] Verify health checks
- [ ] Monitor initial startup
- [ ] Run smoke tests
- [ ] Enable auto-scaling if needed

### Post-Deployment

- [ ] Monitor application logs
- [ ] Check performance metrics
- [ ] Verify database connectivity
- [ ] Test all critical paths
- [ ] Monitor error rates
- [ ] Review security logs

## Troubleshooting

### Common Issues

#### 1. Import Errors

```bash
# Ensure virtual environment is activated
which python  # Should show venv path

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### 2. Database Connection Errors

```bash
# Check database is running
# For Docker: docker ps | grep postgres

# Verify connection string in .env
# Test connection
python -c "from sqlalchemy import create_engine; engine = create_engine('YOUR_DB_URL'); engine.connect()"
```

#### 3. LLM API Errors

```bash
# Verify API key is set
echo $LLM_API_KEY

# Test API connection
python -c "import openai; openai.api_key = 'YOUR_KEY'; print('API connection OK')"
```

#### 4. Docker Issues

```bash
# Clean up and rebuild
docker-compose down -v
docker system prune -a
docker-compose up --build
```

## Development Workflow

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_models.py

# With coverage
pytest --cov=src tests/

# Specific test
pytest tests/unit/test_models.py::TestMessage::test_message_creation -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Sort imports
isort src/ tests/
```

### Running Locally

```bash
# With uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Access API documentation
# Visit http://localhost:8000/docs
```

## Environment Variables Reference

See `.env.example` for all available configuration options.

Key variables:
- `ENVIRONMENT`: development, staging, production
- `DEBUG`: Enable/disable debug mode
- `LLM_PROVIDER`: openai, anthropic, etc.
- `LLM_API_KEY`: LLM provider API key
- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis connection string
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR

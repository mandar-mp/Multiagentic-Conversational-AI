.PHONY: help install test lint format run docker-build docker-up docker-down k8s-deploy clean

help:
	@echo "Available commands:"
	@echo "  make install        - Install dependencies"
	@echo "  make test          - Run tests"
	@echo "  make test-cov      - Run tests with coverage"
	@echo "  make lint          - Lint code"
	@echo "  make format        - Format code"
	@echo "  make run           - Run development server"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-up     - Start Docker containers"
	@echo "  make docker-down   - Stop Docker containers"
	@echo "  make k8s-deploy    - Deploy to Kubernetes"
	@echo "  make clean         - Clean up generated files"

install:
	pip install -r requirements.txt

test:
	pytest

test-cov:
	pytest --cov=src tests/

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

run:
	uvicorn main:app --reload

docker-build:
	docker build -f deployment/docker/Dockerfile -t multi-agent-chatbot:latest .

docker-up:
	docker-compose -f deployment/docker/docker-compose.yml up

docker-down:
	docker-compose -f deployment/docker/docker-compose.yml down

k8s-deploy:
	kubectl apply -f deployment/k8s/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov dist build *.egg-info
	rm -rf .mypy_cache .venv venv ENV env

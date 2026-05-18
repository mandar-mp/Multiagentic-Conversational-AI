#!/bin/bash

# Setup script for development environment
set -e

echo "🚀 Setting up Multi-Agentic Chatbot Development Environment..."

# Check Python version
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Copy environment template if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Copying .env template..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration!"
fi

# Run tests
echo "🧪 Running tests..."
pytest --co -q

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your API keys and configuration"
echo "2. Run 'pytest' to verify installation"
echo "3. Run 'python main.py' or 'uvicorn main:app --reload' to start the application"

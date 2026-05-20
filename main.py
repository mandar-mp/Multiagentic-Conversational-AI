"""
Main application entry point
Multi-Agentic Conversational AI Chatbot using LangGraph
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config.settings import settings
from src.db.session import init_db
from src.models.message import Message
from src.services.conversation_service import ConversationService
from src.services.llm_service import LLMService
from src.utils.logger import setup_logger

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
    conversation_id: str = None


class ChatResponse(BaseModel):
    """Chat response model"""
    status: str
    response: str
    conversation_id: str
    metadata: dict = {}


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

    response_text = await llm_service.generate_with_history(
        history_payload,
        provider=settings.llm_provider,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
    )

    assistant_message = Message(role="assistant", content=response_text)
    conversation_service.add_message(conversation_id, assistant_message)

    return ChatResponse(
        status="success",
        response=response_text,
        conversation_id=conversation_id,
        metadata={"provider": settings.llm_provider, "model": settings.llm_model},
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

"""
Main application entry point
Multi-Agentic Conversational AI Chatbot using LangGraph
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config.settings import settings
from src.utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)

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
    try:
        logger.info(f"Processing chat request: {request.message[:100]}")
        
        # TODO: Implement core chat logic
        # 1. Validate input
        # 2. Get/create conversation
        # 3. Process through workflow
        # 4. Return response
        
        return ChatResponse(
            status="success",
            response="Chat processing not yet implemented",
            conversation_id=request.conversation_id or "new",
            metadata={}
        )
    
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Retrieve conversation history
    """
    try:
        logger.info(f"Retrieving conversation: {conversation_id}")
        
        # TODO: Implement conversation retrieval
        return {
            "conversation_id": conversation_id,
            "messages": []
        }
    
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

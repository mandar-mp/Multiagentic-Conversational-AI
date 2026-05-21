"""
Application settings and configuration
Supports environment-based configuration
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # App Configuration
    app_name: str = Field(default="Multi-Agentic Chatbot", env="APP_NAME")
    app_version: str = Field(default="0.1.0", env="APP_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    
    # LLM Configuration
    # Supported providers: openai, anthropic, gemini
    llm_provider: str = Field(default="openai", env="LLM_PROVIDER")
    llm_model: str = Field(default="gpt-4", env="LLM_MODEL")
    llm_api_key: Optional[str] = Field(default=None, env="LLM_API_KEY")
    llm_temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2048, env="LLM_MAX_TOKENS")
    llm_timeout: int = Field(default=30, env="LLM_TIMEOUT")
    
    # Database Configuration
    db_type: str = Field(default="sqlite", env="DB_TYPE")
    db_url: Optional[str] = Field(default="sqlite:///./app.db", env="DB_URL")

    # Analytics Database Configuration
    analytics_db_url: Optional[str] = Field(default=None, env="ANALYTICS_DB_URL")
    analytics_db_dialect: Optional[str] = Field(default=None, env="ANALYTICS_DB_DIALECT")
    analytics_allowed_tables: list = Field(default_factory=list, env="ANALYTICS_ALLOWED_TABLES")
    analytics_blocked_tables: list = Field(default_factory=list, env="ANALYTICS_BLOCKED_TABLES")
    analytics_max_rows: int = Field(default=200, env="ANALYTICS_MAX_ROWS")
    analytics_query_timeout: int = Field(default=30, env="ANALYTICS_QUERY_TIMEOUT")
    analytics_enable_sql_echo: bool = Field(default=False, env="ANALYTICS_ENABLE_SQL_ECHO")
    
    # Redis Configuration
    redis_enabled: bool = Field(default=False, env="REDIS_ENABLED")
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Vector Store Configuration
    vectorstore_type: str = Field(default="pinecone", env="VECTORSTORE_TYPE")
    vectorstore_api_key: Optional[str] = Field(default=None, env="VECTORSTORE_API_KEY")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_dir: str = Field(default="logs", env="LOG_DIR")
    
    # Security
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    cors_origins: list = Field(default=["*"], env="CORS_ORIGINS")
    
    # Timeouts and Limits
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")
    max_conversation_history: int = Field(default=50, env="MAX_CONVERSATION_HISTORY")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment.lower() == "development"


# Global settings instance
settings = Settings()

"""
Base agent class for all specialized agents
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class AgentConfig(BaseModel):
    """Configuration for an agent"""
    name: str
    description: str
    model: str = "gpt-4"
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=2048, ge=1)
    system_prompt: Optional[str] = None
    tools: List[str] = Field(default_factory=list)


class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, config: AgentConfig):
        """Initialize agent with configuration"""
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{config.name}")
        
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input and return output
        
        Args:
            input_data: Input dictionary containing query and context
            
        Returns:
            Output dictionary with response
        """
        pass
    
    def get_config(self) -> AgentConfig:
        """Get agent configuration"""
        return self.config
    
    def set_tools(self, tools: List[str]) -> None:
        """Set available tools for the agent"""
        self.config.tools = tools

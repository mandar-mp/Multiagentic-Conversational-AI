"""
Base tool class for agent tools
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """Base class for all agent tools"""
    
    def __init__(self, name: str, description: str):
        """
        Initialize tool
        
        Args:
            name: Tool name
            description: Tool description
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool
        
        Args:
            input_data: Input data for tool execution
            
        Returns:
            Tool execution result
        """
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"

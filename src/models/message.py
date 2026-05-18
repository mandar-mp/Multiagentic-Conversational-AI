"""
Message and conversation data models
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Single message in a conversation"""
    
    role: str = Field(..., description="Role: user, assistant, system")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_name: Optional[str] = Field(default=None, description="Which agent generated this")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True


class Conversation(BaseModel):
    """Conversation thread containing multiple messages"""
    
    conversation_id: str = Field(..., description="Unique conversation ID")
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True
    
    def add_message(self, message: Message) -> None:
        """Add a message to conversation"""
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
    
    def get_last_n_messages(self, n: int) -> List[Message]:
        """Get last n messages from conversation"""
        return self.messages[-n:] if len(self.messages) >= n else self.messages

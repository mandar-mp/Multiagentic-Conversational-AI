"""
Conversation management service
"""

from typing import List, Optional
import logging
from src.models.message import Message, Conversation
from src.utils.helpers import generate_id

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversations"""
    
    def __init__(self):
        """Initialize conversation service"""
        self.conversations = {}
    
    def create_conversation(self, metadata: dict = None) -> Conversation:
        """Create a new conversation"""
        conversation_id = generate_id()
        conversation = Conversation(
            conversation_id=conversation_id,
            metadata=metadata or {}
        )
        self.conversations[conversation_id] = conversation
        logger.info(f"Created conversation: {conversation_id}")
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        return self.conversations.get(conversation_id)
    
    def add_message(self, conversation_id: str, message: Message) -> bool:
        """Add message to conversation"""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")
            return False
        
        conversation.add_message(message)
        return True
    
    def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Message]:
        """Get conversation history"""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return []
        
        return conversation.get_last_n_messages(limit)

"""
Conversation management service backed by a relational database.
"""

from typing import List, Optional
import logging

from src.db.crud import (
    add_message as db_add_message,
    create_conversation as db_create_conversation,
    get_conversation_by_id,
    get_messages_for_conversation,
)
from src.db.session import SessionLocal
from src.models.message import Conversation, Message

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversations"""

    def __init__(self):
        """Initialize conversation service with database session factory."""
        self.session_factory = SessionLocal

    def create_conversation(self, metadata: dict = None) -> Conversation:
        """Create a new conversation record in the database."""
        db = self.session_factory()
        try:
            conversation_record = db_create_conversation(db, metadata)
            return self._build_conversation_schema(conversation_record)
        finally:
            db.close()

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Retrieve a conversation and its stored metadata."""
        db = self.session_factory()
        try:
            record = get_conversation_by_id(db, conversation_id)
            if not record:
                return None
            return self._build_conversation_schema(record)
        finally:
            db.close()

    def add_message(self, conversation_id: str, message: Message) -> bool:
        """Add a message to an existing conversation."""
        db = self.session_factory()
        try:
            result = db_add_message(db, conversation_id, message)
            if result is None:
                logger.warning(f"Conversation not found: {conversation_id}")
                return False
            return True
        finally:
            db.close()

    def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Message]:
        """Return the recent message history for a conversation."""
        db = self.session_factory()
        try:
            records = get_messages_for_conversation(db, conversation_id, limit)
            return [self._build_message_schema(record) for record in records]
        finally:
            db.close()

    @staticmethod
    def _build_conversation_schema(conversation_record) -> Conversation:
        """Convert a ConversationModel into a Pydantic Conversation."""
        messages = [
            ConversationService._build_message_schema(message)
            for message in getattr(conversation_record, "messages", [])
        ]
        return Conversation(
            conversation_id=conversation_record.conversation_id,
            created_at=conversation_record.created_at,
            updated_at=conversation_record.updated_at,
            metadata=conversation_record.conversation_metadata or {},
            messages=messages,
        )

    @staticmethod
    def _build_message_schema(message_record) -> Message:
        """Convert a MessageModel into a Pydantic Message."""
        return Message(
            role=message_record.role,
            content=message_record.content,
            timestamp=message_record.created_at,
            agent_name=message_record.agent_name,
            metadata=message_record.message_metadata or {},
        )

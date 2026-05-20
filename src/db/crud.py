"""CRUD helpers for database persistence."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from src.db.models import ConversationModel, MessageModel
from src.models.message import Message
from src.utils.helpers import generate_id


def create_conversation(db: Session, metadata: Optional[dict] = None) -> ConversationModel:
    """Create and persist a new conversation."""
    conversation = ConversationModel(
        conversation_id=generate_id(),
        conversation_metadata=metadata or {},
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_conversation_by_id(db: Session, conversation_id: str) -> Optional[ConversationModel]:
    """Load a conversation by its conversation_id."""
    return db.query(ConversationModel).filter_by(conversation_id=conversation_id).first()


def add_message(db: Session, conversation_id: str, message: Message) -> Optional[MessageModel]:
    """Create and persist a new message for an existing conversation."""
    conversation = get_conversation_by_id(db, conversation_id)
    if not conversation:
        return None

    message_model = MessageModel(
        conversation_id=conversation.conversation_id,
        role=message.role,
        content=message.content,
        agent_name=message.agent_name,
        message_metadata=message.metadata or {},
    )
    db.add(message_model)
    conversation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(message_model)
    return message_model


def get_messages_for_conversation(db: Session, conversation_id: str, limit: int = 10) -> List[MessageModel]:
    """Return the most recent messages for a conversation."""
    return (
        db.query(MessageModel)
        .filter_by(conversation_id=conversation_id)
        .order_by(MessageModel.created_at.asc())
        .limit(limit)
        .all()
    )

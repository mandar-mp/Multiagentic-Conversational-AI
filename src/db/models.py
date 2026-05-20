"""SQLAlchemy models for persistent data storage."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class ConversationModel(Base):
    """Database table for stored conversations."""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    conversation_metadata = Column("metadata", JSON, nullable=False, default=dict)

    messages = relationship(
        "MessageModel",
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="MessageModel.created_at",
    )


class MessageModel(Base):
    """Database table for stored conversation messages."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        String(64),
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(32), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    agent_name = Column(String(128), nullable=True)
    message_metadata = Column("metadata", JSON, nullable=False, default=dict)

    conversation = relationship("ConversationModel", back_populates="messages")

"""
Unit tests for data models
"""

import pytest
from datetime import datetime
from src.models.message import Message, Conversation
from src.models.state import AppState


class TestMessage:
    """Test Message model"""
    
    def test_message_creation(self):
        """Test creating a message"""
        message = Message(role="user", content="Hello")
        assert message.role == "user"
        assert message.content == "Hello"
        assert isinstance(message.timestamp, datetime)
    
    def test_message_with_agent(self):
        """Test message with agent name"""
        message = Message(
            role="assistant",
            content="Hi there",
            agent_name="coordinator"
        )
        assert message.agent_name == "coordinator"


class TestConversation:
    """Test Conversation model"""
    
    def test_conversation_creation(self):
        """Test creating a conversation"""
        conv = Conversation(conversation_id="test-123")
        assert conv.conversation_id == "test-123"
        assert len(conv.messages) == 0
    
    def test_add_message(self):
        """Test adding message to conversation"""
        conv = Conversation(conversation_id="test-123")
        msg = Message(role="user", content="Hello")
        conv.add_message(msg)
        assert len(conv.messages) == 1
        assert conv.messages[0].content == "Hello"


class TestAppState:
    """Test AppState model"""
    
    def test_app_state_creation(self):
        """Test creating app state"""
        state = AppState(
            conversation_id="conv-123",
            current_input="Hello"
        )
        assert state.conversation_id == "conv-123"
        assert state.current_input == "Hello"

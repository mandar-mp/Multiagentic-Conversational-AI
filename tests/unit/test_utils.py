"""
Unit tests for utilities
"""

import pytest
from src.utils.validators import validate_input
from src.utils.helpers import generate_id, format_response


class TestValidators:
    """Test validation utilities"""
    
    def test_validate_input_valid(self):
        """Test valid input"""
        assert validate_input({"query": "Hello"}) is True
    
    def test_validate_input_missing_query(self):
        """Test invalid input - missing query"""
        assert validate_input({"data": "test"}) is False
    
    def test_validate_input_empty_query(self):
        """Test invalid input - empty query"""
        assert validate_input({"query": ""}) is False


class TestHelpers:
    """Test helper functions"""
    
    def test_generate_id(self):
        """Test ID generation"""
        id1 = generate_id()
        id2 = generate_id()
        assert id1 != id2
        assert len(id1) > 0
    
    def test_format_response(self):
        """Test response formatting"""
        response = format_response("success", {"data": "test"})
        assert response["status"] == "success"
        assert response["data"] == {"data": "test"}
        assert "timestamp" in response

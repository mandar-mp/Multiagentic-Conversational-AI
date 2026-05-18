"""
Input validation utilities
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def validate_input(input_data: Dict[str, Any]) -> bool:
    """
    Validate input data structure
    
    Args:
        input_data: Input data to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        if not isinstance(input_data, dict):
            return False
        
        required_fields = ["query"]
        for field in required_fields:
            if field not in input_data:
                logger.warning(f"Missing required field: {field}")
                return False
        
        if not isinstance(input_data.get("query"), str) or not input_data["query"].strip():
            logger.warning("Query must be non-empty string")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return False

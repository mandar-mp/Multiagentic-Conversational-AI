"""
Helper utility functions
"""

from datetime import datetime
import uuid


def get_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.utcnow().isoformat()


def generate_id() -> str:
    """Generate unique ID"""
    return str(uuid.uuid4())


def format_response(status: str, data: dict = None, message: str = None) -> dict:
    """
    Format standard response structure
    
    Args:
        status: Response status (success, error, etc)
        data: Response data
        message: Response message
        
    Returns:
        Formatted response dictionary
    """
    return {
        "status": status,
        "timestamp": get_timestamp(),
        "data": data or {},
        "message": message
    }

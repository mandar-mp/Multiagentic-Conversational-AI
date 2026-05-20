import os
from typing import Optional
import httpx
import logging

# Configure logging for debugging API calls
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

DEFAULT_API_URL = "http://localhost:8000/api/v1"


def get_api_url(api_url: Optional[str] = None) -> str:
    """Resolve the chat backend API URL from environment or override value."""
    if api_url and api_url.strip():
        return api_url.strip().rstrip("/")

    return os.getenv("CHAT_API_URL", DEFAULT_API_URL).rstrip("/")


def check_backend_health(api_url: Optional[str] = None) -> tuple[bool, str]:
    """Check if the backend API is accessible."""
    base_url = get_api_url(api_url)
    health_url = base_url.replace("/api/v1", "") + "/health"
    
    try:
        logger.debug(f"Checking backend health at {health_url}")
        with httpx.Client(timeout=5.0) as client:
            response = client.get(health_url)
            if response.status_code == 200:
                return True, "Backend is healthy"
            else:
                return False, f"Backend returned status {response.status_code}"
    except Exception as exc:
        return False, f"Backend unreachable: {exc}"


def send_chat_message(message: str, conversation_id: Optional[str] = None, api_url: Optional[str] = None) -> dict:
    """Send a user message to the backend chat API and return the parsed response."""
    url = f"{get_api_url(api_url)}/chat"
    payload = {"message": message}

    if conversation_id:
        payload["conversation_id"] = conversation_id

    try:
        logger.debug(f"Sending request to {url} with payload: {payload}")
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload)
            logger.debug(f"Response status: {response.status_code}")
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as exc:
        logger.error(f"HTTP request failed: {exc}")
        raise Exception(f"Connection failed: {exc}") from exc
    except httpx.HTTPStatusError as exc:
        logger.error(f"HTTP error {exc.response.status_code}: {exc.response.text}")
        raise Exception(f"Server error: {exc.response.status_code} - {exc.response.text}") from exc
    except Exception as exc:
        logger.error(f"Unexpected error: {exc}")
        raise


def get_conversation(conversation_id: str, api_url: Optional[str] = None) -> dict:
    """Fetch full conversation details for a known conversation ID."""
    url = f"{get_api_url(api_url)}/conversations/{conversation_id}"
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        logger.error(f"Failed to get conversation: {exc}")
        raise


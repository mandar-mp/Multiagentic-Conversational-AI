import os
from dataclasses import dataclass


@dataclass
class AppConfig:
    """Configuration values used by the Streamlit UI."""
    api_url: str = os.getenv("CHAT_API_URL", "http://localhost:8000/api/v1")
    app_title: str = os.getenv("CHAT_UI_TITLE", "Gemini-like Streamlit Chat")


config = AppConfig()

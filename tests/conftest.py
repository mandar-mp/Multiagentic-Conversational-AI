"""
Pytest configuration and fixtures
"""

import pytest
from typing import Generator


@pytest.fixture
def app_config():
    """Fixture for app configuration"""
    from config.settings import Settings
    return Settings(
        environment="test",
        debug=True,
        llm_api_key="test-key"
    )


@pytest.fixture
async def async_client():
    """Fixture for async HTTP client"""
    from httpx import AsyncClient
    # Add your app setup here
    async with AsyncClient() as client:
        yield client

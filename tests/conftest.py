import pytest
from httpx import AsyncClient, ASGITransport
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def test_app():
    """Fixture that returns a fresh FastAPI app instance for each test."""
    return app


@pytest.fixture
async def client(test_app):
    """Fixture that returns an AsyncClient connected to the test app."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

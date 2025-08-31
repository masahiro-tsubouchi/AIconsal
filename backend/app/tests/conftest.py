"""Pytest configuration and fixtures for Manufacturing AI Assistant tests"""
import asyncio
import pytest
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient
import tempfile
import os

from app.main import create_app
from app.core.config import get_settings
from app.services.chat_service import ChatService
from app.services.file_service import FileService
from app.services.langgraph_service import LangGraphService


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def app():
    """Create FastAPI application for testing"""
    return create_app()


@pytest.fixture
def client(app) -> TestClient:
    """Create test client for API testing"""
    return TestClient(app)


@pytest.fixture
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create async client for testing async endpoints"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def chat_service() -> ChatService:
    """Create ChatService instance for testing"""
    return ChatService()


@pytest.fixture
def file_service() -> FileService:
    """Create FileService instance for testing"""
    return FileService()


@pytest.fixture
def langgraph_service() -> LangGraphService:
    """Create LangGraphService instance for testing"""
    return LangGraphService()


@pytest.fixture
def sample_text_file():
    """Create temporary text file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("これはテスト用のサンプルテキストファイルです。\n製造業の改善活動に関する内容です。")
        temp_file_path = f.name
    
    yield temp_file_path
    
    # Cleanup
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)


@pytest.fixture
def sample_chat_request():
    """Sample chat request data"""
    return {
        "message": "製造業の改善活動について教えてください",
        "session_id": "test-session-123"
    }


@pytest.fixture
def sample_manufacturing_query():
    """Sample manufacturing query for testing"""
    return "工場の生産効率を向上させる方法を教えてください"


@pytest.fixture
def sample_python_query():
    """Sample Python query for testing"""
    return "Pythonでデータ分析する基本的な方法を教えてください"


@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response"""
    return """製造業の改善活動について説明します。

1. 現状分析
   - データ収集と分析
   - 問題点の特定

2. 改善提案
   - 具体的な施策の検討
   - 効果の見積もり

3. 実行と検証
   - 改善施策の実行
   - 効果測定と検証"""


@pytest.fixture
def test_session_id():
    """Test session ID"""
    return "test-session-12345"

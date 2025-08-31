"""
pytest設定ファイル - Docker環境統合テスト対応
"""

import pytest
import asyncio
from typing import Generator
from httpx import AsyncClient
from fastapi.testclient import TestClient
import os
import tempfile
from unittest.mock import Mock

from app.main import app
from app.core.config import Settings, get_settings


def pytest_configure(config):
    """pytest設定"""
    # Docker環境でのテスト実行フラグ
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "docker: mark test as docker environment test"
    )


@pytest.fixture(scope="session")
def event_loop():
    """セッション全体で使用するイベントループ"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """テスト用設定"""
    return Settings(
        PROJECT_NAME="Manufacturing AI Assistant Test",
        API_V1_STR="/api/v1",
        BACKEND_CORS_ORIGINS=["http://localhost:3002", "http://frontend:3000"],
        # テスト用の設定
        GEMINI_API_KEY="test-api-key",
        SECRET_KEY="test-secret-key",
        ACCESS_TOKEN_EXPIRE_MINUTES=30,
        UPLOAD_DIR="/tmp/test_uploads",
        MAX_FILE_SIZE=10 * 1024 * 1024,  # 10MB
        ALLOWED_FILE_TYPES=[".txt", ".pdf", ".docx", ".csv", ".xlsx"]
    )


@pytest.fixture
def override_get_settings(test_settings):
    """設定オーバーライド"""
    app.dependency_overrides[get_settings] = lambda: test_settings
    yield test_settings
    app.dependency_overrides.clear()


@pytest.fixture
def client(override_get_settings):
    """テストクライアント"""
    return TestClient(app)


@pytest.fixture
async def async_client(override_get_settings):
    """非同期テストクライアント"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def temp_upload_dir():
    """一時アップロードディレクトリ"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_gemini_service():
    """Gemini API サービスモック"""
    mock = Mock()
    mock.generate_response.return_value = {
        "content": "テスト用AI応答: 品質改善についてお答えします。",
        "usage": {"input_tokens": 10, "output_tokens": 20}
    }
    return mock


@pytest.fixture
def mock_langgraph_service():
    """LangGraph サービスモック"""
    mock = Mock()
    mock.process_message.return_value = {
        "content": "LangGraphテスト応答: 製造業の改善活動について説明します。",
        "session_id": "test-session",
        "processing_time": 1.23,
        "workflow_state": "completed"
    }
    return mock


@pytest.fixture
def sample_manufacturing_file():
    """製造業サンプルファイル"""
    content = """
製造業品質管理マニュアル

1. 品質方針
   - 顧客満足の向上
   - 継続的改善
   - 全員参加

2. 品質目標
   - 不良率 0.1% 以下
   - 納期遵守率 99% 以上
   - 顧客満足度 95% 以上

3. 検査工程
   - 受入検査
   - 工程内検査
   - 最終検査

4. 改善活動
   - 5S活動
   - カイゼン提案
   - QCサークル
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        f.flush()
        yield f.name
    
    # クリーンアップ
    try:
        os.unlink(f.name)
    except FileNotFoundError:
        pass


@pytest.fixture
def docker_environment_check():
    """Docker環境チェック"""
    def _check():
        # Docker環境の確認
        is_docker = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_ENV') == 'true'
        return is_docker
    return _check


# pytest起動時の設定
def pytest_runtest_setup(item):
    """テスト実行前セットアップ"""
    # Dockerマーカーのテストは Docker環境でのみ実行
    if item.get_closest_marker("docker"):
        if not (os.path.exists('/.dockerenv') or os.environ.get('DOCKER_ENV') == 'true'):
            pytest.skip("Docker環境でのみ実行可能なテスト")


# テスト結果収集
def pytest_collection_modifyitems(config, items):
    """テスト収集の修正"""
    for item in items:
        # 統合テストマーカーを自動付与
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Docker関連テストマーカーを自動付与
        if "docker" in item.nodeid:
            item.add_marker(pytest.mark.docker)

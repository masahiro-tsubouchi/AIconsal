# 🐳 システムアーキテクチャ設計書 (Docker環境)

> **プロジェクト**: Manufacturing AI Assistant  
> **バージョン**: 1.1.0  
> **作成日**: 2025-08-30  
> **更新日**: 2025-09-04  
> **技術スタック**: FastAPI + React + LangGraph + Gemini API  
> **インフラ**: Docker + Docker Compose + DevContainer

## 1. アーキテクチャ概要

### 1.1 Docker環境システム全体図
```
┌─────────────────────────────────────────────────────────────────┐
│                         Docker Host                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Docker Network                         │  │
│  │                                                           │  │
│  │  ┌─────────────────┐    ┌─────────────────┐              │  │
│  │  │  Frontend       │    │   Backend       │              │  │
│  │  │  Container      │◄──►│   Container     │              │  │
│  │  │  React:3002     │    │   FastAPI:8002  │              │  │
│  │  └─────────────────┘    └─────────────────┘              │  │
│  │           │                       │                      │  │
│  │           │              ┌─────────────────┐             │  │
│  │           │              │   LangGraph     │             │  │
│  │           │              │   (AI Engine)   │             │  │
│  │           │              └─────────────────┘             │  │
│  │           │                       │                      │  │
│  │           │              ┌─────────────────┐             │  │
│  │           └─────────────►│  Volume Mounts  │             │  │
│  │                          │  (File Storage) │             │  │
│  │                          └─────────────────┘             │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                        ┌─────────────────┐
                        │   Gemini API    │
                        │   (External)    │
                        └─────────────────┘
```

### 1.2 Docker コンテナ構成
- **フロントエンドコンテナ**: React + TypeScript (ポート: 3002)
- **バックエンドコンテナ**: FastAPI + Python 3.12 (ポート: 8002)
- **開発環境**: VSCode DevContainer + Docker Compose
- **ネットワーク**: Docker内部ネットワーク + ポートフォワーディング
- **ストレージ**: ボリュームマウント (./backend:/app, ./frontend:/app)

### 1.3 レイヤー構成
- **プレゼンテーション層**: React + TypeScript (Container)
- **API層**: FastAPI + Pydantic (Container)
- **ビジネスロジック層**: LangGraph ワークフロー (Container内)
- **外部API層**: Gemini API連携 (External)
- **データ層**: Volume Mounts + In-memory

## 2. バックエンド設計（FastAPI）

### 2.1 APIエンドポイント設計
```python
# 主要エンドポイント
POST /api/v1/chat          # チャット送信
GET  /api/v1/chat/history  # 会話履歴取得
POST /api/v1/files/upload  # ファイルアップロード
GET  /api/v1/health        # ヘルスチェック
WS   /api/v1/chat/ws/{session_id}  # WebSocket接続
```

### 2.2 データモデル設計
```python
# Pydanticモデル
class ChatMessage(BaseModel):
    id: str = Field(..., description="メッセージID")
    session_id: str = Field(..., description="セッションID")
    content: str = Field(..., description="メッセージ内容")
    role: Literal["user", "assistant"] = Field(..., description="送信者ロール")
    timestamp: datetime = Field(default_factory=datetime.now)
    
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None
    file_ids: List[str] = Field(default_factory=list)
    
class ChatResponse(BaseModel):
    message: ChatMessage
    session_id: str
    processing_time: float
```

### 2.3 ディレクトリ構造
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPIアプリケーション
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py          # 依存性注入
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── chat.py      # チャットAPI
│   │       └── files.py     # ファイルAPI
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # 設定管理
│   │   └── security.py      # セキュリティ
│   ├── models/
│   │   ├── __init__.py
│   │   ├── chat.py          # データモデル
│   │   └── files.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── agents/              # エージェント実装（V2専用）+ registry
│   │   ├── chat_service.py      # チャットロジック
│   │   ├── file_service.py      # ファイル処理
│   │   └── langgraph_service.py # LangGraph連携
│   └── tests/
│       ├── __init__.py
│       ├── test_api/
│       └── test_services/
├── requirements.txt
├── Dockerfile
└── pytest.ini
```

## 3. フロントエンド設計（React）

### 3.1 コンポーネント設計
```
src/
├── components/
│   ├── common/
│   │   ├── Layout.tsx       # レイアウト
│   │   ├── Header.tsx       # ヘッダー
│   │   └── LoadingSpinner.tsx
│   ├── chat/
│   │   ├── ChatInterface.tsx    # メインチャット画面
│   │   ├── MessageList.tsx      # メッセージ一覧
│   │   ├── MessageItem.tsx      # 個別メッセージ
│   │   ├── InputArea.tsx        # 入力エリア
│   │   └── FileUpload.tsx       # ファイルアップロード
│   └── ui/
│       ├── Button.tsx
│       ├── Input.tsx
│       └── Card.tsx
├── hooks/
│   ├── useChat.ts          # チャット状態管理
│   ├── useWebSocket.ts     # WebSocket管理
│   └── useFileUpload.ts    # ファイルアップロード
├── services/
│   ├── api.ts              # API通信
│   ├── websocket.ts        # WebSocket通信
│   └── fileService.ts      # ファイル管理
├── types/
│   ├── chat.ts             # チャット型定義
│   └── api.ts              # API型定義
└── utils/
    ├── constants.ts
    └── helpers.ts
```

### 3.2 状態管理戦略
```typescript
// React Context + useReducer パターン
interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  sessionId: string | null;
  error: string | null;
}

// カスタムフック
const useChat = () => {
  const [state, dispatch] = useReducer(chatReducer, initialState);
  
  const sendMessage = async (content: string, files?: File[]) => {
    // メッセージ送信ロジック
  };
  
  return { ...state, sendMessage };
};
```

## 4. LangGraph設計

### 4.1 ワークフローグラフ
```python
# LangGraphワークフロー設計
from langgraph.graph import StateGraph
from typing import TypedDict

class ChatState(TypedDict):
    messages: List[Dict]
    user_query: str
    context: str
    response: str
    files: List[Dict]

# ノード定義
def analyze_query(state: ChatState) -> ChatState:
    """ユーザークエリを分析"""
    pass

def process_files(state: ChatState) -> ChatState:
    """ファイル内容を処理"""
    pass

def generate_response(state: ChatState) -> ChatState:
    """レスポンス生成"""
    pass

# グラフ構築
workflow = StateGraph(ChatState)
workflow.add_node("analyze", analyze_query)
workflow.add_node("process_files", process_files)  
workflow.add_node("generate", generate_response)

# フロー定義
workflow.set_entry_point("analyze")
workflow.add_edge("analyze", "process_files")
workflow.add_edge("process_files", "generate")
```

### 4.2 エージェントI/F（V2専用）
V2 の構造化I/Oに統一されています。各エージェントは `run_v2(AgentInput) -> AgentOutput`（async）を実装し、レジストリから解決して利用します。

```python
# backend/app/services/agents/types.py（抜粋）
from pydantic import BaseModel
from typing import Optional, List, Dict

class AgentInput(BaseModel):
    session_id: str
    user_query: str
    messages: List[Dict] = []
    file_context: Optional[str] = None
    debug: bool = False

class AgentOutput(BaseModel):
    content: str
    display_header: Optional[str] = None
    selected_tool: Optional[str] = None
    decision_trace: Optional[Dict] = None

# 各エージェントは次の署名を満たします（例: manufacturing_advisor.run_v2）
# async def run_v2(inp: AgentInput) -> AgentOutput: ...
```

```python
# backend/app/services/agents/registry.py（抜粋）
_REGISTRY_V2 = {
    "general": general_responder.run_v2,
    "python": python_mentor.run_v2,
    "manufacturing": manufacturing_advisor.run_v2,
}

def get_agent_v2(name: str):
    return _REGISTRY_V2.get(name)
```

```python
# 利用例（langgraph_service から）
from backend.app.services.agents.registry import get_agent_v2
from backend.app.services.agents.types import AgentInput

agent_fn = get_agent_v2("manufacturing")
assert agent_fn is not None
result = await agent_fn(AgentInput(session_id=sid, user_query=question))
# result は AgentOutput
```

## 5. 外部API連携

### 5.1 Gemini API統合
```python
# Gemini API設定
class GeminiService:
    def __init__(self, api_key: str):
        self.client = genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    async def generate_response(
        self, 
        prompt: str, 
        context: str = None,
        files: List = None
    ) -> str:
        # プロンプト構築とレスポンス生成
        pass
```

### 5.2 ファイル処理サービス
```python
# ファイル処理サービス
class FileProcessor:
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.txt', '.csv', '.xlsx']
    
    async def process_file(self, file_path: str) -> Dict:
        # ファイル形式に応じた処理
        pass
        
    async def extract_text(self, file_content: bytes, file_type: str) -> str:
        # テキスト抽出
        pass
```

## 6. データフロー設計

### 6.1 チャットフロー
```
1. [User] メッセージ入力 → [React] 
2. [React] API送信 → [FastAPI]
3. [FastAPI] リクエスト検証 → [LangGraph]
4. [LangGraph] ワークフロー実行 → [Gemini API]
5. [Gemini API] レスポンス → [LangGraph]
6. [LangGraph] 後処理 → [FastAPI]
7. [FastAPI] レスポンス → [React]
8. [React] UI更新
```

### 6.2 ファイル処理フロー
```
1. [User] ファイル選択 → [React]
2. [React] ファイルアップロード → [FastAPI]
3. [FastAPI] ファイル保存 → [FileService]
4. [FileService] テキスト抽出 → [LangGraph]
5. [LangGraph] コンテキスト統合 → [Response]
```

## 7. セキュリティ設計

### 7.1 認証・認可
```python
# 簡易認証（Phase 1）
class SessionManager:
    def __init__(self):
        self.sessions = {}  # In-memory storage
    
    def create_session(self, user_id: str) -> str:
        session_id = str(uuid4())
        self.sessions[session_id] = {
            "user_id": user_id,
            "created_at": datetime.now(),
            "last_active": datetime.now()
        }
        return session_id
```

### 7.2 データ保護
- **ファイル一時保存**: アップロード後24時間で自動削除
- **メモリ管理**: セッション終了時の状態クリア
- **ログ管理**: 個人情報を含まない操作ログのみ記録

## 8. パフォーマンス設計

### 8.1 レスポンス時間最適化
- **非同期処理**: FastAPI async/await活用
- **ストリーミング**: WebSocketでのリアルタイム応答
- **キャッシュ**: よく使われる応答のメモリキャッシュ

### 8.2 スケーラビリティ
- **水平スケーリング**: Docker Swarmでのコンテナ複製
- **ロードバランシング**: Nginxによる負荷分散（Phase 2）

## 9. 監視・ログ設計

### 9.1 監視項目
- **API応答時間**: 95パーセンタイル 3秒以下
- **エラー率**: 5%以下
- **同時接続数**: 10セッション対応

### 9.2 ログ設計
```python
# 構造化ログ
import structlog

logger = structlog.get_logger()

# 使用例
logger.info(
    "chat_request_received",
    session_id=session_id,
    message_length=len(message),
    processing_time=elapsed_time
)
```

## 10. Docker開発環境

### 10.1 Docker Compose構成
```yaml
# docker-compose.yml の主要設定
services:
  backend:
    build: ./backend
    ports:
      - "8002:8002"
    volumes:
      - ./backend:/app
    environment:
      - PYTHONPATH=/app
      - PYTHON_ENV=development
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./frontend
    ports:
      - "3002:3002"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - REACT_APP_API_URL=http://localhost:8002/api/v1
```

### 10.2 DevContainer設定
```json
{
  "name": "Manufacturing AI Assistant Development",
  "dockerComposeFile": "../docker-compose.yml",
  "service": "backend",
  "workspaceFolder": "/app",
  "forwardPorts": [8002, 3002],
  "postCreateCommand": "pip install -e .",
  "remoteUser": "appuser"
}
```

### 10.3 Docker開発ワークフロー
1. **環境起動**: `docker compose up -d`
2. **DevContainer接続**: VSCodeでコンテナに接続
3. **テスト実行**: コンテナ内でpytest/npm test
4. **ホットリロード**: ボリュームマウントで即座反映
5. **デバッグ**: コンテナ内でブレークポイント設定

## 11. テスト戦略

### 11.1 Docker環境でのテストレベル
- **単体テスト**: 各コンテナ内でモジュール・コンポーネントテスト
- **統合テスト**: Docker内部ネットワークでのAPI・LangGraphワークフロー
- **E2Eテスト**: Docker Composeでの全体システムテスト

### 11.2 Docker TDD実装方針
```bash
# バックエンドテスト（Docker内実行）
docker compose exec backend pytest tests/ -v --cov=app

# フロントエンドテスト（Docker内実行）
docker compose exec frontend npm test

# 統合テスト（Docker Compose環境）
docker compose up -d
docker compose exec backend pytest tests/integration/ -v
```

```python
# Docker環境でのテスト例
def test_chat_endpoint_success():
    """正常なチャットリクエストのテスト"""
    # Arrange
    request_data = {"message": "こんにちは", "session_id": "test-session"}
    
    # Act - Docker内部ネットワークを使用
    response = client.post("/api/v1/chat", json=request_data)
    
    # Assert
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["session_id"] == "test-session"
```

---

**次のステップ**: プロジェクト構造作成とDocker環境構築

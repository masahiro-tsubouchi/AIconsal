# 製造業AI アシスタント (Manufacturing AI Assistant)

> **🐳 完全Docker環境での製造業向けAI Chatbot**  
> 改善活動コンサルティングとPython技術指導のためのAIアシスタント

## 📋 概要

製造業の現場で活用される専門的なAIアシスタントです。改善活動のコンサルティング、Python技術指導、ファイルベースの質問応答機能を提供します。

**🔧 Docker環境での開発・テスト・運用を前提とした設計**

### 🎯 主要機能

- **製造業特化コンサルティング**: 改善活動、品質管理、効率化に関する専門的な回答
- **Python技術指導**: コーディング、デバッグ、ベストプラクティスの指導
- **ファイルアップロード対応**: PDF、DOCX、TXT、CSV、XLSX形式のファイル解析
- **マルチターン対話**: 履歴を保持した継続的な会話
- **リアルタイム通信**: WebSocketによる高速レスポンス

### 🛠️ 技術スタック

- **バックエンド**: FastAPI (Python 3.12)
- **フロントエンド**: React + TypeScript
- **AI/ML**: LangGraph + Google Gemini API
- **インフラ**: Docker + Docker Compose
- **開発**: TDD (Test-Driven Development)

## 🔧 前提条件

**必須環境:**
- Docker Engine 20.10+
- Docker Compose V2

**開発環境（推奨）:**
- VSCode + Dev Containers拡張機能

### 🧭 コマンド規約

- Docker Compose CLI は `docker compose`（V2）を使用します。
- Compose ファイル名は `docker-compose.yml` を使用します。
- 任意指定の注記は日本語では全て `（任意）` と表記します。

## 🚀 Docker環境セットアップ

### 1. リポジトリクローン
```bash
git clone <repository-url>
cd LangGraphChatBot
```

### 2. 環境変数設定
```bash
# バックエンド環境変数
cp backend/.env.example backend/.env

# フロントエンド環境変数  
cp frontend/.env.example frontend/.env

# 必要なAPI キーを設定
# - GEMINI_API_KEY
# - LANGSMITH_API_KEY（任意）
```

### 3. Docker Compose起動
```bash
# 開発環境起動（デタッチモード）
docker compose up -d

# ログ確認
docker compose logs -f

# 停止
docker compose down
```

### 4. アクセス
- **フロントエンド**: http://localhost:3002
- **バックエンドAPI**: http://localhost:8002
- **API仕様書**: http://localhost:8002/docs

## 🔧 Docker開発環境

### VSCode DevContainer使用（推奨）
```bash
# VSCodeで開発環境起動
code .
# Ctrl+Shift+P → "Dev Containers: Reopen in Container"
```

### 手動Docker開発環境
```bash
# 開発用コンテナ起動（ホットリロード有効）
docker compose up

# バックエンドシェル接続
docker compose exec backend bash

# フロントエンドシェル接続  
docker compose exec frontend bash

# 依存関係インストール（バックエンド）
docker compose exec backend pip install <package-name>

# 依存関係インストール（フロントエンド）
docker compose exec frontend npm install <package-name>
```

## 🧪 Docker環境でのテスト実行

### バックエンドテスト
```bash
# テスト実行
docker compose exec backend pytest

# カバレッジ付きテスト
docker compose exec backend pytest --cov=app --cov-report=html

# 特定テストファイル実行
docker compose exec backend pytest tests/test_chat_service.py -v

# 単体・統合テスト分割実行
docker compose exec backend pytest -m unit
docker compose exec backend pytest -m integration
```

#### 開発中の素早いループ（カバレッジ閾値を無効化）
pytest.ini でカバレッジ閾値 `--cov-fail-under=80` を有効化しています。部分的なテスト実行や素早い開発ループでは、以下のように一時的にカバレッジ計測を無効化して失敗を避けられます。

```bash
# 全テスト（カバレッジ無効）
docker compose exec -T backend pytest -q --no-cov

# 統合テストのみ（例）
docker compose exec -T backend pytest tests/integration -v --tb=short --no-cov

# 単一テスト（例）
docker compose exec -T backend pytest tests/integration/test_api_debug.py::TestAPIDebugMode::test_chat_endpoint_returns_debug_payload_and_header -q --no-cov
```

カバレッジを確認・担保したい場合は、`--no-cov` を外して実行してください。

### フロントエンドテスト
```bash
# テスト実行
docker compose exec frontend npm test

# カバレッジ付きテスト
docker compose exec frontend npm run test:coverage

# E2Eテスト（将来実装）
docker compose exec frontend npm run test:e2e
```

#### 非対話（CI想定）でのフロントエンドテスト実行
CI 互換の一括実行コマンド（watch 無効化）:

```bash
docker compose run --rm -e CI=true frontend npm test -- --watchAll=false
```
※ 新規 UI テストでは、デバッグモード時に `[DEBUG]` ヘッダーが UI 上で強調表示されることを検証しています。

#### CI（GitHub Actions）
- `.github/workflows/ci.yml` にて Docker ベースで CI を実行します。
- バックエンド: `pytest` + カバレッジ（閾値 >= 80%）
- フロントエンド: Jest + カバレッジ
- グラフエクスポート: LangGraph の `draw_mermaid()` を利用し Mermaid/PNG を生成（Docker Mermaid CLI へフォールバック）
- すべてのCIタスクは Docker 上で完結するため、ローカル環境差分の影響を受けにくい構成です。

### 統合テスト
```bash
# 全サービス起動後の統合テスト
docker compose exec backend pytest tests/integration/ -v

# API接続テスト
curl http://localhost:8002/api/v1/health
```

## 📁 プロジェクト構造

```
LangGraphChatBot/
├── .devcontainer/             # VSCode DevContainer設定
│   └── devcontainer.json
├── backend/                   # FastAPI バックエンド
│   ├── app/
│   │   ├── api/              # API エンドポイント
│   │   ├── core/             # 設定・ユーティリティ
│   │   ├── models/           # データモデル
│   │   └── services/         # ビジネスロジック
│   ├── tests/                # テストコード
│   ├── requirements.txt      # Python依存関係
│   ├── Dockerfile           # バックエンドイメージ
│   └── .env.example         # 環境変数テンプレート
├── frontend/                 # React フロントエンド
│   ├── src/
│   │   ├── components/       # UIコンポーネント
│   │   ├── hooks/           # カスタムフック
│   │   ├── services/        # API通信
│   │   └── types/           # TypeScript型定義
│   ├── public/              # 静的ファイル
│   ├── package.json         # Node.js依存関係
│   ├── Dockerfile          # フロントエンドイメージ
│   └── .env.example        # 環境変数テンプレート
├── docs/                    # ドキュメント
├── docker-compose.yml       # Docker Compose設定
└── README.md               # このファイル
```

## 📚 ドキュメント索引
- [APIリファレンス](docs/api_reference.md)
- [Backend開発ガイド](docs/development/backend_guide.md)
- [Frontend開発ガイド](docs/development/frontend_guide.md)
- [テストガイド](docs/testing.md)
- [Debug/Traceガイド](docs/debug_trace.md)
- [グラフ資産ガイド](docs/graph_assets.md)
- [Contributing ガイド](CONTRIBUTING.md)
- [変更履歴 (CHANGELOG)](CHANGELOG.md)
- [ADR 一覧 (ADR-001)](docs/adr/ADR-001-adopt-agents-v2-and-checkpointer.md)

## 🤝 コントリビューション

### Docker環境での開発フロー
1. Issue作成・確認
2. Feature ブランチ作成
3. Docker環境で実装・テスト
4. プルリクエスト作成
5. Docker環境でのCI/CD確認
6. コードレビュー
7. マージ

### 開発環境統一
- **必須**: Docker環境での開発
- **推奨**: VSCode DevContainer使用
- **テスト**: Docker内でのテスト実行必須

## 📄 ライセンス

社内利用限定

## 📞 サポート

技術的な質問や不具合報告は、Issueまたは社内チャットでお問い合わせください。

### Docker環境リセット手順
```bash
# 完全リセット
docker compose down -v
docker system prune -a
docker compose build --no-cache
docker compose up

# ログ確認
docker compose logs | grep ERROR

# 個別サービス再起動
docker compose restart backend frontend
```

---

**🐳 Happy Docker Development! 🚀**

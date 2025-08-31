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
# - LANGSMITH_API_KEY (オプション)
```

### 3. Docker Compose起動
```bash
# 開発環境起動（デタッチモード）
docker-compose up -d

# ログ確認
docker-compose logs -f

# 停止
docker-compose down
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
docker-compose up

# バックエンドシェル接続
docker-compose exec backend bash

# フロントエンドシェル接続  
docker-compose exec frontend bash

# 依存関係インストール（バックエンド）
docker-compose exec backend pip install <package-name>

# 依存関係インストール（フロントエンド）
docker-compose exec frontend npm install <package-name>
```

## 🧪 Docker環境でのテスト実行

### バックエンドテスト
```bash
# テスト実行
docker-compose exec backend pytest

# カバレッジ付きテスト
docker-compose exec backend pytest --cov=app --cov-report=html

# 特定テストファイル実行
docker-compose exec backend pytest tests/test_chat_service.py -v

# 単体・統合テスト分割実行
docker-compose exec backend pytest -m unit
docker-compose exec backend pytest -m integration
```

### フロントエンドテスト
```bash
# テスト実行
docker-compose exec frontend npm test

# カバレッジ付きテスト
docker-compose exec frontend npm run test:coverage

# E2Eテスト（将来実装）
docker-compose exec frontend npm run test:e2e
```

### 統合テスト
```bash
# 全サービス起動後の統合テスト
docker-compose exec backend pytest tests/integration/ -v

# API接続テスト
curl http://localhost:8002/health
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

## ⚙️ Docker環境設定

### docker-compose.yml主要設定
- **バックエンドポート**: 8002
- **フロントエンドポート**: 3002
- **ボリュームマウント**: ホットリロード対応
- **ネットワーク**: プライベートネットワーク構成
- **ヘルスチェック**: 自動サービス監視

### 環境変数

#### バックエンド (.env)
```env
# AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=manufacturing-ai-assistant

# Server Configuration
HOST=0.0.0.0
PORT=8002
DEBUG=true

# File Processing
MAX_FILE_SIZE=10485760
UPLOAD_DIR=/tmp/uploads

# Session Management
SESSION_TIMEOUT=3600
```

#### フロントエンド (.env)
```env
REACT_APP_API_URL=http://localhost:8002
REACT_APP_WS_URL=ws://localhost:8002
PORT=3002
```

## 🎨 機能詳細

### 改善活動コンサルティング
- リーン生産方式
- 5S活動
- カイゼン手法
- 品質管理（QC七つ道具等）
- 生産性向上施策

### Python技術指導
- コーディング支援
- デバッグ手法
- ベストプラクティス
- ライブラリ活用法
- パフォーマンス最適化

### ファイル処理
- **対応形式**: PDF, DOCX, TXT, CSV, XLSX
- **最大サイズ**: 10MB
- **処理機能**: テキスト抽出、内容解析、文脈理解

## 📚 API仕様

### 主要エンドポイント

#### チャット
- `POST /api/v1/chat/` - メッセージ送信
- `GET /api/v1/chat/history/{session_id}` - 会話履歴取得
- `WS /api/v1/chat/ws/{session_id}` - WebSocket接続

#### ファイル
- `POST /api/v1/files/upload` - ファイルアップロード
- `GET /api/v1/files/{file_id}` - ファイル情報取得
- `DELETE /api/v1/files/{file_id}` - ファイル削除

詳細は http://localhost:8002/docs をご確認ください。

## 🧠 AI機能詳細

### LangGraphワークフロー
1. **クエリ分析** - 質問内容の分類（製造業/Python/一般）
2. **コンテキスト処理** - ファイル内容・会話履歴の統合
3. **専門応答生成** - 分野別の最適化された回答生成

### 対応ファイル形式
- PDF (.pdf) - テキスト抽出
- Word (.docx) - 文書内容抽出
- テキスト (.txt) - 直接読み込み
- CSV (.csv) - データ構造化
- Excel (.xlsx) - スプレッドシート解析

## 🔧 Docker開発ガイド

### コーディング規約

#### Python (バックエンド)
```bash
# コード整形（Docker内）
docker-compose exec backend black app/
docker-compose exec backend isort app/

# 型チェック
docker-compose exec backend mypy app/

# リント
docker-compose exec backend flake8 app/
```

#### TypeScript (フロントエンド)
```bash
# コード整形（Docker内）
docker-compose exec frontend npm run format

# リント
docker-compose exec frontend npm run lint

# 型チェック
docker-compose exec frontend npm run type-check
```

### デバッグ

#### バックエンドデバッグ
```bash
# デバッグログ確認
docker-compose logs backend -f

# コンテナ内でインタラクティブ実行
docker-compose exec backend python -i
```

#### フロントエンドデバッグ
```bash
# 開発モードブラウザデバッグ
# Chrome DevTools使用推奨

# React DevTools確認
docker-compose logs frontend
```

## 📊 Docker監視・運用

### ヘルスチェック
```bash
# サービス状態確認
docker-compose ps

# ヘルスチェック
curl http://localhost:8002/health
curl http://localhost:3002

# リソース使用量
docker stats
```

### ログ管理
```bash
# 全サービスログ
docker-compose logs -f

# 特定サービスログ
docker-compose logs -f backend
docker-compose logs -f frontend

# ログファイル出力
docker-compose logs > logs/app.log
```

### パフォーマンス最適化
```bash
# イメージサイズ最適化
docker images | grep langraph

# 不要コンテナ・イメージ削除
docker system prune -a

# キャッシュクリア
docker builder prune
```

## 🧪 テスト戦略

### テスト分類
- **単体テスト**: 各サービス内でのテスト
- **統合テスト**: サービス間連携テスト
- **E2Eテスト**: ユーザーシナリオベーステスト

### TDD + Docker開発手順
1. **テスト作成** - Docker内で期待する動作のテストを先に書く
2. **実装** - テストが通る最小限のコード実装
3. **リファクタリング** - AIによるコード改善提案

## 🐛 Docker環境トラブルシューティング

### よくある問題

#### 1. Gemini API エラー
```bash
# APIキーの確認
docker-compose exec backend env | grep GEMINI_API_KEY
```

#### 2. Docker ビルドエラー
```bash
# 完全リセット
docker-compose down -v
docker system prune -a
docker-compose build --no-cache
docker-compose up
```

#### 3. ポート競合エラー
```bash
# ポート使用状況確認
lsof -i :8002
lsof -i :3002

# コンテナ停止
docker-compose down
```

#### 4. ボリュームマウントエラー
```bash
# ボリューム再作成
docker-compose down -v
docker volume prune
docker-compose up
```

## 📊 非機能要件

- **同時接続**: 10ユーザー
- **レスポンス時間**: 2秒以内（Docker環境）
- **可用性**: 99.9%
- **セキュリティ**: 社内ネットワーク限定

## 🔮 将来の拡張

- **Kubernetes対応**: 本番スケール環境への移行
- **マイクロサービス化**: サービス分離・独立デプロイ
- **マルチエージェント**: 専門分野別のエージェント追加
- **RAG機能**: 社内文書データベースとの連携
- **監視・アラート**: Prometheus + Grafana統合

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
docker-compose down -v
docker system prune -a
docker-compose build --no-cache
docker-compose up

# ログ確認
docker-compose logs | grep ERROR

# 個別サービス再起動
docker-compose restart backend frontend
```

---

**🐳 Happy Docker Development! 🚀**

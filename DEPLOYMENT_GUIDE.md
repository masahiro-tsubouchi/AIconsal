# 製造業AI Chatbot デプロイメントガイド

> **バージョン**: 1.0.0  
> **最終更新**: 2025-08-30  
> **対象環境**: Docker + Gemini API

## 概要

製造業向けAI Chatbotの本番環境デプロイメント手順書です。

### システム構成
- **バックエンド**: FastAPI + Python 3.12 + LangGraph
- **フロントエンド**: React 18 + TypeScript + Tailwind CSS
- **AI**: Google Gemini API
- **インフラ**: Docker Compose

## 事前準備

### 1. 必要なAPI キー取得
```bash
# Gemini API キー取得
# https://ai.google.dev/ でAPIキーを生成
GEMINI_API_KEY=your_actual_api_key_here
```

### 2. システム要件
- **Docker**: 20.10.0+
- **Docker Compose**: 2.0.0+
- **CPU**: 2コア以上推奨
- **メモリ**: 4GB以上推奨
- **ディスク**: 10GB以上の空き容量

## 本番デプロイ手順

### ステップ1: プロジェクトクローン
```bash
git clone https://github.com/your-org/LangGraphChatBot.git
cd LangGraphChatBot
```

### ステップ2: 環境変数設定
```bash
# バックエンド環境変数
cp backend/.env.example backend/.env
vim backend/.env

# 必須設定項目
GEMINI_API_KEY=your_actual_gemini_api_key
DEBUG=false
RELOAD=false
ENVIRONMENT=production
```

### ステップ3: Docker環境起動
```bash
# 本番モード起動（compose 単体でOK。必要に応じて .env や override で設定を切替）
docker compose up -d

# ログ確認
docker compose logs -f
```

### ステップ4: ヘルスチェック
```bash
# バックエンドAPI確認
curl http://localhost:8002/api/v1/health

# フロントエンド確認
curl http://localhost:3002/

# AI機能テスト
curl -X POST http://localhost:8002/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "テスト", "session_id": "health-check"}'
```

## セキュリティ設定

### 1. 環境変数セキュリティ
```bash
# 本番環境での推奨設定
SECRET_KEY=$(openssl rand -base64 32)
CORS_ORIGINS="https://your-domain.com"
```

### 2. ファイアウォール設定
```bash
# 必要ポートのみ開放
# 8002: バックエンドAPI
# 3002: フロントエンド
```

### 3. HTTPS設定
```nginx
# nginx.conf例
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    location /api/ {
        proxy_pass http://localhost:8002;
    }
    
    location / {
        proxy_pass http://localhost:3002;
    }
}
```

## 監視・運用

### 1. ログ監視
```bash
# アプリケーションログ
docker compose logs backend --tail=100 -f

# エラーログ確認
docker compose logs backend | grep ERROR
```

### 2. パフォーマンス監視
```bash
# コンテナリソース使用量
docker compose stats

# ディスク使用量
docker system df
```

### 3. バックアップ
```bash
# データベース/ログバックアップ（必要に応じて）
docker compose exec backend python -m app.scripts.backup
```

## トラブルシューティング

### よくある問題と解決策

#### 1. Gemini API エラー
```bash
# API キー確認
docker compose exec backend env | grep GEMINI

# クォータ確認
# https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas
```

#### 2. メモリ不足
```bash
# メモリ使用量確認
docker compose exec backend python -c "
import psutil
print(f'Memory: {psutil.virtual_memory().percent}%')
"

# コンテナ再起動
docker compose restart backend
```

#### 3. ファイルアップロードエラー
```bash
# アップロードディレクトリ権限確認
docker compose exec backend ls -la /tmp/uploads/

# 権限修正
docker compose exec backend chmod 755 /tmp/uploads/
```

## スケーリング

### 1. 水平スケーリング
```yaml
# docker-compose.scale.yml
services:
  backend:
    deploy:
      replicas: 3
```

### 2. リソース制限
```yaml
# リソース制限設定
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
```

## アップデート手順

### 1. ゼロダウンタイムアップデート
```bash
# 新バージョンビルド
docker compose build --no-cache

# ローリングアップデート
docker compose up -d --force-recreate
```

### 2. ロールバック
```bash
# 前バージョンに戻す
docker compose down
git checkout previous-version
docker compose up -d
```

## サポート

### 連絡先
- **技術サポート**: your-tech-support@company.com
- **緊急対応**: your-emergency@company.com

### ドキュメント
- **API仕様書**: http://localhost:8002/docs
- **アーキテクチャ**: architecture_design.md
- **要件仕様**: requirements_specification.md

---

**注意**: 本番環境では必ずHTTPSを使用し、適切なセキュリティ設定を行ってください。

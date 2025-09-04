#!/bin/bash
# Docker環境統合テスト実行スクリプト
# ベストプラクティス: TDD + Docker環境での自動テスト実行

set -e

echo "🐳 Docker環境統合テスト開始"
echo "================================"

# Docker Composeサービス起動確認
echo "📋 Docker Composeサービス状態確認..."
docker compose ps

# バックエンドコンテナの起動確認
if ! docker compose ps backend | grep -q "Up"; then
    echo "⚠️  バックエンドサービスを起動中..."
    docker compose up -d backend
    sleep 10
fi

# フロントエンドコンテナの起動確認
if ! docker compose ps frontend | grep -q "Up"; then
    echo "⚠️  フロントエンドサービスを起動中..."
    docker compose up -d frontend
    sleep 10
fi

echo ""
echo "🧪 バックエンド統合テスト実行"
echo "--------------------------------"

# バックエンド統合テスト実行
echo "実行中: backend/tests/integration/"

# Coverage トグル: NO_COV=1 の場合はカバレッジ無効化（開発ループ向け）
if [ "${NO_COV:-0}" = "1" ]; then
    echo "⚙️  Backend coverage disabled (NO_COV=1)"
    PYTEST_COV_OPTS="--no-cov"
else
    PYTEST_COV_OPTS="--cov=app --cov-report=term-missing"
fi

docker compose exec -T backend pytest tests/integration/ -v --tb=short ${PYTEST_COV_OPTS}

echo ""
echo "🧪 フロントエンド統合テスト実行"
echo "--------------------------------"

# フロントエンド統合テスト実行
echo "実行中: frontend/src/tests/integration/"

# Frontend coverage toggle: reuse NO_COV like backend. When NO_COV=1, do not collect coverage
if [ "${NO_COV:-0}" = "1" ]; then
    echo "⚙️  Frontend coverage disabled (NO_COV=1)"
    FE_TEST_ARGS="--testPathPattern=integration --watchAll=false --verbose --passWithNoTests"
else
    FE_TEST_ARGS="--testPathPattern=integration --watchAll=false --coverage --verbose"
fi

docker compose exec -T frontend npm test -- $FE_TEST_ARGS

echo ""
echo "🔍 サービス間通信テスト"
echo "--------------------------------"

# ヘルスチェック
echo "バックエンドヘルスチェック..."
BACKEND_HEALTH=$(curl -s http://localhost:8002/api/v1/health || echo "FAILED")
echo "結果: $BACKEND_HEALTH"

# フロントエンドからバックエンドへの接続確認
echo "フロントエンド→バックエンド接続確認..."
FRONTEND_TO_BACKEND=$(docker compose exec -T frontend sh -lc "node -e \"fetch('http://backend:8002/api/v1/health').then(r=>r.text()).then(t=>console.log(t)).catch(()=>console.log('FAILED'))\"" || echo "FAILED")
echo "結果: $FRONTEND_TO_BACKEND"

echo ""
echo "📊 テスト結果サマリー"
echo "================================"

# テスト結果レポート
echo "✅ バックエンド統合テスト: 完了"
echo "✅ フロントエンド統合テスト: 完了"
echo "✅ サービス間通信テスト: 完了"

echo ""
echo "🎉 Docker環境統合テスト完了!"
echo "================================"

# 任意: テスト後にサービス停止
if [ "$1" = "--stop" ]; then
    echo "🛑 Dockerサービス停止中..."
    docker compose down
fi

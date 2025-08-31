#!/bin/bash

# 🐳 Manufacturing AI Assistant - DevContainer Post-Creation Script
# Docker環境での開発用初期化スクリプト

set -e

echo "🚀 Starting Manufacturing AI Assistant DevContainer setup..."

# 🐍 Python環境セットアップ
echo "📦 Installing Python dependencies..."
cd /app
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# 開発用追加パッケージ
pip install -e .

# ⚛️ Frontend依存関係チェック
echo "📦 Checking Frontend dependencies..."
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
    cd frontend
    if [ ! -d "node_modules" ]; then
        echo "Installing Node.js dependencies..."
        npm install
    fi
    cd /app
fi

# 🧪 テスト環境セットアップ
echo "🧪 Setting up test environment..."
if [ ! -d "logs" ]; then
    mkdir -p logs
fi

# 📁 必要なディレクトリ作成
echo "📁 Creating necessary directories..."
mkdir -p /tmp/uploads
mkdir -p coverage

# 🔧 権限設定
echo "🔧 Setting up permissions..."
chown -R appuser:appuser /app
chmod +x .devcontainer/post-create.sh

# ✅ セットアップ完了
echo "✅ DevContainer setup completed!"
echo "🐳 Docker environment ready for development"
echo ""
echo "🚀 Quick start commands:"
echo "  - Backend tests: docker-compose exec backend pytest"
echo "  - Frontend tests: docker-compose exec frontend npm test" 
echo "  - Full stack: docker-compose up"
echo ""
echo "📚 Documentation: http://localhost:8002/docs"
echo "⚛️ Frontend: http://localhost:3002"
echo ""
echo "Happy coding! 🎉"

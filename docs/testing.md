# テストガイド (Docker専用)

> バージョン: 1.0.0  
> 最終更新: 2025-09-05  
> 対象: 開発者 / QA

## 方針
- すべてのテストは Docker コンテナ内で実行します。
- カバレッジ閾値はバックエンドで 80%（`backend/pytest.ini`）。
- フロントエンドは非対話実行（watchAll=false）を基本とします。

## 前提
```bash
# サービス起動
docker compose up -d backend frontend

# 状態確認
docker compose ps
```

## バックエンドテスト（pytest）
```bash
# 通常（カバレッジ計測あり）
docker compose exec backend pytest

# 開発ループ向け（カバレッジ無効化）
docker compose exec -T backend pytest -q --no-cov

# 特定ファイル/テストのみ
docker compose exec backend pytest tests/integration/test_api_debug.py::TestAPIDebugMode::test_chat_endpoint_returns_debug_payload_and_header -q --no-cov
```
- 設定は `backend/pytest.ini` を参照（`--cov-fail-under=80` など）。

## フロントエンドテスト（Jest）
```bash
# 非対話（CI互換）実行（推奨）
docker compose run --rm -e CI=true frontend npm test -- --watchAll=false

# カバレッジ付き
docker compose exec frontend npm run test:coverage
```

## 統合テスト（E2E的な疎通含む）
```bash
# スクリプトで一括実行（バックエンド・フロント・疎通）
NO_COV=1 sh scripts/run_integration_tests.sh   # カバレッジ無効（開発ループ）
sh scripts/run_integration_tests.sh            # カバレッジ有効
```
- スクリプト: `scripts/run_integration_tests.sh`
  - Backend: `pytest tests/integration/`
  - Frontend: `npm test -- --testPathPattern=integration --watchAll=false`
  - 疎通: `curl` と `frontend`→`backend` の接続確認

## CI ヒント
- GitHub Actions（`.github/workflows/ci.yml`）は Docker ベースで実行。
- 失敗時はログと `htmlcov/`（バックエンド）や Jest のカバレッジ出力を確認。

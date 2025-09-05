# Contributing Guide

> バージョン: 1.0.0  
> 最終更新: 2025-09-05  
> 対象: すべてのコントリビューター / レビュアー

本プロジェクトは Docker 前提・TDD を基本とした開発プロセスです。コード・ドキュメント・テストは一貫して Docker コンテナ内で実行してください。

## 開発フロー（ベストプラクティス）
1. 課題の明確化（Issue 作成）
2. ブランチ作成（例: `feat/...`, `fix/...`）
3. TDD で小さく実装（300行以内の差分を推奨）
4. Docker 内でテスト（バックエンド/フロント/統合）
5. ドキュメント更新（API/挙動変更に追随）
6. PR 作成（PR テンプレとチェックリスト遵守）

## ブランチ戦略とコミット規約
- ブランチ命名: `feat/*`, `fix/*`, `docs/*`, `chore/*`, `refactor/*`
- Conventional Commits 準拠:
  - `feat: ...` 新機能
  - `fix: ...` 不具合修正
  - `docs: ...` ドキュメントのみ
  - `test: ...` テストのみ
  - `refactor: ...` 機能変更なしのリファクタリング
  - `chore: ...` ビルド/依存/CI 等

例:
```
feat(api): add history limit parameter to GET /chat/history
fix(frontend): prevent WebSocket reconnect loop on 1001 close
docs: add debug/trace guide and curl examples
```

## コーディング規約 / Lint / Format

### Backend (Python)
- フォーマッタ: `black`
- インポート整形: `isort`
- 型チェック: `mypy`

実行例（Docker 内）:
```bash
docker compose exec backend black app/
docker compose exec backend isort app/
docker compose exec backend mypy app/
```

### Frontend (TypeScript/React)
- Lint: `eslint`
- Format: `prettier`
- 型チェック: `tsc`

実行例（Docker 内）:
```bash
docker compose exec frontend npm run lint
docker compose exec frontend npm run format
docker compose exec frontend npm run type-check
```

## テスト（Docker専用）
- すべてのテストは Docker コンテナ内で実行します。
- フロントは非対話実行（`--watchAll=false`）を基本とします。

ショートカット:
```bash
# 開発ループ（カバレッジ無効）
NO_COV=1 sh scripts/run_integration_tests.sh

# バックエンドのみ
docker compose exec -T backend pytest -q --no-cov

# フロントエンドのみ（CI互換）
docker compose run --rm -e CI=true frontend npm test -- --watchAll=false
```

詳細は `docs/testing.md` を参照してください。

## ドキュメント更新の原則
- API/挙動/ログ構造の変更時は、以下を必ず更新:
  - `docs/api_reference.md`
  - `docs/development/backend_guide.md` / `docs/development/frontend_guide.md`
  - `docs/debug_trace.md`（`display_header`/trace 変更時）
  - `docs/graph_assets.md`（LangGraph 変更時は Mermaid/PNG を再生成）
- README の索引がリンク切れにならないように保守

## PR チェックリスト
- 仕様変更に対応するテストを追加（TDD）
- すべてのテストを Docker 内でパス
  - Backend: `pytest`（閾値 >= 80%）
  - Frontend: Jest 非対話 + カバレッジ
  - Integration: `scripts/run_integration_tests.sh`
- Lint/Format/Type-check を実行済み
- ドキュメント更新（API例・curl・スクリーンショット等）
- Graph 資産（`docs/graph.mmd/png`）が最新
- 秘密情報・個人情報を含まない

## セキュリティと秘密情報
- API キー等の秘密情報をコミットしない
- `.env` はテンプレート（`.env.example`）のみに整備

## Issue / Discussion
- 再現手順・ログ・期待結果/実結果を明記
- スクリーンショットや `curl` 例を歓迎

## リリースと変更履歴
- リリース前に `CHANGELOG.md` を更新
- 重要な設計判断は `docs/adr/` に ADR として追記

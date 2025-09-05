# ADR-001: Agents v2 と Checkpointer の採用

> ステータス: 承認  
> 作成日: 2025-09-05  
> 対象: Backend（LangGraph）

## 背景
- 既存のエージェント実装は I/F が曖昧で拡張時の整合性確保が難しい。
- 対話の継続性・耐障害性（リトライ/再開）の要求が高まっている。
- 可観測性（Debug/Trace、グラフ可視化）を強化し、UI と連携したデバッグを容易にしたい。

## 決定
- LangGraph 公式の v2 形式に合わせた `AgentInput`/`AgentOutput` に統一し、レジストリ `get_agent_v2(name)` を採用する。
- Durable 実行を可能にするため、`ENABLE_CHECKPOINTER=true` の場合に `MemorySaver` を使用してコンパイルし、`thread_id` を `configurable` に付与する。
- Debug/Trace を標準化し、REST 応答 `message.content` の先頭に `[DEBUG] {display_header}\n\n` を付与。`ChatResponse.debug` に構造化情報を同梱する。

## 根拠
- v2 I/F による入出力の型安全化により、エージェント追加時のリグレッションを最小化。
- Checkpointer により長時間処理や中断からの復帰、失敗時の再実行が容易。
- 構造化された Debug/Trace は運用・QA でのトラブルシューティング時間を短縮。

## 影響
- 旧 I/F のエージェントは v2 へ移行が必要。
- `LangGraphService` のビルド・実行パスが Checkpointer の有無で分岐。
- フロントエンドは `[DEBUG]` ヘッダーの抽出と UI 表示（すでに `MessageItem.tsx` 実装済み）。

## 代替案
- 代替1: 既存 I/F のまま運用 → 型のばらつき・結合度増大により保守性が低下。
- 代替2: 外部ワークフローエンジン採用 → LangGraph との親和性・コスト・学習コストの観点で不利。

## 実装計画（抜粋）
1. `app/services/agents/types.py` に `AgentInput/AgentOutput` を定義（完了）。
2. `registry.py` に v2 レジストリ追加、旧 I/F の公開を停止（完了）。
3. `LangGraphService` で v2 I/F 専用ワークフローへ更新（完了）。
4. Checkpointer フラグ `ENABLE_CHECKPOINTER` を設定で管理（完了）。
5. Debug/Trace の `display_header` と `decision_trace` を統合（完了）。
6. テスト・ドキュメント更新（本ADR含む）（完了）。

## 計測/検証
- 統合テスト: `scripts/run_integration_tests.sh` で回帰確認。
- デバッグ検証: `debug=true` 時に `[DEBUG]` ヘッダー表示・`debug` ペイロード内容を確認。
- グラフ可視化: `scripts/generate_graph_assets.sh` で Mermaid/PNG を更新し設計と乖離がないかレビュー。

## 参照
- `docs/development/backend_guide.md`
- `docs/debug_trace.md`
- `docs/graph_assets.md`

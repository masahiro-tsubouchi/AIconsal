# Backend 開発ガイド（FastAPI + LangGraph）

> バージョン: 1.0.0  
> 最終更新: 2025-09-05  
> 対象: バックエンド開発者 / レビュアー

## プロジェクト構成（抜粋）
```
backend/
├─ app/
│  ├─ api/v1/
│  │  ├─ chat.py      # チャットAPI（REST/WS、履歴limit対応）
│  │  └─ files.py     # ファイルAPI（upload/get/list/delete）
│  ├─ services/
│  │  ├─ langgraph_service.py     # LangGraphワークフロー
│  │  ├─ agents/ (types.py, registry.py, *.py)
│  │  └─ tools/  (detect/registry 実装)
│  ├─ models/   # Pydanticモデル
│  └─ core/     # 設定・ユーティリティ
└─ pytest.ini
```

## エージェント I/F（v2）
- 型定義: `app/services/agents/types.py`
  - `AgentInput` / `AgentOutput`
  - 署名: `AgentFnV2 = Callable[[LLMProvider|None, AgentInput], Awaitable[AgentOutput]]`
- レジストリ: `app/services/agents/registry.py`
  - `get_agent_v2(name)` で解決（`general/python/manufacturing` 登録済み）
- 呼び出し例（`langgraph_service.py` 内）:
```python
inp = AgentInput(user_query=state['user_query'], conversation_history=state['conversation_history'], file_context=state['file_context'])
out = await agent_v2(self._llm, inp)
state['response'] = out.content
```

## LangGraphワークフロー
- 定義・コンパイル: `LangGraphService._build_workflow()`
  - ノード: `analyze_query` → (`process_manufacturing` | `process_python` | `general_response` | `process_tool`) → `END`
  - 公式準拠の可視化: `export_mermaid()` は `get_graph().draw_mermaid()` を優先
  - PNG出力: `export_mermaid_png()`（スクリプト側でCLIフォールバック）
- 実行: `LangGraphService.process_query()`
  - タイムアウト: `workflow_invoke_timeout_seconds`（設定）
  - Durable: `ENABLE_CHECKPOINTER=true` のとき `MemorySaver` でコンパイルし `thread_id` を `configurable` に付与

## ツール実行
- 検出: `tools.detect_tool_request()`（接頭辞 `sql:`, `web:` など）
- 実行: `tools.async_execute_tool()` が `ToolResult` を返却（`tool/input/took_ms/error`）
- Debug時は `decision_trace` に `tool_invoked` を追記

## Debug/Trace
- `debug=True` で `decision_trace` を蓄積し、`_build_debug_info()` が UI 用 `display_header` を生成
  （`app/services/langgraph_service.py`）。
- RESTでは `message.content` 先頭に `[DEBUG] ...` を付与し、`ChatResponse.debug` に構造化情報を同梱
  （`app/api/v1/chat.py`）。

### フェーズA: イベントストリーミング（開発者向け）
- 実装ファイル: `app/services/langgraph_service.py` の `stream_events()`
  - LangGraph の `astream_events` を用いて、`on_chain_start|on_chain_stream|on_chain_end` などを逐次送出
  - 返却ペイロードは `{ "event_type", "ts", "payload" }` に正規化
- WebSocket 統合: `app/api/v1/chat.py` の `/api/v1/chat/ws/{session_id}`
  - クエリ `?debug_streaming=1` または環境変数 `DEBUG_STREAMING=true` で有効化
  - 有効時、通常の `message` とは別に `{"type":"debug_event"}` を逐次送信
- サニタイズ方針（漏えい抑止）:
  - トップレベルで `state/input/inputs/context/config` など機微・重量フィールドを除去
  - 文字列は 500 文字を上限にトリム
  - 追加強化（再帰的除去）は今後の改善余地
- フェーズB最小プレビュー（breakpoint）:
  - `DEBUG_BREAKPOINTS=true` かつ `debug=true` で接続した場合、処理開始前に `breakpoint_hit` を1度 emit
- 運用指針:
  - 既定は OFF。調査時のみ `?debug_streaming=1` か `DEBUG_STREAMING=true` を使用
  - 本番では OFF を推奨

## ロギング
- `structlog` で相関IDを付与
  - `thread_id` / `agent` / `tool` / イベント種別（`query_analyzed`, `agent_completed`, `tool_executed` 等）
- 検証テスト: `backend/tests/test_logging_correlations.py`

## Docker実行
```bash
# 起動
docker compose up -d backend
# テスト
docker compose exec backend pytest -q --no-cov
# Mermaid/PNG 生成
sh scripts/generate_graph_assets.sh
```

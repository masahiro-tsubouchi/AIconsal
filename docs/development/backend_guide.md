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
- RESTでは `message.content` 先頭に `[DEBUG] ...` を付与し、`ChatResponse.debug` に構造化情報を同梱

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

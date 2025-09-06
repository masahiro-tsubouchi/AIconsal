# Debug / Trace モードガイド

> バージョン: 1.0.0  
> 最終更新: 2025-09-05  
> 対象: 開発者 / QA

## 目的
- 応答生成の意思決定（エージェント・ツール）を可視化するためのモード。
- UI では先頭に短いヘッダー（`display_header`）を表示します。

## 有効化（REST）
```bash
curl -s -X POST http://localhost:8002/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message":"Pythonの基本","session_id":"dbg-1","debug":true}' | jq .
```

## レスポンス例（要約）
```json
{
  "message": {
    "content": "[DEBUG] Agent: python_mentor / Tool: none / 根拠: キーワード検出\n\n(本文...)",
    "role": "assistant",
    "session_id": "dbg-1",
    "timestamp": "2025-09-05T12:34:56.789Z"
  },
  "debug": {
    "display_header": "Agent: python_mentor / Tool: none / 根拠: キーワード検出",
    "selected_agent": "python_mentor",
    "selected_tool": null,
    "decision_trace": [
      {"type":"agent_selected","name":"python_mentor","reason":"キーワード検出","ts":1725350000000}
    ],
    "thread_id": "dbg-1"
  }
}
```

## バックエンド内部
- `LangGraphService.process_query(debug=True)` で `decision_trace` を蓄積し、`_build_debug_info()` が `display_header` を生成（`app/services/langgraph_service.py`）。
- `app/api/v1/chat.py` で `message.content` の先頭に `[DEBUG] ...` を付与し、`debug` をレスポンスに同梱。

## フロントエンド表示
- `MessageItem.tsx` で `[DEBUG] ...` の1行目を検出してヘッダーバッジ表示。本文Markdownはヘッダーを除いて描画。コピーは元テキストを維持。
- フェーズA: WebSocket `debug_event` を受け取り、`components/debug/DebugPanel.tsx` でリアルタイム表示可能。

## フェーズA: WebSocket Debug Event Streaming（開発者向け）
- 有効化方法
  - クエリ: `ws://.../api/v1/chat/ws/{session_id}?debug_streaming=1`
  - 環境変数: `DEBUG_STREAMING=true`（バックエンド） / `REACT_APP_DEBUG_STREAMING=true`（フロント、クエリ自動付与）
- イベント例（サニタイズ済み）
```json
{
  "type": "debug_event",
  "session_id": "dbg-1",
  "data": {
    "event_type": "on_chain_start",
    "ts": 1725235200000,
    "payload": {"event": "on_chain_start", "name": "analyze_query", "tags": ["graph:step:1"]}
  }
}
```
- 注意: 入力や内部状態は除去・短縮されます（漏えい抑止）。

### 最小ブレークポイント（プレビュー）
- `DEBUG_BREAKPOINTS=true` かつ `debug=true` の場合、処理開始前に `breakpoint_hit` イベントを1度送出します。

## 注意（セキュリティ/プライバシー）
- `decision_trace` には入力の一部（ツール入力の短縮版など）が含まれる場合があります。運用時は取り扱いに注意してください。

# APIリファレンス (Manufacturing AI Assistant)

> バージョン: 1.0.0  
> 最終更新: 2025-09-05  
> 対象: 開発者 / QA / 運用

## 概要
- ベースURL: `http://localhost:8002`
- OpenAPI: [http://localhost:8002/docs](http://localhost:8002/docs)
- すべてDocker環境でのアクセスを前提とします（`docker compose up -d`）。

## 認証
- 現状、社内ネットワーク内利用を前提とした簡易構成（追加の認証は未導入）。

## エンドポイント

### チャット: POST `/api/v1/chat/`
- 概要: ユーザーメッセージを送信し、AI応答を取得します。
- リクエスト(JSON):
```json
{
  "message": "string (必須)",
  "session_id": "string (任意)",
  "file_ids": ["string"],
  "debug": true
}
```
- レスポンス(JSON 概要):
```json
{
  "message": {
    "id": "string",
    "session_id": "string",
    "content": "string",
    "role": "assistant",
    "timestamp": "ISO-8601",
    "processing_time": 0.123,
    "file_ids": ["string"]
  },
  "session_id": "string",
  "processing_time": 0.123,
  "debug": {
    "display_header": "Agent: ... / Tool: ... / 根拠: ...",
    "selected_agent": "string|null",
    "selected_tool": "string|null",
    "decision_trace": [ {"type": "...", "ts": 1725235200000 } ],
    "thread_id": "string"
  }
}
```
- 備考: `debug=true` の場合、`message.content` 先頭に `[DEBUG] {display_header}\n\n` が自動付与され、`debug` フィールドにフルのデバッグ情報が返ります（`app/api/v1/chat.py`）。
- curl例:
```bash
curl -s -X POST http://localhost:8002/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message":"改善活動のポイントは？","session_id":"demo-1","debug":true}' | jq .
```

### 履歴取得: GET `/api/v1/chat/history/{session_id}`
- 概要: セッションの会話履歴を取得します。
- クエリ: `?limit=N`（任意、`N>=1` の最新 N 件のみ返却）。
- レスポンス(JSON 概要):
```json
{
  "session_id": "string",
  "messages": [ { "id": "...", "content": "...", "role": "user|assistant", "timestamp": "..." } ],
  "created_at": "ISO-8601",
  "last_active": "ISO-8601"
}
```
- curl例:
```bash
curl -s "http://localhost:8002/api/v1/chat/history/demo-1?limit=50" | jq .
```

### WebSocket: `WS /api/v1/chat/ws/{session_id}`
- 概要: リアルタイム応答（双方向）。型付きJSONメッセージを送受信します。
- メッセージ種別（例）:
```json
{"type": "status",  "session_id": "...", "data": "connected"}
{"type": "message", "session_id": "...", "data": { /* ChatMessage */ }}
{"type": "error",   "session_id": "...", "data": "エラー内容"}
```
- 備考: 接続直後に `status` が送信され、その後は `message`（`ChatMessage`）が届きます（`app/api/v1/chat.py`）。

### ファイルアップロード: POST `/api/v1/files/upload`
- フォーム: `file`(必須, binary), `session_id`(任意)
- バリデーション: 拡張子は `settings.supported_file_types`、サイズは `settings.max_file_size` 以内。
- レスポンス(JSON 概要):
```json
{
  "file": {
    "id": "string",
    "filename": "string",
    "original_filename": "string",
    "file_type": ".pdf|.docx|.txt|.csv|.xlsx",
    "file_size": 12345,
    "session_id": "string",
    "upload_time": "ISO-8601",
    "content": "抽出テキスト or null"
  },
  "message": "..."
}
```
- curl例:
```bash
curl -s -X POST http://localhost:8002/api/v1/files/upload \
  -F "file=@/path/to/sample.pdf" -F "session_id=demo-1" | jq .
```

### ファイル取得: GET `/api/v1/files/{file_id}`
- 概要: アップロード済みファイルの情報を返します。

### セッションのファイル一覧: GET `/api/v1/files/session/{session_id}`
- 概要: セッションに紐づくファイル一覧を返します。

### ファイル削除: DELETE `/api/v1/files/{file_id}`
- 概要: 指定ファイルを削除します。

## エラーとステータス
- バリデーションエラー: 400/413 などを明示（`files/upload`）。
- サーバーエラー: 500 を返し、詳細は `detail` に記載。
- WebSocket: エラー時は `type:error` で送信。

## 補足
- 詳細な型は OpenAPI を参照してください（`/docs`）。
- `debug` はRESTエンドポイントでサポート（現状、WSは通常メッセージを送信）。

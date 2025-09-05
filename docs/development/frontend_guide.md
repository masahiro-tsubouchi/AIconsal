# Frontend 開発ガイド（React + TypeScript）

> バージョン: 1.0.0  
> 最終更新: 2025-09-05  
> 対象: フロントエンド開発者 / レビュアー

## 構成（抜粋）
```
frontend/
├─ src/
│  ├─ components/MessageList/MessageItem.tsx
│  ├─ hooks/useWebSocket.ts
│  ├─ services/api.ts / mappers.ts
│  └─ types/api.ts
└─ package.json
```

## WebSocket（`hooks/useWebSocket.ts`）
- 接続URLは `REACT_APP_WS_URL`（未指定時は `REACT_APP_API_URL` → `ws://` に置換）
- 型付きメッセージをハンドル（`type: status|error|message`）。`message` の `data` はバックエンドの `ChatMessage`。
- 切断時の自動再接続（3秒）

## メッセージ表示（`components/MessageList/MessageItem.tsx`）
- アシスタントメッセージの先頭が `"[DEBUG] ...\n\n"` の場合、先頭行をデバッグヘッダーとして抽出し、UIで強調表示。
- 本文は `react-markdown` で描画。コピー操作は元テキスト（ヘッダー含む）を保持。

## 正規化（`services/mappers.ts`）
- バックエンドの `file_ids` を `file_context` に正規化してフロントの `Message` へ統一。
- `normalizeHistory()` は履歴の `messages` を `normalizeMessage()` で整形。

## テスト
```bash
# 非対話実行（CI同等）
docker compose run --rm -e CI=true frontend npm test -- --watchAll=false
# カバレッジ
docker compose exec frontend npm run test:coverage
```

## 環境変数（`.env`）
```
REACT_APP_API_URL=http://localhost:8002
REACT_APP_WS_URL=ws://localhost:8002
PORT=3002
```

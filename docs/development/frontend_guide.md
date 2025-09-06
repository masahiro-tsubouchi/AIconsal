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
- 型付きメッセージをハンドル（`type: status|error|message|debug_event`）。`message` の `data` はバックエンドの `ChatMessage`。
- 切断時の自動再接続（3秒）

### フェーズA: Debug Event Streaming（開発者向け）
- 有効化: フロント `.env` に `REACT_APP_DEBUG_STREAMING=true` を設定すると、WS 接続先に `?debug_streaming=1` が自動付与されます。
- 受信: `type: 'debug_event'` を受け取った場合、既定では `console.debug` に出力します。
- カスタムハンドラ: `useWebSocket({ onDebugEvent })` を渡すと、アプリ側でリアルタイム可視化が可能です。
  - 例: `components/debug/DebugPanel.tsx` を用意し、`Chat.tsx` から `onDebugEvent` でイベント配列に蓄積して表示。

```tsx
// Chat.tsx（抜粋）
const { isConnected, sendMessage } = useWebSocket({
  sessionId,
  onMessage: ..., onError: ..., onStatusUpdate: ..., 
  onDebugEvent: (ev) => setDebugEvents(prev => [...prev.slice(-99), ev])
});
```

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
REACT_APP_DEBUG_STREAMING=false
PORT=3002
```

### 開発時の注意
- StrictMode によるマウント/アンマウントで 1006 の再接続が発生する場合があります（自動で復帰）。

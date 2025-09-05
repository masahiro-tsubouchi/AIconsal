# 250905_LangSmith実装計画

> バージョン: 1.0.0  
> 作成日: 2025-09-05  
> 対象: Backend（LangGraph + LangChain）  
> 目的: LangSmith を用いたエージェント・ワークフローの可視化を、環境変数のみで最小限の変更で有効化する（既定はOFF）

## 1. 方針（最小構成）
- 既存コードの変更は原則不要（LangChain/LangGraph の標準トレーシング機構を使用）。
- Docker 環境で Backend コンテナに環境変数を与えるだけで有効化（既定は OFF）。
- プロジェクト名・APIキーは環境変数で注入し、Secrets 管理（.env, GitHub Secrets）を徹底。
- 既存の `Settings.langsmith_api_key` / `Settings.langsmith_project` はそのまま（参考値）。まずは標準環境変数で完結。

## 2. 必要な環境変数（推奨）
```bash
# 必須
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=xxxxx_your_langsmith_api_key_xxxxx
LANGCHAIN_PROJECT=manufacturing-ai-assistant

# 任意（デフォルトエンドポイントを明示したい場合）
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

- 備考: 既存設定に `langsmith_api_key`, `langsmith_project` があるが、最小構成では未使用でも可。将来的に SDK を直接使う場合に流用可能。

## 3. Docker / .env 設定例
### 3.1 backend/.env（ローカル専用・コミット禁止）
```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=xxxxx_your_langsmith_api_key_xxxxx
LANGCHAIN_PROJECT=manufacturing-ai-assistant
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

### 3.2 docker-compose.yml（backend サービス抜粋）
```yaml
services:
  backend:
    environment:
      - LANGCHAIN_TRACING_V2=${LANGCHAIN_TRACING_V2}
      - LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
      - LANGCHAIN_PROJECT=${LANGCHAIN_PROJECT:-manufacturing-ai-assistant}
      - LANGCHAIN_ENDPOINT=${LANGCHAIN_ENDPOINT:-https://api.smith.langchain.com}
```

## 4. 導入手順
1) LangSmith で API キーを発行し、backend/.env に設定（コミット禁止）。
2) docker compose を再起動：
```bash
docker compose up -d backend
```
3) 動作確認（任意の Chat API 呼び出し）：
```bash
curl -s -X POST http://localhost:8002/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message":"LangSmith可視化テスト","session_id":"lsm-1"}' | jq .
```
4) LangSmith UI で対象プロジェクト（`LANGCHAIN_PROJECT`）の Run/Trace を確認。

## 5. 受け入れ基準
- 既定（環境変数未設定）では挙動不変・トレース送信無し。
- 環境変数を設定すると、1回のリクエストで LangSmith ダッシュボードに Run が可視化される。
- 複数ノード（例: `analyze_query`→`process_*`）がツリーとして確認できる。

## 6. セキュリティ/プライバシ
- APIキーは `.env` / CI の Secrets で管理し、リポジトリにコミットしない。
- デバッグ/トレースには入力の一部が含まれる可能性があるため、運用時は取り扱いに注意（PII/機密の送信禁止）。
- フロントエンドへ環境変数を公開しない（Backend のみ）。

## 7. ロールバック
- `LANGCHAIN_TRACING_V2` を未設定/`false` にするか、`LANGCHAIN_API_KEY` を外す。
- Backend コンテナを再起動すればトレーシングは停止。

## 8. 影響範囲・パフォーマンス
- 影響範囲は Backend のみ。既存 API/WS は不変。
- 追加オーバーヘッドは最小限（ネットワーク送信）。問題があればフラグOFFで即停止可能。

## 9. 次フェーズ（任意・非必須）
- メタデータ/タグ付与：`RunnableConfig` の `tags` / `metadata` で `thread_id` や `agent` を付帯（可観測性向上）。
- Debug Streaming との連携：LangSmith 側の Run とアプリ内 `debug_event` を相関。
- SDK 直接利用：`langsmith` クライアントでカスタムイベント/メトリクスを送信。

## 10. 参考
- LangSmith: https://smith.langchain.com/  
- Tracing v2 環境変数: https://docs.smith.langchain.com/tracing  
- LangGraph × LangSmith（概念）: https://langchain-ai.github.io/langgraph/concepts/streaming/

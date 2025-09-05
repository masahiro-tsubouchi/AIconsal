# グラフ資産ガイド（Mermaid / PNG）

> バージョン: 1.0.0  
> 最終更新: 2025-09-05  
> 対象: 開発者 / CI

## 目的
- LangGraph 実体（コンパイル済みグラフ）と一致した Mermaid/PNG を生成し、`docs/graph.mmd` と `docs/graph.png` を更新します。

## 推奨ワンコマンド
```bash
sh scripts/generate_graph_assets.sh
```
- 前提: `docker compose up -d backend`（backend コンテナが起動済み）
- 動作:
  - Mermaid生成は backend コンテナ内で `export_mermaid()` を実行
  - PNG はビルトイン `export_mermaid_png()` を試行し、失敗時のみ Mermaid CLI にフォールバック

## フォールバック制御
```bash
# 常にMermaid CLIを使いたい場合
FORCE_PNG_FALLBACK=1 sh scripts/generate_graph_assets.sh
```

## 手動実行
```bash
# Mermaidのみ生成（backend コンテナ内実行）
docker compose exec -T backend \
  python -c "from app.services.langgraph_service import LangGraphService; print(LangGraphService().export_mermaid())" > docs/graph.mmd

# Mermaid CLI で PNG 生成
sh scripts/render_graph_png.sh
```

## 出力先
- Mermaid: `docs/graph.mmd`
- PNG: `docs/graph.png`

## 更新タイミング
- ワークフローのノード/遷移に変更が入ったPRで更新してください。

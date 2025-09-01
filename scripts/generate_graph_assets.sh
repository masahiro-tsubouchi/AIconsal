#!/usr/bin/env bash
# Generate Mermaid (docs/graph.mmd) via backend container and render PNG (docs/graph.png) via Docker
# Usage: sh scripts/generate_graph_assets.sh
set -euo pipefail

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." &> /dev/null && pwd)
DOCS_DIR="$REPO_ROOT/docs"
MERMAID_FILE="$DOCS_DIR/graph.mmd"
PNG_FILE="$DOCS_DIR/graph.png"

mkdir -p "$DOCS_DIR"

echo "[1/2] Generating Mermaid to $MERMAID_FILE ..."
# Requires backend service running via docker compose up -d
if ! docker compose ps backend >/dev/null 2>&1; then
  echo "docker compose is not running or 'backend' service unavailable. Start it with: docker compose up -d" >&2
  exit 1
fi

docker compose exec -T backend \
  python -c "from app.services.langgraph_service import LangGraphService; print(LangGraphService().export_mermaid())" \
  > "$MERMAID_FILE"

if [ ! -s "$MERMAID_FILE" ]; then
  echo "Failed to write Mermaid file: $MERMAID_FILE" >&2
  exit 2
fi

echo "[2/2] Rendering PNG to $PNG_FILE ..."
# Try built-in LangGraph renderer first (inside backend container)
set +e
docker compose exec -T backend python - <<'PY' > "$PNG_FILE"
from app.services.langgraph_service import LangGraphService
import sys
sys.stdout.buffer.write(LangGraphService().export_mermaid_png())
PY
STATUS=$?
set -e

if [ $STATUS -ne 0 ] || [ ! -s "$PNG_FILE" ]; then
  echo "Built-in PNG renderer failed or produced empty file. Falling back to Mermaid CLI ..." >&2
  # Ensure render script is executable when run directly with bash/sh as well
  sh "$REPO_ROOT/scripts/render_graph_png.sh"
fi

if [ -f "$PNG_FILE" ]; then
  echo "✅ Done:\n  - Mermaid: $MERMAID_FILE\n  - PNG    : $PNG_FILE"
else
  echo "PNG generation appears to have failed. Check logs above." >&2
  exit 3
fi

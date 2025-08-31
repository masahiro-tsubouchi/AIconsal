#!/usr/bin/env bash
# Render docs/graph.mmd -> docs/graph.png using Mermaid CLI in a container
# Requirements: Docker available on host, internet access (first run pulls image)
set -euo pipefail

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." &> /dev/null && pwd)
DOCS_DIR="$REPO_ROOT/docs"
INPUT="$DOCS_DIR/graph.mmd"
OUTPUT="$DOCS_DIR/graph.png"

if [ ! -f "$INPUT" ]; then
  echo "Mermaid source not found: $INPUT" >&2
  echo "Run: docker compose exec -T backend python -c \"from app.services.langgraph_service import LangGraphService; print(LangGraphService().export_mermaid())\" > docs/graph.mmd" >&2
  exit 1
fi

# Use ghcr.io/mermaid-js/mermaid-cli image to render without local node install
# Notes:
# -v mounts docs directory to /data inside container
# -u matches current user to avoid root-owned output
USER_FLAG=""
if command -v id >/dev/null 2>&1; then
  USER_FLAG="-u $(id -u):$(id -g)"
fi

echo "Rendering $INPUT -> $OUTPUT ..."
docker --version >/dev/null 2>&1 || true

set +e
docker run --rm $USER_FLAG \
  -v "$DOCS_DIR:/data" \
  ghcr.io/mermaid-js/mermaid-cli:10.9.1 \
  mmdc -i /data/graph.mmd -o /data/graph.png -b transparent -t default
STATUS=$?
set -e

if [ $STATUS -ne 0 ]; then
  echo "GHCR image pull or run failed. Trying Docker Hub fallback (minlag/mermaid-cli)..." >&2
  docker run --rm $USER_FLAG \
    -v "$DOCS_DIR:/data" \
    minlag/mermaid-cli:10.9.0 \
    -i /data/graph.mmd -o /data/graph.png -b transparent -t default
fi

if [ -f "$OUTPUT" ]; then
  echo "Done: $OUTPUT"
else
  echo "Failed to render PNG." >&2
  exit 2
fi

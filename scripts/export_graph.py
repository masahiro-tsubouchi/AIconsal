#!/usr/bin/env python3
"""
Export the current LangGraph workflow as a Mermaid diagram to docs/graph.mmd

Usage:
  python scripts/export_graph.py

This script is side-effect free except writing docs/graph.mmd.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Best-effort to make `app` (and `backend.app`) importable
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Try both import paths depending on PYTHONPATH
LangGraphService = None
try:
    from app.services.langgraph_service import LangGraphService as _LGS  # type: ignore
    LangGraphService = _LGS
except Exception:
    try:
        from backend.app.services.langgraph_service import (  # type: ignore
            LangGraphService as _LGS2,
        )
        LangGraphService = _LGS2
    except Exception as e:
        print(f"Failed to import LangGraphService: {e}")
        sys.exit(1)


def main() -> int:
    service = LangGraphService()
    mermaid = service.export_mermaid()

    out_dir = REPO_ROOT / "docs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "graph.mmd"
    out_file.write_text(mermaid, encoding="utf-8")

    print(f"Wrote Mermaid diagram to {out_file} ({len(mermaid)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

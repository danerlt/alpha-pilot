"""导出 OpenAPI schema 到 docs/api/openapi.json（webapp 前端类型生成的契约源）。

用法（仓库根目录）:
    cd backend && ALPHAPILOT_SKIP_SECRET_VALIDATION=1 uv run python scripts/export_openapi.py

前端随后执行 `cd webapp && npm run gen:api` 重新生成 TS 类型。
见 docs/webapp前端架构.md §3 B1。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("ALPHAPILOT_SKIP_SECRET_VALIDATION", "1")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.app import app  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "docs" / "api" / "openapi.json"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    schema = app.openapi()
    OUT.write_text(
        json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"OpenAPI schema 已导出: {OUT} ({len(schema.get('paths', {}))} paths)")


if __name__ == "__main__":
    main()

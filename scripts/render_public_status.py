#!/usr/bin/env python3
"""根据 state 和 handoff 生成 public/stage-status.md 与 final-summary.md。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"


def read_text(path: Path) -> str:
    return path.read_text().strip() if path.exists() else ""


def extract_handoff_summary(path: Path) -> str:
    if not path.exists():
        return ""
    for line in path.read_text().splitlines():
        if line.strip().startswith("summary:"):
            return line.split("summary:", 1)[1].strip()
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Render AlphaPilot public status")
    parser.add_argument("run_id")
    parser.add_argument("--final", action="store_true")
    args = parser.parse_args()

    run_dir = RUNS_DIR / args.run_id
    state = json.loads((run_dir / "state.json").read_text())

    plan_summary = extract_handoff_summary(run_dir / "handoff" / "planner-to-developer.yaml")
    impl_summary = extract_handoff_summary(run_dir / "handoff" / "developer-to-ops.yaml")
    ops_summary = extract_handoff_summary(run_dir / "handoff" / "ops-to-alpha-pilot.yaml")

    stage_text = (
        "# Stage Status\n\n"
        f"- Run: {args.run_id}\n"
        f"- 当前阶段：{state.get('currentStage')}\n"
        f"- 当前状态：{state.get('status')}\n"
        f"- 阻塞原因：{state.get('blockedReason')}\n"
        f"- 规划摘要：{plan_summary or '暂无'}\n"
        f"- 实现摘要：{impl_summary or '暂无'}\n"
        f"- 交付摘要：{ops_summary or '暂无'}\n"
    )
    (run_dir / "public" / "stage-status.md").write_text(stage_text)

    if args.final:
        final_text = (
            "# Final Summary\n\n"
            f"- 规划：{plan_summary or '暂无'}\n"
            f"- 实现：{impl_summary or '暂无'}\n"
            f"- 测试与交付：{ops_summary or '暂无'}\n"
            f"- 最终状态：{state.get('status')}\n"
        )
        (run_dir / "public" / "final-summary.md").write_text(final_text)

    print(run_dir / "public" / "stage-status.md")


if __name__ == "__main__":
    main()

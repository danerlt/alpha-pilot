#!/usr/bin/env python3
"""初始化一个新的 agent orchestration run。

这是最小脚手架脚本：
- 复制 runs/RUN_TEMPLATE
- 生成 run id
- 写入 task.md
- 写入 state.json

当前阶段先做本地文件初始化，不直接接 workflow 执行器。
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
TEMPLATE_DIR = RUNS_DIR / "RUN_TEMPLATE"


def next_run_id() -> str:
    now = datetime.now(timezone.utc)
    prefix = now.strftime("R-%Y%m%d")
    existing = sorted(p.name for p in RUNS_DIR.glob(f"{prefix}-*") if p.is_dir())
    if not existing:
        return f"{prefix}-001"
    last = existing[-1].split("-")[-1]
    n = int(last) + 1
    return f"{prefix}-{n:03d}"


def write_task(task_file: Path, title: str, task_type: str, requested_by: str, original_request: str) -> None:
    content = f"# Task\n\n- Title: {title}\n- Type: {task_type}\n- Requested by: {requested_by}\n- Created at: {datetime.now(timezone.utc).isoformat()}\n\n## Original Request\n\n{original_request}\n"
    task_file.write_text(content)


def write_state(state_file: Path, run_id: str, workflow: str) -> None:
    state = {
        "runId": run_id,
        "workflow": workflow,
        "status": "pending",
        "currentStage": "intake",
        "blockedReason": None,
        "approvalNeeded": False,
        "retryFrom": None,
    }
    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def write_public_status(status_file: Path, title: str) -> None:
    status_file.write_text(f"# Stage Status\n\n- 当前任务：{title}\n- 当前阶段：intake\n- 当前状态：pending\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize an AlphaPilot agent orchestration run")
    parser.add_argument("--title", required=True)
    parser.add_argument("--type", required=True, choices=["feature", "bug", "deploy"])
    parser.add_argument("--requested-by", default="unknown")
    parser.add_argument("--request", required=True)
    args = parser.parse_args()

    workflow = "alpha-feature-dev" if args.type == "feature" else "alpha-bug-fix"
    run_id = next_run_id()
    run_dir = RUNS_DIR / run_id
    shutil.copytree(TEMPLATE_DIR, run_dir)

    write_task(run_dir / "task.md", args.title, args.type, args.requested_by, args.request)
    write_state(run_dir / "state.json", run_id, workflow)
    write_public_status(run_dir / "public" / "stage-status.md", args.title)

    print(run_id)


if __name__ == "__main__":
    main()

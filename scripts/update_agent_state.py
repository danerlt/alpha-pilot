#!/usr/bin/env python3
"""更新 run 的 state.json。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"


def main() -> None:
    parser = argparse.ArgumentParser(description="Update AlphaPilot run state")
    parser.add_argument("run_id")
    parser.add_argument("--status")
    parser.add_argument("--stage")
    parser.add_argument("--blocked-reason")
    parser.add_argument("--approval-needed", choices=["true", "false"])
    parser.add_argument("--retry-from")
    args = parser.parse_args()

    state_file = RUNS_DIR / args.run_id / "state.json"
    state = json.loads(state_file.read_text())

    if args.status is not None:
        state["status"] = args.status
    if args.stage is not None:
        state["currentStage"] = args.stage
    if args.blocked_reason is not None:
        state["blockedReason"] = args.blocked_reason
    if args.approval_needed is not None:
        state["approvalNeeded"] = args.approval_needed == "true"
    if args.retry_from is not None:
        state["retryFrom"] = args.retry_from

    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    print(state_file)


if __name__ == "__main__":
    main()

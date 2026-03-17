#!/usr/bin/env python3
"""写入 handoff 文件。"""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"


def yaml_list(items: list[str], indent: int = 2) -> str:
    if not items:
        return "[]"
    pad = " " * indent
    return "\n".join(f"{pad}- {item}" for item in items)


def main() -> None:
    parser = argparse.ArgumentParser(description="Write AlphaPilot handoff file")
    parser.add_argument("run_id")
    parser.add_argument("name", help="planner-to-developer | developer-to-ops | ops-to-alpha-pilot")
    parser.add_argument("--from-role", required=True)
    parser.add_argument("--to-role", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--next-action", required=True)
    parser.add_argument("--artifacts", nargs="*", default=[])
    parser.add_argument("--constraints", nargs="*", default=[])
    parser.add_argument("--risks", nargs="*", default=[])
    parser.add_argument("--questions", nargs="*", default=[])
    args = parser.parse_args()

    out = RUNS_DIR / args.run_id / "handoff" / f"{args.name}.yaml"
    text = f"""handoff:
  runId: {args.run_id}
  from: {args.from_role}
  to: {args.to_role}
  stage: {args.stage}
  status: {args.status}
  summary: {args.summary}
  artifacts:
{yaml_list(args.artifacts, 4)}
  constraints:
{yaml_list(args.constraints, 4)}
  risks:
{yaml_list(args.risks, 4)}
  questions:
{yaml_list(args.questions, 4)}
  nextAction: {args.next_action}
"""
    out.write_text(text)
    print(out)


if __name__ == "__main__":
    main()

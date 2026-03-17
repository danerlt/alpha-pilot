#!/usr/bin/env python3
"""最小角色执行桥接脚本。

当前版本支持：
- 读取 run_id + role
- 校验当前阶段与上游工件是否满足执行前置条件
- 生成 prompt 文件
- 根据角色映射输出建议执行命令
- 兼容 developer / implementer 历史命名差异

后续可继续接真实 CLI 执行与结果解析。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
CONFIG_FILE = ROOT / "config" / "agent_runners.json"

ROLE_ALIASES = {
    "planner": "planner",
    "developer": "developer",
    "implementer": "developer",
    "ops": "ops",
}

ROLE_STAGE_RULES = {
    "planner": {"intake", "plan", "bug-plan"},
    "developer": {"implement", "fix", "retrying"},
    "ops": {"ops-verify-and-ship"},
}

ROLE_REQUIREMENTS = {
    "planner": [],
    "developer": [
        {
            "label": "planner requirements",
            "any_of": ["plan/requirements.md"],
        },
        {
            "label": "planner design",
            "any_of": ["plan/design.md"],
        },
        {
            "label": "planner scope",
            "any_of": ["plan/scope.json"],
        },
        {
            "label": "planner handoff",
            "any_of": [
                "handoff/planner-to-developer.yaml",
                "handoff/planner-to-implementer.yaml",
            ],
        },
    ],
    "ops": [
        {
            "label": "developer implementation summary",
            "any_of": ["implement/summary.md"],
        },
        {
            "label": "developer changed files",
            "any_of": ["implement/changed-files.json"],
        },
        {
            "label": "developer handoff",
            "any_of": [
                "handoff/developer-to-ops.yaml",
                "handoff/implementer-to-ops.yaml",
            ],
        },
    ],
}


class ValidationError(Exception):
    """Raised when a run is not ready for the requested role."""


def load_state(run_dir: Path) -> dict:
    return json.loads((run_dir / "state.json").read_text())


def load_task(run_dir: Path) -> str:
    return (run_dir / "task.md").read_text()


def resolve_role(role: str) -> str:
    try:
        return ROLE_ALIASES[role]
    except KeyError as exc:
        raise ValidationError(f"Unsupported role: {role}") from exc


def find_existing_file(run_dir: Path, candidates: list[str]) -> Path | None:
    for candidate in candidates:
        path = run_dir / candidate
        if path.exists():
            return path
    return None


def is_placeholder_content(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    placeholder_markers = ["REPLACE_ME", "RUN_TEMPLATE"]
    return any(marker in stripped for marker in placeholder_markers)


def validate_run_ready(run_id: str, role: str) -> tuple[Path, dict]:
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        raise ValidationError(f"Run not found: {run_id}")

    state = load_state(run_dir)
    current_stage = state.get("currentStage")
    allowed_stages = ROLE_STAGE_RULES[role]
    if current_stage not in allowed_stages:
        raise ValidationError(
            f"Role '{role}' cannot run at stage '{current_stage}'. Allowed stages: {', '.join(sorted(allowed_stages))}."
        )

    missing = []
    placeholders = []
    for requirement in ROLE_REQUIREMENTS[role]:
        path = find_existing_file(run_dir, requirement["any_of"])
        if path is None:
            missing.append(f"{requirement['label']} -> one of {', '.join(requirement['any_of'])}")
            continue
        if is_placeholder_content(path.read_text()):
            placeholders.append(str(path.relative_to(run_dir)))

    problems = []
    if missing:
        problems.append("missing prerequisites: " + "; ".join(missing))
    if placeholders:
        problems.append("placeholder artifacts detected: " + ", ".join(placeholders))

    if problems:
        raise ValidationError(f"Run '{run_id}' is not ready for role '{role}': " + " | ".join(problems))

    return run_dir, state


def read_optional(run_dir: Path, *candidates: str) -> str:
    path = find_existing_file(run_dir, list(candidates))
    if path is None:
        return ""
    return path.read_text()


def build_prompt(run_id: str, role: str) -> str:
    run_dir, state = validate_run_ready(run_id, role)
    task = load_task(run_dir)

    if role == "planner":
        return dedent(f"""
        你是 AlphaPilot 的 planner。

        当前 run: {run_id}
        当前阶段: {state.get('currentStage')}
        当前状态: {state.get('status')}

        请基于以下任务生成：
        1. plan/requirements.md
        2. plan/design.md
        3. plan/scope.json
        4. 一段给 developer 的 handoff 摘要

        任务内容如下：

        {task}
        """).strip()

    if role == "developer":
        req = read_optional(run_dir, "plan/requirements.md")
        design = read_optional(run_dir, "plan/design.md")
        scope = read_optional(run_dir, "plan/scope.json")
        handoff = read_optional(
            run_dir,
            "handoff/planner-to-developer.yaml",
            "handoff/planner-to-implementer.yaml",
        )
        return dedent(f"""
        你是 AlphaPilot 的 developer。

        当前 run: {run_id}
        当前阶段: {state.get('currentStage')}
        当前状态: {state.get('status')}

        请基于现有方案实现代码，并产出：
        1. implement/summary.md
        2. implement/changed-files.json
        3. 一段给 ops 的 handoff 摘要

        Task:
        {task}

        Requirements:
        {req}

        Design:
        {design}

        Scope:
        {scope}

        Planner Handoff:
        {handoff}
        """).strip()

    if role == "ops":
        impl = read_optional(run_dir, "implement/summary.md")
        changed_files = read_optional(run_dir, "implement/changed-files.json")
        handoff = read_optional(
            run_dir,
            "handoff/developer-to-ops.yaml",
            "handoff/implementer-to-ops.yaml",
        )
        return dedent(f"""
        你是 AlphaPilot 的 ops。

        当前 run: {run_id}
        当前阶段: {state.get('currentStage')}
        当前状态: {state.get('status')}

        请完成以下交付子阶段：
        - test-design
        - test-run
        - review
        - pr
        - merge
        - deploy

        并产出：
        1. ops/test-plan.md
        2. ops/test-report.md
        3. ops/review-report.md
        4. ops/pr.md
        5. ops/merge.md
        6. ops/deploy.md
        7. 一段给 alpha-pilot 的 handoff 摘要

        Implementation Summary:
        {impl}

        Changed Files:
        {changed_files}

        Developer Handoff:
        {handoff}
        """).strip()

    raise ValidationError(f"Unsupported role: {role}")


def write_prompt_file(run_id: str, role: str, prompt: str) -> Path:
    prompt_dir = RUNS_DIR / run_id / "_prompts"
    prompt_dir.mkdir(exist_ok=True)
    path = prompt_dir / f"{role}.prompt.txt"
    path.write_text(prompt)
    return path


def render_command(role: str, prompt_file: Path) -> str:
    config = json.loads(CONFIG_FILE.read_text())
    if role not in config:
        raise ValidationError(f"Role '{role}' missing from {CONFIG_FILE}")
    tpl = config[role]["commandTemplate"]
    quoted = f'"{prompt_file}"'
    return tpl.replace("{prompt_file}", quoted)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare or run an AlphaPilot agent stage")
    parser.add_argument("run_id")
    parser.add_argument("role", choices=sorted(ROLE_ALIASES.keys()))
    parser.add_argument("--execute", action="store_true", help="reserved for future real execution")
    args = parser.parse_args()

    try:
        role = resolve_role(args.role)
        prompt = build_prompt(args.run_id, role)
        prompt_file = write_prompt_file(args.run_id, role, prompt)
        command = render_command(role, prompt_file)
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"role={role}")
    print(f"prompt_file={prompt_file}")
    print(f"runner_command={command}")

    if args.execute:
        print("--execute 预留，当前版本暂未直接调用 CLI。")


if __name__ == "__main__":
    main()

# Run 目录说明

本目录用于存放 AlphaPilot 每次任务执行的结构化产物，避免长期依赖聊天上下文。

## 目标

- 将任务状态落地到文件
- 支持 planner → developer → ops 的阶段交接
- 支持回溯验收、部署和阻塞原因

## 推荐目录结构

每个任务一个目录：

- `runs/<task-id>/任务说明.md`
- `runs/<task-id>/规划交接.md`
- `runs/<task-id>/开发交接.md`
- `runs/<task-id>/运维总结.md`
- `runs/<task-id>/产物清单.md`

## 模板来源

- `runs/templates/feature/`：功能任务模板
- `runs/templates/bug/`：缺陷修复模板

## 基本规则

1. 任务开始时创建 run 目录
2. planner 完成后必须写 `规划交接.md`
3. developer 完成后必须写 `开发交接.md`
4. ops 完成后必须写 `运维总结.md`
5. 群里播报是摘要，run 目录才是完整执行记录

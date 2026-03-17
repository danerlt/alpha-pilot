# 2026-03-17 Devserver Auto-Deploy Policy

## 新规则

从现在开始，每完成一个可独立验收的实现块后，执行顺序调整为：

1. 跑相关测试 / build
2. commit
3. push
4. 自动部署 dev server：`bash scripts/deploy-dev.sh`

## 目的

- 保持开发环境与最新通过测试的代码同步
- 减少“代码已 push 但 dev server 未更新”的偏差
- 让次日验收直接对应最新构建结果

## 适用范围

- 低风险工程收口
- 前后端配置中心开发
- 迁移 / 测试 / 文档类更新
- 其他已通过本地验收的实现块

## 注意

- 仍然要求先通过相关测试 / build，再部署
- 若 dev server 部署失败，应把失败原因记入 `docs/worklog/`

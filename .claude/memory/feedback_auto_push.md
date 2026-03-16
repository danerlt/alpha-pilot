---
name: auto commit push and deploy
description: After completing each implementation chunk, commit + push + auto-deploy to dev server
type: feedback
---

每次完成一个实现块后，必须依次执行：

1. `git commit` — 提交代码
2. `git push` — 立即推送到远程，无需询问用户
3. `bash scripts/deploy-dev.sh` — 自动部署到服务器开发环境（仅在 Linux 服务器上执行）

**Why:** 用户需要跨机器开发（Windows + Linux 服务器），push 确保代码在远程可用，自动部署确保开发环境始终是最新代码。

**How to apply:**
- 每次 commit 后立即 push，不需要询问
- 在 Linux 服务器上开发完成后，push 完毕再执行 `bash scripts/deploy-dev.sh`
- Windows 本地只需 push，不执行 deploy-dev.sh（因为 deploy-dev.sh 是服务器脚本）
- 生产环境（prod）只能手动执行 `bash scripts/deploy-prod.sh`，需要用户确认

**端口规则（百位加环境编号）：**
- local：backend 8000, frontend 3000（本地直接访问）
- dev：backend 8001, frontend 3001 → https://www.danerlt.top/ap-dev
- test：backend 8002, frontend 3002 → https://www.danerlt.top/ap-test
- prod：backend 8003, frontend 3003 → https://www.danerlt.top/ap

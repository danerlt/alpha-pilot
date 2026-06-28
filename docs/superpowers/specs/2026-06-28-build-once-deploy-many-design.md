# 构建一次 · 多环境部署（build-once / deploy-many）设计

> 状态：待 review。本设计取代旧"服务器拉源码 + 本地构建"范式中"部署目录即源码"的部分。
> 关联：[2026-06-27 服务器部署打通设计](2026-06-27-server-deployment-completion-design.md)、[runbook-server-bootstrap](../../runbook-server-bootstrap.md)、[deploy-ci](../../deploy-ci.md)。
> **本次仅落地 dev**；test/prod 的脚本与 compose 一并改造保持一致，但不执行部署。

## 1. 背景与现状

当前部署范式（核实自 `docker-compose.{dev-server,test,prod}.yml` / `scripts/deploy-*.sh` / `.github/workflows/`）：

- 三个 compose **全部 `build:`**（context 指向 `../backend`、`../frontend`），无一用 `image:`。
- `deploy-*.sh` = `git pull origin <branch>` + `docker compose up -d --build`：**镜像在服务器、在部署目录本地构建**。
- GitHub workflow 只跑测试门禁 + SSH 触发 deploy 脚本，**CI 不构建/不推送镜像**。

由此带来的问题：

1. **部署目录必须存源码**（要在那儿 build），部署目录与源码混在一起。
2. **无法"构建一次、多环境部署"**：每个环境各自 `--build`，同一份代码被重复构建，且无法保证 dev/test/prod 跑的是同一个二进制。
3. **回滚靠 `git reset`**，不是不可变镜像回滚，不够干净。

## 2. 目标

- **开发 / 构建 / 部署 三类目录彻底分离**，CI 永不触碰开发工作区。
- **镜像只构建一次**，以 git commit SHA 为 tag；**同一镜像沿分支流晋升**到多环境，环境差异只在 env。
- 与现有分支流 `feat → dev → test → main` 天然结合。
- 不引入外部镜像仓库（registry），用服务器本地镜像 + SHA tag。
- 保持现有 GitHub Actions 链路骨架（测试门禁 → SSH → deploy 脚本）不变，只改 deploy 脚本与 compose 的内部逻辑。

非目标（本次不做）：外部 registry（GHCR 等）、test/prod 的实际部署、nginx 域名接入（待老板提供域名后单独做）。

## 3. 目录结构

```
/workspace/alpha-pilot              ← 开发工作区（人/Claude 开发；CI 永不 git pull/reset 它）
/workspace/alpha-pilot-build        ← 唯一构建目录（CI checkout 目标 commit → docker build 出 :<sha> 镜像）
/workspace/alpha-pilot-deploy/
   ├── dev/                         ← dev 部署目录：瘦 compose(image:) + envs/dev.env + 当前 tag 记录；无源码
   ├── test/                        ← test 部署目录（预留）
   ├── prod/                        ← prod 部署目录（预留）
   └── middleware/                  ← 共享中间件 compose（常驻，独立生命周期）
```

- **构建目录唯一**：因为"构建一次"，不需要按环境分子目录。它按需 `git fetch` + `checkout` 目标 commit 来构建。
- **部署目录无源码**：只含该环境的 compose 文件（`image:` 引用）、`envs/<env>.env`、镜像 tag 记录文件。compose 文件由 deploy 脚本从构建目录按 commit 同步过来，保证 compose 与镜像版本一致。

## 4. 镜像与 tag 策略

- 镜像：`alphapilot-backend:<sha>`、`alphapilot-frontend:<sha>`。**scheduler 复用 backend 同一镜像**（仅启动命令不同）。
- `<sha>` = 目标 commit 的 `git rev-parse --short=12 HEAD`（纯 hex，合法 docker tag）。
- **inspect-or-build**：部署任一环境前 `docker image inspect alphapilot-backend:<sha> >/dev/null 2>&1 || (在构建目录 build)`。
  - 代码总是先过 dev：到 test/prod 时该 SHA 镜像已存在 → 直接复用，**自动满足"只构建一次"**。
  - dev 是唯一通常触发真正 build 的环境。

## 5. 与 GitHub 的结合（分支流晋升）

```
push dev   → CI 测试门禁 → SSH → deploy-dev.sh   : 构建目录 build :<sha>(若无) → 部署到 dev
push test  → CI 测试门禁 → SSH → deploy-test.sh  : :<sha> 已存在 → 复用 → 部署到 test     (不重复 build)
push main  → CI 测试门禁 → SSH → deploy-prod.sh  : 复用 → 部署到 prod（GitHub Environment 审批门）
```

- 同一 commit 沿 `dev → test → main` 推进，**SHA 不变、镜像复用一次构建**。
- "dev 比 test/prod 新"自然成立：dev 已部署较新的 SHA，test/prod 仍跑此前验证过的 SHA，直到对应分支被推进。
- workflow 文件（`deploy-{dev,test,prod}.yml` / `_deploy.yml`）**逻辑不变**：仍是测试门禁 + SSH 执行 deploy 脚本；改动都在 deploy 脚本内部。
- GitHub Secret：`DEPLOY_DIR_DEV = /workspace/alpha-pilot-deploy/dev`（test/prod 同理）。构建目录路径作为 deploy 脚本内部常量（不需 secret）。

## 6. compose 改造

各环境 compose（`docker-compose.{dev-server,test,prod}.yml`）：

- `build: {context, dockerfile}` → `image: alphapilot-backend:${IMAGE_TAG}` / `alphapilot-frontend:${IMAGE_TAG}`。
- 删除 build context 依赖 → compose 文件可独立于源码存在于部署目录。
- 其余不变：scheduler 仍 `image: backend:${IMAGE_TAG}` + `command: python scripts/start_scheduler.py`；环境变量、`ap-shared` 外部网络、端口映射（dev 8001/3001）保持。
- `${IMAGE_TAG}` 由 deploy 脚本通过 shell 环境注入（`IMAGE_TAG=<sha> docker compose ... up -d`）。

## 7. 部署脚本改造（以 deploy-dev.sh 为例）

常量：`DEV_DEPLOY_DIR`、`BUILD_DIR=/workspace/alpha-pilot-build`、`MIDDLEWARE_DIR`、`ENV_FILE=<deploy>/envs/dev.env`。

步骤：

1. **确保中间件在**：`docker compose -f $MIDDLEWARE_DIR/docker-compose.middleware.yml up -d` + 等 `pg_isready` + 建库兜底（`alphapilot_dev`）。
2. **解析目标 SHA**：在构建目录 `git fetch origin dev && git checkout -q origin/dev`（detached），`SHA=$(git rev-parse --short=12 HEAD)`。
3. **inspect-or-build**：两个镜像 `docker image inspect …:$SHA || docker build -t …:$SHA -f docker/Dockerfile.<x> <ctx>`（在构建目录）。
4. **同步 compose**：从构建目录把 `docker-compose.dev-server.yml` 拷到部署目录（保证 compose 与该 SHA 一致）。
5. **记录回滚点**：把部署目录现有 `current.tag` 存为 `last-good.tag`（首次部署则跳过）。
6. **起栈**：`IMAGE_TAG=$SHA docker compose -f <deploy>/docker-compose.dev-server.yml --env-file $ENV_FILE up -d`，写 `current.tag=$SHA`。
7. **迁移（单点）**：`docker compose ... exec -T backend python scripts/upgrade_db.py`。
8. **健康三检**：API `/health` + scheduler 日志 `APScheduler started` + （冒烟）。
9. **失败回滚**：若有 `last-good.tag` → `IMAGE_TAG=<last-good> docker compose up -d` 回到上一个可用镜像（**不动 git**）。首次部署无回滚点则报错停下。

test/prod 脚本结构相同，差异：第 2 步 checkout `origin/test` / `origin/main`；第 3 步预期镜像已存在（不存在仍兜底 build）；env 用各自文件；prod 走审批门。

## 8. 迁移与回滚

- **迁移**：在部署目录用该 SHA 镜像 `exec backend upgrade_db.py`；各环境各自迁移自己的库（`alphapilot_{dev,test,prod}`，同一镜像、不同 DATABASE_URL）。
- **回滚**：基于不可变镜像 —— 回到 `last-good.tag` 对应镜像并 `up -d`。比 `git reset` 干净、可预期。注意：迁移不自动回退（与现状一致；schema 变更需向后兼容，这点沿用既有约定）。

## 9. 旧资源清理（一次性）

- 旧的 `ap-dev` 4 容器（`ap-dev-postgres-1`/`redis-1`/`backend-1`/`frontend-1`，3 个月前旧范式）：**停删，保留数据卷**（`docker compose -p ap-dev down`，卷不删）。新架构数据在共享中间件 `alphapilot_dev`。
- 现有的 `/workspace/alpha-pilot-deploy/dev`（目前是完整 clone）：**改造为瘦部署目录**（移除源码，仅留 compose + `envs/dev.env` + tag 文件）。`envs/dev.env`（已含生成密钥 + 搬运的管理员配置）保留。

## 10. 本次落地范围（dev only）与验证标准

落地：

1. 建构建目录 `/workspace/alpha-pilot-build`（clone）。
2. 改 `docker-compose.dev-server.yml`（及 test/prod 同步改，保持一致）build→image。
3. 改 `deploy-dev.sh`（及 test/prod 同步改）为 build-once 逻辑。
4. 瘦化 `deploy/dev`、清理旧容器。
5. 起 dev 栈，跑健康三检。

验证（全过才算成功）：

- [ ] dev：backend + scheduler + frontend 三 service `Up`；scheduler 日志见 `APScheduler started`。
- [ ] `/health` 返回正常 envelope。
- [ ] 运行中容器镜像 tag = 当前 dev HEAD 的 SHA（`docker inspect` 确认）。
- [ ] 部署目录 `deploy/dev` 内**无源码**（只 compose + envs + tag 文件）。
- [ ] 改一行代码 push 模拟 → 重跑 deploy-dev.sh → 新 SHA 镜像构建并切换；构造一次失败 → 验证回滚到 last-good。

## 11. 待老板提供 / 确认（阻塞项）

- `envs/dev.env` 的 `LLM_API_KEY`（必填才跑通策略链）、Binance testnet 凭据（可留占位）。
- 旧 `ap-dev` 4 容器停删确认。
- 域名 + nginx 主配置位置（nginx 阶段，单独做）。
- 代码改动 commit/push 到 dev：本设计改了 compose + deploy 脚本，需 push 才能让 CI 用新逻辑。

## 12. 取舍说明

- **不用外部 registry**：服务器单机、三环境同机，本地 SHA 镜像即可满足"构建一次多处部署"，省去 registry 认证与运维。若将来多机部署，再引入 GHCR（compose 的 `image:` 只需加仓库前缀，改动小）。
- **构建目录 detached checkout**：避免在构建目录维护分支状态，纯按 commit 构建，幂等。
- **tag 用 SHA 而非环境名**：保证可追溯、可复用、可回滚；环境名 tag 会破坏"同一镜像多环境"。

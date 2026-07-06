# AlphaPilot 三环境 CI/CD 部署指南

> push 分支即自动部署。本文档说明分支模型、GitHub 配置、服务器准备。

## 1. 分支模型

```
feat-xxx ──PR──► dev ──PR──► test ──PR──► main
   │              │           │            │
(从 dev 切)    自动部署 dev  自动部署 test  部署 prod(可加审批门)
               /ap-dev       /ap-test      /ap
```

- `dev` / `test` / `main` 三条长存分支，均从 `main` 切出。
- 日常开发在 `feat-xxx`（从 `dev` 切）或直接在 `dev`，**先合并到 `dev`**。
- 流转：`feat → dev`（部署 dev 验证）→ OK → `dev → test`（部署 test 验收）→ OK → `test → main`（部署 prod）。
- 三环境共用一套中间件（`ap-postgres`/`ap-redis`），靠不同 database + Redis db 隔离（见 §2）。

## 2. 环境与端口（共享中间件 + 库隔离）

> 架构详见 [中间件 spec](superpowers/specs/2026-06-27-server-deployment-completion-design.md) 与
> [**build-once / deploy-many** spec](superpowers/specs/2026-06-28-build-once-deploy-many-design.md)：
> **一套中间件**（`ap-postgres` / `ap-redis`，常驻）被 dev/test/prod **共用**，靠不同 database + Redis db 隔离。
> 应用 compose 不含 pg/redis，加入共享 network `ap-shared`。
>
> **构建一次·多环境部署**：compose 不再 `build:`，改 `image:` 引用预构建镜像。镜像在**独立构建目录**
> 按 git SHA 构建一次（`alphapilot-backend:<sha>` backend/scheduler 共用；`alphapilot-frontend:<sha>-<env>`
> 因 basePath 构建期烘焙按环境构建），同一 commit 沿 `dev→test→main` **复用同一镜像晋升**，环境差异只在 env。
> 三类目录分离：**开发工作区**（CI 不碰）/ **构建目录**（CI fetch+build）/ **部署目录**（仅 compose+env，无源码）。

| 环境 | 触发分支 | nginx 路径 | api/前端口(127.0.0.1) | 应用 compose | env 文件 | database | Redis db |
|------|---------|-----------|----------------------|-------------|---------|----------|----------|
| dev  | `dev`  | `/ap-dev`  | 8001/3004(webapp) | `docker-compose.dev-server.yml` | `envs/dev.env`  | alphapilot_dev  | 0 |
| test | `test` | `/ap-test` | 8002/3002 | `docker-compose.test.yml`       | `envs/test.env` | alphapilot_test | 1 |
| prod | `main` | `/ap`      | 8003/3003 | `docker-compose.prod.yml`       | `envs/prod.env` | alphapilot_prod | 2 |

共享中间件 `docker-compose.middleware.yml`：`ap-postgres` 绑 `127.0.0.1:5432`、`ap-redis` 绑 `127.0.0.1:6379`（仅本机）。
应用 compose 含 **backend(API) + scheduler + 前端** 三 service（scheduler 跑定时/异步任务，缺它则不交易不监控）。
前端：dev 已切 **webapp**（Vite 新前端，`127.0.0.1:3004` → nginx `/ap-dev`，2026-07-06 起）；
test/prod 仍为 Next.js frontend，dev 验收通过后同步切换。

## 3. GitHub 配置（一次性）

### 3.1 Secrets（Settings → Secrets and variables → Actions）

三环境共用同一台服务器,因此 SSH 凭证只配一组。**`DEPLOY_DIR_*` 一律填【构建目录】**——
CI 执行 `cd $DEPLOY_DIR_<ENV> && bash scripts/deploy-<env>.sh`,脚本在构建目录里、内部部署到 `deploy/<env>`。

| Secret | 说明 |
|--------|------|
| `DEPLOY_SSH_HOST` | 服务器公网 IP 或域名 |
| `DEPLOY_SSH_USER` | 专用部署用户(建议 `deployer`,仅 docker 组,非 root) |
| `DEPLOY_SSH_KEY`  | 部署私钥整段(PEM),公钥加入 `deployer` 的 `~/.ssh/authorized_keys` |
| `DEPLOY_SSH_PORT` | [可选] SSH 端口,缺省 22 |
| `DEPLOY_DIR_DEV`  | **构建目录**绝对路径(如 `/workspace/alpha-pilot-build`) |
| `DEPLOY_DIR_TEST`  | 同构建目录(三环境共用一个构建目录) |
| `DEPLOY_DIR_PROD` | 同构建目录 |

**两把方向相反的 key**(详细步骤见 [runbook §5](runbook-server-bootstrap.md)):
- 部署 key(GitHub Actions→服务器):公钥进 `deployer` authorized_keys,私钥进 Secret `DEPLOY_SSH_KEY`。
- deployer 的 GitHub key(服务器→GitHub 拉代码):公钥加到仓库 **Deploy keys**(只读)。**漏这把 CI 会卡在 `git fetch origin` 报 `Permission denied (publickey)`。**

### 3.2 生产审批门（推荐，接 Binance mainnet）

Settings → Environments → 新建 `prod` → 勾选 **Required reviewers** 填你自己。
合并到 `main` 后，Deploy Prod 会**暂停等待你在网页点 Approve** 才真正部署。
（同理可给 `test` 也加审批门；`dev` 一般不加，直推直部署。）

> workflow 里已写 `environment: dev|test|prod`，配了 reviewer 就生效，不配就照常自动部署。

## 4. 服务器准备（一次性）

> 完整 SOP（含 deployer 用户、两把 key、逐步验证）见 [runbook-server-bootstrap.md](runbook-server-bootstrap.md)。下面是要点。

```bash
# 1) 部署用户（一次性）：仅 docker 组，非 root
useradd -m -s /bin/bash deployer && usermod -aG docker deployer
#    两把 key 见 runbook §5：部署 key(公钥→deployer authorized_keys)、deployer GitHub key(公钥→仓库 Deploy keys)

# 2) 构建目录（唯一，CI 在此 fetch+build）
git clone <repo> /workspace/alpha-pilot-build && (cd /workspace/alpha-pilot-build && git checkout dev)
#    其 origin 指向 GitHub；DEPLOY_DIR_DEV/TEST/PROD 都填这个路径

# 3) 部署目录（仅 compose+env，无源码；compose 由 deploy 脚本从构建目录同步）
mkdir -p /workspace/alpha-pilot-deploy/{dev,test,prod,middleware}
#    各放 envs/<env>.env（从 example.env 拷贝填真实密钥，不进 git；必填 APP_AUTH_SECRET_KEY/APP_CONFIG_MASTER_KEY）
#    DATABASE_URL/REDIS_URL 由 compose 指向共享中间件，无需设
chown -R deployer:deployer /workspace/alpha-pilot-build /workspace/alpha-pilot-deploy

# 4) 起共享中间件（常驻；首次自动建三库 + 创建 network ap-shared）
cd /workspace/alpha-pilot-deploy/middleware   # 放一份 docker-compose.middleware.yml
docker compose -f docker-compose.middleware.yml up -d

# 5) nginx: 把 docker/nginx/alpha-pilot.conf 的 location 块并入 HTTPS server{}
#    （/ap、/ap-test、/ap-dev 三段 + http{} 顶层 limit_req_zone / log_format）；nginx -t && systemctl reload nginx
#    证书自动续期务必配（cron 或 certbot.timer），否则会过期

# 6) Docker + docker compose 已装；DNS <PUBLIC_DOMAIN> → 本服务器
```

## 5. 工作流程速查

```bash
# 开发
git checkout dev && git checkout -b feat-xxx
# ... coding ...
git push → 提 PR 合入 dev → 自动部署 dev → 在 /ap-dev 验证

# 验收
PR: dev → test → 自动部署 test → 在 /ap-test 验收

# 上线
PR: test → main → (审批门 Approve) → 部署 prod → /ap
```

## 6. 手动触发

每个 workflow 都支持 `workflow_dispatch`：Actions 页面选对应 workflow → Run workflow。
服务器上也可直接 `bash scripts/deploy-{dev,test,prod}.sh`（prod 交互式会问确认，CI 无 TTY 自动跳过）。

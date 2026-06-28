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

> 架构详见 [spec](superpowers/specs/2026-06-27-server-deployment-completion-design.md)：
> **一套中间件**（`ap-postgres` / `ap-redis`，常驻）被 dev/test/prod **共用**，靠不同 database + Redis db 隔离。
> 应用 compose 不含 pg/redis，加入共享 network `ap-shared`。

| 环境 | 触发分支 | nginx 路径 | api/前端口(127.0.0.1) | 应用 compose | env 文件 | database | Redis db |
|------|---------|-----------|----------------------|-------------|---------|----------|----------|
| dev  | `dev`  | `/ap-dev`  | 8001/3001 | `docker-compose.dev-server.yml` | `envs/dev.env`  | alphapilot_dev  | 0 |
| test | `test` | `/ap-test` | 8002/3002 | `docker-compose.test.yml`       | `envs/test.env` | alphapilot_test | 1 |
| prod | `main` | `/ap`      | 8003/3003 | `docker-compose.prod.yml`       | `envs/prod.env` | alphapilot_prod | 2 |

共享中间件 `docker-compose.middleware.yml`：`ap-postgres` 绑 `127.0.0.1:5432`、`ap-redis` 绑 `127.0.0.1:6379`（仅本机）。
应用 compose 现含 **backend(API) + scheduler + frontend** 三 service（scheduler 跑定时/异步任务，缺它则不交易不监控）。

## 3. GitHub 配置（一次性）

### 3.1 Secrets（Settings → Secrets and variables → Actions）

三环境共用同一台服务器，因此 SSH 凭证只配一组：

| Secret | 说明 |
|--------|------|
| `DEPLOY_SSH_HOST` | 服务器 IP 或域名 |
| `DEPLOY_SSH_USER` | SSH 登录用户名 |
| `DEPLOY_SSH_KEY`  | SSH **私钥**整段（PEM），对应公钥加入服务器 `~/.ssh/authorized_keys` |
| `DEPLOY_SSH_PORT` | [可选] SSH 端口，缺省 22 |
| `DEPLOY_DIR_DEV`  | dev 分支 clone 在服务器上的绝对路径 |
| `DEPLOY_DIR_TEST`  | test 分支 clone 在服务器上的绝对路径 |
| `DEPLOY_DIR_PROD` | main 分支 clone 在服务器上的绝对路径 |

生成专用部署密钥：
```bash
ssh-keygen -t ed25519 -C "alphapilot-deploy" -f deploy_key
# deploy_key.pub  → 服务器 authorized_keys
# deploy_key      → 粘贴进 DEPLOY_SSH_KEY secret
```

### 3.2 生产审批门（推荐，接 Binance mainnet）

Settings → Environments → 新建 `prod` → 勾选 **Required reviewers** 填你自己。
合并到 `main` 后，Deploy Prod 会**暂停等待你在网页点 Approve** 才真正部署。
（同理可给 `test` 也加审批门；`dev` 一般不加，直推直部署。）

> workflow 里已写 `environment: dev|test|prod`，配了 reviewer 就生效，不配就照常自动部署。

## 4. 服务器准备（一次性）

```bash
# 1) 起共享中间件（仅一次，常驻；后续应用重部署不动它）
cd <某个 clone>/docker && docker compose -f docker-compose.middleware.yml up -d
#    首次启动（数据卷为空）自动建 alphapilot_dev / alphapilot_test / alphapilot_prod 三库
#    并创建共享 docker network: ap-shared

# 2) 三个独立 clone（各自 checkout 对应分支）
git clone <repo> <DEPLOY_DIR_DEV>  && (cd <DEPLOY_DIR_DEV>  && git checkout dev)
git clone <repo> <DEPLOY_DIR_TEST> && (cd <DEPLOY_DIR_TEST> && git checkout test)
git clone <repo> <DEPLOY_DIR_PROD> && (cd <DEPLOY_DIR_PROD> && git checkout main)
# 上述三个路径分别填进 DEPLOY_DIR_DEV / _TEST / _PROD secret

# 3) 各 clone 放好 env 文件（从 example.env 拷贝填真实密钥, 不进 git）
#    <DEPLOY_DIR_DEV>/envs/dev.env   等；必填 APP_AUTH_SECRET_KEY / APP_CONFIG_MASTER_KEY
#    DATABASE_URL/REDIS_URL 已由各 compose 指向共享中间件，env 里无需再设

# 4) nginx: 把 docker/nginx/alpha-pilot.conf 的 location 块并入 HTTPS server{}
#    （/ap、/ap-test、/ap-dev 三段 + http{} 顶层 limit_req_zone / log_format）
#    reload: nginx -t && systemctl reload nginx

# 5) Docker + docker compose 已装；DNS <PUBLIC_DOMAIN> → 本服务器
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

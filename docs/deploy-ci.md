# AlphaPilot 三环境 CI/CD 部署指南

> push 分支即自动部署。本文档说明分支模型、GitHub 配置、服务器准备。

## 1. 分支模型

```
feat-xxx ──PR──► dev ──PR──► uat ──PR──► main
   │              │           │           │
(从 dev 切)    自动部署 dev  自动部署 uat  部署 prod(可加审批门)
               /ap-dev       /ap-uat       /ap
```

- `dev` / `uat` / `main` 三条长存分支，均从 `main` 切出。
- 日常开发在 `feat-xxx`（从 `dev` 切）或直接在 `dev`，**先合并到 `dev`**。
- 流转：`feat → dev`（部署 dev 验证）→ OK → `dev → uat`（部署 uat 验收）→ OK → `uat → main`（部署 prod）。

## 2. 环境与端口（沿用"百位加环境号"约定）

| 环境 | 触发分支 | nginx 路径 | 后端/前端口 | compose | env 文件 | 数据库 |
|------|---------|-----------|------------|---------|---------|--------|
| dev  | `dev`  | `/ap-dev` | 8001/3001 | `docker/docker-compose.dev-server.yml` | `envs/dev.env`  | alphapilot_dev |
| uat  | `uat`  | `/ap-uat` | 8002/3002 | `docker/docker-compose.uat.yml`        | `envs/uat.env`  | alphapilot_uat |
| prod | `main` | `/ap`     | 8003/3003 | `docker/docker-compose.prod.yml`       | `envs/prod.env` | alphapilot_prod |

PostgreSQL/Redis 内部端口：dev 5433/6380 · uat 5434/6381 · prod 5435/6382（均绑 `127.0.0.1`）。

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
| `DEPLOY_DIR_UAT`  | uat 分支 clone 在服务器上的绝对路径 |
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
（同理可给 `uat` 也加审批门；`dev` 一般不加，直推直部署。）

> workflow 里已写 `environment: dev|uat|prod`，配了 reviewer 就生效，不配就照常自动部署。

## 4. 服务器准备（一次性）

```bash
# 1) 三个独立 clone（各自 checkout 对应分支）
git clone <repo> /opt/alphapilot/dev  && (cd /opt/alphapilot/dev  && git checkout dev)
git clone <repo> /opt/alphapilot/uat  && (cd /opt/alphapilot/uat  && git checkout uat)
git clone <repo> /opt/alphapilot/prod && (cd /opt/alphapilot/prod && git checkout main)
# 上述三个路径分别填进 DEPLOY_DIR_DEV / _UAT / _PROD

# 2) 各 clone 放好 env 文件（从 example.env 拷贝填真实密钥, 不进 git）
#    /opt/alphapilot/dev/envs/dev.env
#    /opt/alphapilot/uat/envs/uat.env
#    /opt/alphapilot/prod/envs/prod.env

# 3) nginx: 把 docker/nginx/alpha-pilot.conf 的 location 块并入你的 HTTPS server{}
#    （含 /ap、/ap-uat、/ap-dev 三段 + http{} 顶层的 limit_req_zone / log_format）
#    reload: nginx -t && systemctl reload nginx

# 4) Docker + docker compose 已装；DNS www.danerlt.top → 本服务器
```

## 5. 工作流程速查

```bash
# 开发
git checkout dev && git checkout -b feat-xxx
# ... coding ...
git push → 提 PR 合入 dev → 自动部署 dev → 在 /ap-dev 验证

# 验收
PR: dev → uat → 自动部署 uat → 在 /ap-uat 验收

# 上线
PR: uat → main → (审批门 Approve) → 部署 prod → /ap
```

## 6. 手动触发

每个 workflow 都支持 `workflow_dispatch`：Actions 页面选对应 workflow → Run workflow。
服务器上也可直接 `bash scripts/deploy-{dev,uat,prod}.sh`（prod 交互式会问确认，CI 无 TTY 自动跳过）。

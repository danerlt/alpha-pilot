# 服务器部署引导 Runbook（给服务器上的 Claude Code 执行）

> 本文件是一份**可执行 SOP**：服务器上的 Claude Code 照此把 AlphaPilot 的 dev/test/prod 部署打通。
> 架构见 [部署 spec](superpowers/specs/2026-06-27-server-deployment-completion-design.md) 与 [deploy-ci.md](deploy-ci.md)。

## 给执行者（服务器 Claude Code）的总原则

1. **先做 dev，验证通过再碰 test，最后才 prod**。prod 接 Binance mainnet，**必须老板手动确认**才执行。
2. **绝不编造或读取真实密钥**。需要真实值的地方（Binance/LLM key、SSH、域名）一律**停下来让老板填**。
   - 例外：`APP_AUTH_SECRET_KEY` / `APP_CONFIG_MASTER_KEY` 这两个是随机密钥，**可以用命令现场生成并写入**（见 §3）。
3. **不把任何 env 文件内容打印到对话或日志**（envs/ 在本仓库 CLAUDE.md 黑名单内；只创建/写入，不回显）。
4. 每个阶段执行完**做验证检查**，失败就停下报告，不要硬继续。
5. 路径有疑问就问老板，不要假设（如 clone 目录、域名）。

---

## 阶段 0：前置检查

```bash
docker --version && docker compose version      # 确认 Docker + compose 已装
git --version
# 确认当前在 alpha-pilot 仓库内，且已拉到最新 dev
git rev-parse --show-toplevel
git fetch origin && git log --oneline -1 origin/dev
```

若 Docker 未装 → 停，让老板装。

---

## 阶段 1：共享中间件（一次性，常驻）

dev/test/prod 共用这一套 PG+Redis，靠不同 database + Redis db 隔离。

```bash
cd <仓库>/docker
docker compose -f docker-compose.middleware.yml up -d
```

**验证**（必须全过）：

```bash
# 1) 容器健康
docker ps --filter name=ap-postgres --filter name=ap-redis --format "{{.Names}} {{.Status}}"
# 2) 三个业务库已建（首次启动数据卷为空时由 init 脚本自动建）
docker exec ap-postgres psql -U alphapilot -tAc \
  "SELECT datname FROM pg_database WHERE datname LIKE 'alphapilot_%' ORDER BY 1"
#   期望输出: alphapilot_dev / alphapilot_prod / alphapilot_test
# 3) 共享网络存在
docker network ls --filter name=ap-shared --format "{{.Name}}"
# 4) Redis 通
docker exec ap-redis redis-cli ping     # 期望 PONG
```

> 若中间件卷**已存在**（非首次）导致三库没自动建：手动建缺的库
> `docker exec ap-postgres psql -U alphapilot -c "CREATE DATABASE alphapilot_dev"`（test/prod 同理）。

---

## 阶段 2：dev 应用 clone + env

> **[需老板确认]** dev 应用 clone 的目标目录（下文用 `<DEV_DIR>` 代指，例如 `~/alphapilot/dev`）。
> 这个路径之后要填进 GitHub Secret `DEPLOY_DIR_DEV`。

```bash
# 若尚未单独 clone dev 分支目录:
git clone <仓库地址> <DEV_DIR> && cd <DEV_DIR> && git checkout dev

# 准备 env（从模板拷贝；真实值待填）
cd <DEV_DIR>
cp example.env envs/dev.env       # envs/ 已 gitignore，不会进 git
```

**填 `envs/dev.env`**（执行者按以下规则处理，逐项确认）：

- `TRADING_MODE=testnet`（dev 用测试盘）
- `APP_AUTH_SECRET_KEY` ← **现场生成并写入**：`python3 -c "import secrets;print(secrets.token_urlsafe(48))"`
- `APP_CONFIG_MASTER_KEY` ← **现场生成并写入**：`python3 -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"`
- `BINANCE_API_KEY` / `BINANCE_API_SECRET` ← **[需老板填]** testnet 凭据（无则留空，启动后从前端运行时配置页填也可）
- `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` ← **[需老板填]**
- `DEFAULT_ADMIN_EMAIL` / `DEFAULT_ADMIN_PASSWORD` ← **[需老板填]**（首登管理员；dev 可设，prod 勿用固定密码）
- `DATABASE_URL` / `REDIS_URL` **无需设**——compose 已指向共享中间件（alphapilot_dev / db0）

> 写入这些值时**不要把文件内容回显到对话**。生成的两个随机密钥也不要打印。

---

## 阶段 3：起 dev 应用栈 + 验证

```bash
cd <DEV_DIR>
bash scripts/deploy-dev.sh
```

该脚本会：确保中间件在 → 建库兜底 → `git pull origin dev` → 起 **backend + scheduler + frontend** → 单点迁移 → 健康三检 → 失败自动回滚。

**验证**（必须全过）：

```bash
cd <DEV_DIR>/docker
# 1) 三个应用 service 都在跑
docker compose -f docker-compose.dev-server.yml ps --format "{{.Service}} {{.Status}}"
#    期望 backend / scheduler / frontend 均 Up
# 2) scheduler 确实在跑定时任务（关键！缺它=不交易不监控）
docker compose -f docker-compose.dev-server.yml logs scheduler --tail=20 | grep "APScheduler started"
# 3) API 健康
docker compose -f docker-compose.dev-server.yml exec -T backend \
  python -c "import urllib.request;print(urllib.request.urlopen('http://localhost:8000/health').read())"
```

任一失败 → 打印对应 service 日志，停下报告老板。

---

## 阶段 4：nginx（一次性）

把 `docker/nginx/alpha-pilot.conf` 的 location 块并入老板的 HTTPS `server{}`，
http{} 顶层补 `limit_req_zone` / `log_format`（文件内注释有说明）。

> **[需老板确认]** 域名与现有 nginx 主配置位置。执行者**不要猜域名**，问老板。

```bash
nginx -t && systemctl reload nginx
# 验证（用老板提供的域名占位 <DOMAIN>）:
curl -sS https://<DOMAIN>/ap-dev/api/health
```

---

## 阶段 5：GitHub 自动部署（老板在 GitHub 网页操作，非服务器）

> 这部分**执行者只需提醒老板**，不在服务器上做：

在 GitHub → Settings → Secrets and variables → Actions 配：

| Secret | 值 |
|--------|----|
| `DEPLOY_SSH_HOST` | 服务器 IP |
| `DEPLOY_SSH_PORT` | SSH 端口 |
| `DEPLOY_SSH_USER` | SSH 用户名 |
| `DEPLOY_SSH_KEY`  | 专用部署私钥 PEM（公钥已加服务器 `~/.ssh/authorized_keys`） |
| `DEPLOY_DIR_DEV`  | `<DEV_DIR>` |
| `DEPLOY_DIR_TEST` | test 应用 clone 路径 |
| `DEPLOY_DIR_PROD` | prod 应用 clone 路径 |

配好后，老板每次 `git push origin dev` → GitHub Actions 自动跑测试门禁 + SSH 部署 dev。

生成部署专用密钥（在老板自己的机器上）：
```bash
ssh-keygen -t ed25519 -C "alphapilot-deploy" -f deploy_key
# deploy_key.pub → 服务器 ~/.ssh/authorized_keys
# deploy_key     → GitHub Secret DEPLOY_SSH_KEY
```

---

## 阶段 6：test / prod（dev 验证通过后再做）

- **test**：重复阶段 2-3，把 `<DEV_DIR>`→test clone、`dev.env`→`test.env`、`deploy-dev.sh`→`deploy-test.sh`、
  compose 用 `docker-compose.test.yml`（自动连 alphapilot_test / redis db1）。
- **prod**：**[必须老板手动确认]** 接 Binance mainnet。
  - `prod.env` 的 `TRADING_MODE=mainnet`、填真实主网凭据。
  - 建议先在 GitHub Environments → prod 配 Required reviewers（审批门）。
  - 服务器手动 `bash scripts/deploy-prod.sh`（会交互确认），或 push main 走审批门。

---

## 验收清单（"部署打通"达成）

- [ ] 中间件 `ap-postgres`/`ap-redis` 健康，三库已建，`ap-shared` 网络在。
- [ ] dev：backend + scheduler + frontend 三 service Up；scheduler 日志见 `APScheduler started`。
- [ ] `https://<DOMAIN>/ap-dev/api/health` 返回正常 envelope。
- [ ] GitHub Secrets 配齐；`git push origin dev` 触发 Actions 自动测试 + 部署。
- [ ] 全程无真实凭据进 git；env 真实值只在服务器 `envs/`、SSH 只在 GitHub Secrets。

## 出问题时

- scheduler 没 `APScheduler started` → 看 `logs scheduler`，多半是 env 缺 `APP_AUTH_SECRET_KEY`/`APP_CONFIG_MASTER_KEY`（`_validate_secrets` 拒绝启动）。
- backend 连不上 DB → 确认中间件在跑、`ap-shared` 网络、env 没覆盖掉 compose 的 DATABASE_URL。
- 迁移失败 → `docker compose ... exec -T backend python scripts/upgrade_db.py` 单独跑看报错。

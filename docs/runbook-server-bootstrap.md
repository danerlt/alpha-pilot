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

## 阶段 5：部署用户 + GitHub 自动部署

> **架构已切换为 build-once / deploy-many**（见 [spec](superpowers/specs/2026-06-28-build-once-deploy-many-design.md)）：
> 镜像在【构建目录】`alpha-pilot-build` 按 git SHA 构建一次，部署目录只放 compose+env。
> CI 执行 `cd $DEPLOY_DIR_<ENV> && bash scripts/deploy-<env>.sh`，脚本在构建目录里、内部部署到 `deploy/<env>`。
> 因此 **`DEPLOY_DIR_*` 一律填【构建目录】路径**（三环境共用一个构建目录）。

### 5A. 服务器侧：建专用部署用户 + 两把 key（执行者在服务器做）

用专用非 root 用户 `deployer` 跑部署（最小权限：只需 docker 组）。涉及**两把方向相反的 key**，别混：

| key | 方向 | 公钥放哪 | 私钥放哪 |
|-----|------|---------|---------|
| 部署 key | GitHub Actions → 服务器 | `deployer` 的 `~/.ssh/authorized_keys` | GitHub Secret `DEPLOY_SSH_KEY` |
| deployer 的 GitHub key | 服务器 → GitHub（拉代码） | GitHub 仓库 **Deploy keys**（只读） | 服务器 `/home/deployer/.ssh/id_ed25519` |

```bash
# 1) 建用户 + 加 docker 组（跑部署只需 docker 组，勿加 root/sudo）
useradd -m -s /bin/bash deployer
usermod -aG docker deployer
# 2) 部署 key（GitHub Actions → 服务器）：在服务器或自己机器生成，公钥进 deployer
ssh-keygen -t ed25519 -C "alphapilot-deploy" -f ~/.ssh/alphapilot_deploy_key -N ""
install -d -m700 -o deployer -g deployer /home/deployer/.ssh
cp ~/.ssh/alphapilot_deploy_key.pub /home/deployer/.ssh/authorized_keys
chmod 600 /home/deployer/.ssh/authorized_keys && chown -R deployer:deployer /home/deployer/.ssh
#   私钥 ~/.ssh/alphapilot_deploy_key → 贴到 GitHub Secret DEPLOY_SSH_KEY（不要回显/进 git）
# 3) deployer 的 GitHub key（服务器 → GitHub 拉代码）
sudo -u deployer ssh-keygen -t ed25519 -C "alphapilot-deployer-github" -f /home/deployer/.ssh/id_ed25519 -N ""
ssh-keyscan -t ed25519 github.com >> /home/deployer/.ssh/known_hosts
#   公钥 /home/deployer/.ssh/id_ed25519.pub → 加到 GitHub 仓库 Deploy keys（见 5B，不勾 write）
# 4) 构建/部署目录归属 deployer
chown -R deployer:deployer <构建目录> <部署目录根>   # 如 /workspace/alpha-pilot-build /workspace/alpha-pilot-deploy
# 5) 自检
id deployer                                          # 应含 docker 组
su - deployer -c 'docker ps >/dev/null && echo DOCKER_OK'
su - deployer -c 'GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes" git ls-remote <构建目录的 origin> -h refs/heads/dev'  # 加完 Deploy key 后应返回 SHA
```

### 5B. GitHub 网页侧（老板操作）

**① Deploy keys**（仓库 → Settings → Deploy keys → Add deploy key，**不勾** Allow write）：
贴 `deployer` 的公钥 `/home/deployer/.ssh/id_ed25519.pub`。没这把，CI 部署会卡在 `git fetch origin`（`Permission denied (publickey)`）。

**② Secrets**（仓库 → Settings → Secrets and variables → Actions）：

| Secret | 值 |
|--------|----|
| `DEPLOY_SSH_HOST` | 服务器公网 IP / 域名 |
| `DEPLOY_SSH_PORT` | SSH 端口（默认 22 可不建） |
| `DEPLOY_SSH_USER` | `deployer` |
| `DEPLOY_SSH_KEY`  | 部署私钥全文（`~/.ssh/alphapilot_deploy_key`） |
| `DEPLOY_DIR_DEV`  | **构建目录**路径（如 `/workspace/alpha-pilot-build`） |
| `DEPLOY_DIR_TEST` | 同构建目录路径 |
| `DEPLOY_DIR_PROD` | 同构建目录路径 |

配好后，`git push origin dev` → GitHub Actions 直接 SSH（`deployer@HOST`）进服务器 → 构建目录 `git fetch origin` + build-once + 部署 dev。
（CI 不跑测试门禁——单测/构建在本地提交前完成；`make test` + 前端 build 自查后再 push。）

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
- [ ] `deployer` 用户建好（仅 docker 组）；`DOCKER_OK` + 能 `git ls-remote` GitHub。
- [ ] GitHub **Deploy key**（deployer 公钥）已加；**Secrets** 配齐（`DEPLOY_SSH_USER=deployer`、`DEPLOY_DIR_*`=构建目录）。
- [ ] `git push origin dev` 触发 Actions 直接部署（无测试门禁），CI 绿。
- [ ] 全程无真实凭据进 git；env 真实值只在服务器 `envs/`、私钥只在服务器与 GitHub Secrets。

## 出问题时

- CI 部署卡在 `git fetch origin` 报 `Permission denied (publickey)` → deployer 的公钥没加到 GitHub **Deploy keys**（注意是 Deploy keys 区，不是 Secrets）。
- CI SSH 连不上 → 检查 `DEPLOY_SSH_HOST/PORT/USER`、`DEPLOY_SSH_KEY` 私钥全文、服务器放通公网 SSH、`deployer` 的 `authorized_keys` 有部署公钥。
- `dubious ownership in repository` → 构建/部署目录属主不是运行用户；`chown -R deployer:deployer` 或 `git config --global --add safe.directory <repo>`。
- scheduler crash-loop（`No module named src`）→ 后端镜像须有 `ENV PYTHONPATH=/app`（见 Dockerfile.backend）。
- scheduler 没 `APScheduler started` → 看 `logs scheduler`，多半是 env 缺 `APP_AUTH_SECRET_KEY`/`APP_CONFIG_MASTER_KEY`（`_validate_secrets` 拒绝启动）。
- backend 连不上 DB → 确认中间件在跑、`ap-shared` 网络、env 没覆盖掉 compose 的 DATABASE_URL。
- 迁移失败 → `docker compose ... exec -T backend python scripts/upgrade_db.py` 单独跑看报错。

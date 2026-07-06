# 服务器部署引导 Runbook（给服务器上的 Claude Code 执行）

> 本文件是一份**可执行 SOP**：服务器上的 Claude Code 照此把 AlphaPilot 的 dev/test/prod 部署打通。
> 架构见 [deploy-ci.md](deploy-ci.md)（分支模型/GitHub 配置）与
> [build-once spec](superpowers/specs/2026-06-28-build-once-deploy-many-design.md)。
> 最后更新：2026-07-06（配置分层 + webapp 服务 + 目录模型对齐 deploy_common.sh）。

## 给执行者（服务器 Claude Code）的总原则

1. **先做 dev，验证通过再碰 test，最后才 prod**。prod 接 Binance mainnet，**必须老板手动确认**才执行。
2. **绝不编造或读取真实密钥**。需要真实值的地方（域名、SSH、管理员密码）一律**停下来让老板填**。
   - 例外：`APP_AUTH_SECRET_KEY` / `APP_CONFIG_MASTER_KEY` 是随机密钥，**可以现场生成并写入**（见阶段 2）。
   - **Binance / LLM Key 不进 env**（配置分层，2026-07-06 起）：部署完成后由老板在**前端设置页**配置，
     Fernet 加密存 DB；env 里对应字段留空即可（缺 LLM Key 时自动回退 Mock 恒 HOLD，不误下单）。
3. **不把任何 env 文件内容打印到对话或日志**（只创建/写入，不回显；生成的随机密钥也不打印）。
4. 每个阶段执行完**做验证检查**，失败就停下报告，不要硬继续。
5. 路径/域名有疑问就问老板，不要假设。

## 目录模型（build-once / deploy-many，三类目录分离）

| 目录 | 路径（默认约定） | 内容 | 谁写 |
|------|----------------|------|------|
| 构建目录（唯一） | `/workspace/alpha-pilot-build` | 完整 git clone；CI/手动部署在此 fetch + docker build | deploy 脚本 |
| 部署目录 | `/workspace/alpha-pilot-deploy/{dev,test,prod}` | 仅 `docker/<compose>.yml`（脚本自动同步）+ `envs/<env>.env` | deploy 脚本 + 老板(env) |
| 中间件目录 | `/workspace/alpha-pilot-deploy/middleware` | `docker-compose.middleware.yml` 一份 | 一次性 |

部署脚本 `scripts/deploy-<env>.sh`（内部 `scripts/lib/deploy_common.sh::run_deploy`）在**构建目录里执行**，
默认 `DEPLOY_DIR=/workspace/alpha-pilot-deploy/<env>`（可用环境变量覆盖）。它自动完成 7 步：
①确保中间件健康+幂等建库 → ②`git fetch` + checkout 目标 commit → ③按 SHA inspect-or-build 镜像
（`alphapilot-backend:<sha>` 跨环境复用；`alphapilot-frontend:<sha>-<env>` basePath 烘焙 /
`alphapilot-webapp:<sha>` 零烘焙，均仅当目标 compose 引用了该服务才构建）→
④同步 compose 到部署目录 → ⑤记录回滚点+起栈 → ⑥容器内 `python scripts/upgrade_db.py` 迁移 →
⑦健康三检（API `/health` + scheduler running 非 crash-loop + 启动标记），**任一步失败自动回滚到 `last-good.tag`**。

## 环境速查

| 环境 | 分支 | nginx 路径 | api / 前端（127.0.0.1） | 前端实现 | compose | database | Redis db |
|------|------|-----------|------------------------|---------|---------|----------|----------|
| dev  | dev  | `/ap-dev` | 8001 / **3004** | **webapp**（Vite 新前端） | docker-compose.dev-server.yml | alphapilot_dev | 0 |
| test | test | `/ap-test` | 8002 / 3002 | frontend（Next.js 老前端） | docker-compose.test.yml | alphapilot_test | 1 |
| prod | main | `/ap` | 8003 / 3003 | frontend（Next.js 老前端） | docker-compose.prod.yml | alphapilot_prod | 2 |

> 2026-07-06 起 dev 前端已切换为 webapp 直接挂 `/ap-dev`（老 Next.js frontend 从 dev 下线）；
> dev 验收通过后 test/prod 同样切换（复制 webapp service 块 + nginx 改指剥前缀转发）。

---

## 阶段 0：前置检查

```bash
docker --version && docker compose version      # 确认 Docker + compose 已装
git --version
nproc && free -h && df -h /                     # 资源心里有数（build 需 ~2G 内存）
```

若 Docker 未装 → 停，让老板装。

---

## 阶段 1：目录 + 共享中间件（一次性，常驻）

```bash
# 1) 构建目录（唯一；三环境共用）。仓库地址问老板或用已配好的 deployer GitHub key
git clone <仓库地址> /workspace/alpha-pilot-build
cd /workspace/alpha-pilot-build && git checkout dev

# 2) 部署目录骨架
mkdir -p /workspace/alpha-pilot-deploy/{dev,test,prod}/envs /workspace/alpha-pilot-deploy/middleware

# 3) 中间件 compose 放到位并起栈（dev/test/prod 共用一套 PG+Redis，靠 database + Redis db 隔离）
cp /workspace/alpha-pilot-build/docker/docker-compose.middleware.yml /workspace/alpha-pilot-deploy/middleware/
cd /workspace/alpha-pilot-deploy/middleware
docker compose -f docker-compose.middleware.yml up -d
```

**验证**（必须全过）：

```bash
docker ps --filter name=ap-postgres --filter name=ap-redis --format "{{.Names}} {{.Status}}"   # 两容器 healthy
docker exec ap-postgres psql -U alphapilot -tAc \
  "SELECT datname FROM pg_database WHERE datname LIKE 'alphapilot_%' ORDER BY 1"
#   期望: alphapilot_dev / alphapilot_prod / alphapilot_test（首启由 init 脚本自动建）
docker network ls --filter name=ap-shared --format "{{.Name}}"                                 # ap-shared
docker exec ap-redis redis-cli ping                                                            # PONG
```

> 若中间件卷**已存在**（非首次）导致三库没自动建：`docker exec ap-postgres createdb -U alphapilot alphapilot_dev`
> （test/prod 同理；deploy 脚本也有幂等建库兜底）。

---

## 阶段 2：dev 的 env（配置分层：只放基础设施）

env 文件位置 = **部署目录**下：`/workspace/alpha-pilot-deploy/dev/envs/dev.env`。

```bash
cp /workspace/alpha-pilot-build/example.env /workspace/alpha-pilot-deploy/dev/envs/dev.env
```

**填写规则**（逐项处理，不回显内容）：

| 字段 | 怎么填 |
|------|--------|
| `TRADING_MODE` | `testnet`（dev 用测试盘） |
| `APP_AUTH_SECRET_KEY` | **现场生成**：`python3 -c "import secrets;print(secrets.token_urlsafe(48))"` |
| `APP_CONFIG_MASTER_KEY` | **现场生成**：`docker run --rm alphapilot-backend:latest python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"`（或本机有 cryptography 时直接 python3） |
| `DEFAULT_ADMIN_EMAIL` / `DEFAULT_ADMIN_PASSWORD` | **[需老板填]** 首登管理员（dev 可设；prod 勿用固定密码） |
| `BINANCE_API_KEY/SECRET`、`LLM_*` | **留空**——部署后走前端设置页存 DB（DB 值优先于 env） |
| `DATABASE_URL` / `REDIS_URL` | **无需设**——compose 已指向共享中间件（alphapilot_dev / db0） |
| 风控参数 `MAX_*` | 模板默认即可 |

> `APP_CONFIG_MASTER_KEY` 是解密 DB 内业务密钥（Binance/LLM）的根，丢了 DB 里的密钥全部作废——
> 让老板把两个生成的密钥**另行离线备份**（Claude 不保存不回显）。

---

## 阶段 3：首次部署 dev + 验证

```bash
cd /workspace/alpha-pilot-build
bash scripts/deploy-dev.sh          # 7 步全自动，失败自动回滚（首次无回滚点则直接失败退出）
```

**验证**（必须全过）：

```bash
# 1) 三个 service 都在跑（backend / scheduler / webapp）
docker ps --filter name=ap-dev --format "{{.Names}} {{.Status}}"
# 2) API + webapp 健康（宿主机侧）
curl -sS http://127.0.0.1:8001/health
curl -sSI http://127.0.0.1:3004/ | head -1        # HTTP 200
# 3) scheduler 启动标记 + 运行时配置从 DB 加载（配置分层生效的证据）
docker logs $(docker ps -qf name=ap-dev-scheduler) 2>&1 | grep -E "APScheduler started|runtime settings"
#    期望含 "APScheduler started: strategy_loop=..."；配置过设置页后还会有 "runtime settings loaded from DB"
# 4) backend 无秘钥校验报错（InsecureSecretError 出现 = env 两个 APP_* 密钥没填对）
docker logs $(docker ps -qf name=ap-dev-backend) --tail 30
```

任一失败 → 打印对应 service 日志，停下报告老板。

---

## 阶段 4：nginx（一次性）

把 `docker/nginx/alpha-pilot.conf` 的 location 块并入老板的 HTTPS `server{}`：
`/ap`、`/ap-test`、`/ap-dev`（页面段指向 webapp 127.0.0.1:3004，带斜杠剥前缀）三段 +
http{} 顶层 `limit_req_zone` / `log_format`（文件头注释有说明）。

> **[需老板确认]** 域名与现有 nginx 主配置位置。执行者**不要猜域名**。
> 若服务器上已并入过旧版 conf：`/ap-dev` 页面段的 proxy_pass 要从 3001 改为 `http://127.0.0.1:3004/`
> （注意结尾斜杠），并删掉旧的 `/ap-dev-next` 段（如有）。

```bash
nginx -t && systemctl reload nginx
# 验证（<DOMAIN> 用老板提供的域名）:
curl -sS https://<DOMAIN>/ap-dev/api/health      # 后端 envelope
curl -sSI https://<DOMAIN>/ap-dev/ | head -3     # webapp 200
```

---

## 阶段 5：业务配置（老板在浏览器操作，Claude 只引导）

1. 浏览器打开 `https://<DOMAIN>/ap-dev/` → 用 `DEFAULT_ADMIN_EMAIL/PASSWORD` 登录。
2. **设置页**依次配置（存 DB、Fernet 加密、日志脱敏）：
   - 交易所连接：Binance **testnet** API Key/Secret → 「测试连接」通过。
   - AI 模型：LLM base_url / api_key / model → 「测试连接」通过。
   - 通知（可选）：Telegram / Email。
3. 配好后**无需重启**：api/scheduler 每个策略周期自动从 DB 刷新（也可重启 scheduler 立即生效）。
4. 验证决策链跑起来：等一个策略周期（默认 15 分钟）后看 AI 决策流页面有新决策；
   或 `docker logs ap-dev-scheduler-1 --tail 100` 看 strategy pipeline 日志。
5. 之后按 [testnet验收手册](testnet验收手册.md) 走完整实盘验收 + 24h 观察。

---

## 阶段 6：部署用户 + GitHub 自动部署

> CI 执行 `cd $DEPLOY_DIR_<ENV> && bash scripts/deploy-<env>.sh`，**`DEPLOY_DIR_*` 一律填【构建目录】**
> `/workspace/alpha-pilot-build`（三环境共用）。

### 6A. 服务器侧：建专用部署用户 + 两把 key

用专用非 root 用户 `deployer` 跑部署（最小权限：只需 docker 组）。**两把方向相反的 key**，别混：

| key | 方向 | 公钥放哪 | 私钥放哪 |
|-----|------|---------|---------|
| 部署 key | GitHub Actions → 服务器 | `deployer` 的 `~/.ssh/authorized_keys` | GitHub Secret `DEPLOY_SSH_KEY` |
| deployer 的 GitHub key | 服务器 → GitHub（拉代码） | GitHub 仓库 **Deploy keys**（只读） | 服务器 `/home/deployer/.ssh/id_ed25519` |

```bash
# 1) 建用户 + 加 docker 组（勿加 root/sudo）
useradd -m -s /bin/bash deployer && usermod -aG docker deployer
# 2) 部署 key（GitHub Actions → 服务器）
ssh-keygen -t ed25519 -C "alphapilot-deploy" -f ~/.ssh/alphapilot_deploy_key -N ""
install -d -m700 -o deployer -g deployer /home/deployer/.ssh
cp ~/.ssh/alphapilot_deploy_key.pub /home/deployer/.ssh/authorized_keys
chmod 600 /home/deployer/.ssh/authorized_keys && chown -R deployer:deployer /home/deployer/.ssh
#   私钥 ~/.ssh/alphapilot_deploy_key → 老板贴到 GitHub Secret DEPLOY_SSH_KEY（不要回显）
# 3) deployer 的 GitHub key（服务器 → GitHub 拉代码）
sudo -u deployer ssh-keygen -t ed25519 -C "alphapilot-deployer-github" -f /home/deployer/.ssh/id_ed25519 -N ""
sudo -u deployer sh -c 'ssh-keyscan -t ed25519 github.com >> /home/deployer/.ssh/known_hosts'
#   公钥 /home/deployer/.ssh/id_ed25519.pub → 老板加到仓库 Deploy keys（不勾 write）
# 4) 目录归属 deployer
chown -R deployer:deployer /workspace/alpha-pilot-build /workspace/alpha-pilot-deploy
# 5) 自检
id deployer                                              # 应含 docker
su - deployer -c 'docker ps >/dev/null && echo DOCKER_OK'
su - deployer -c 'cd /workspace/alpha-pilot-build && git fetch origin && echo GIT_OK'  # 加完 Deploy key 后
```

### 6B. GitHub 网页侧（老板操作）

**① Deploy keys**（Settings → Deploy keys，不勾 write）：贴 `/home/deployer/.ssh/id_ed25519.pub`。
没这把，CI 会卡在 `git fetch origin` 报 `Permission denied (publickey)`。

**② Secrets**（Settings → Secrets and variables → Actions）：

| Secret | 值 |
|--------|----|
| `DEPLOY_SSH_HOST` | 服务器公网 IP / 域名 |
| `DEPLOY_SSH_PORT` | SSH 端口（默认 22 可不建） |
| `DEPLOY_SSH_USER` | `deployer` |
| `DEPLOY_SSH_KEY`  | 部署私钥全文（`~/.ssh/alphapilot_deploy_key`） |
| `DEPLOY_DIR_DEV` / `DEPLOY_DIR_TEST` / `DEPLOY_DIR_PROD` | 都填 `/workspace/alpha-pilot-build` |

**③ prod 审批门（推荐）**：Settings → Environments → 新建 `prod` → Required reviewers 填老板。
合并到 main 后 Deploy Prod 会暂停等网页 Approve。

配好后 `git push origin dev` → Actions SSH 进服务器自动部署 dev（CI 不跑测试门禁，单测在本地 pre-commit）。

---

## 阶段 7：test / prod（dev 验证通过后再做）

- **test**：`cp example.env` → `/workspace/alpha-pilot-deploy/test/envs/test.env`（同阶段 2 规则，
  **另行生成**两个 APP 密钥），然后构建目录里 `bash scripts/deploy-test.sh`。
  同一 commit 的 backend/webapp 镜像**直接复用**（build-once 晋升），只重建 frontend（basePath 烘焙）。
- **prod**：**[必须老板手动确认]** 接 Binance mainnet。
  - `prod.env`：`TRADING_MODE=mainnet`、独立 APP 密钥、`DEFAULT_ADMIN_PASSWORD` 用强密码。
  - 主网 Binance Key 同样走前端设置页（不进 env）。
  - 先配好 GitHub prod 审批门；服务器手动跑 `bash scripts/deploy-prod.sh` 会交互二次确认。

---

## 日常运维速查

```bash
# 手动部署 / 重部署（任何环境）
cd /workspace/alpha-pilot-build && bash scripts/deploy-dev.sh        # test/prod 同理

# 部署指定 commit（如回退到某个已验证 SHA）
SOURCE_REF=<sha或分支> bash scripts/deploy-dev.sh

# 查看当前/上一个可用版本
cat /workspace/alpha-pilot-deploy/dev/current.tag /workspace/alpha-pilot-deploy/dev/last-good.tag

# 看日志
docker logs -f $(docker ps -qf name=ap-dev-backend)
docker logs -f $(docker ps -qf name=ap-dev-scheduler)

# 中间件永远不随应用重部署重启；确需维护时先停三环境应用栈
```

## 验收清单（"部署打通"达成）

- [ ] 中间件 `ap-postgres`/`ap-redis` healthy，三库已建，`ap-shared` 网络在。
- [ ] dev：backend + scheduler + webapp 三 service Up；scheduler 日志见 `APScheduler started`。
- [ ] `https://<DOMAIN>/ap-dev/api/health` 返回正常 envelope；`/ap-dev/` 打开 webapp 登录页。
- [ ] 老板已在设置页配好 testnet Key + LLM Key，测试连接通过；策略周期产生决策。
- [ ] `deployer` 用户建好；GitHub Deploy key + Secrets 配齐；push dev 触发 Actions 自动部署，CI 绿。
- [ ] 全程无真实凭据进 git / 对话；env 真实值只在服务器 `envs/`，业务 Key 只在 DB（加密）。

## 出问题时

- CI 卡 `git fetch origin` 报 `Permission denied (publickey)` → deployer 公钥没加到 GitHub **Deploy keys**。
- CI SSH 连不上 → 查 `DEPLOY_SSH_HOST/PORT/USER/KEY`、服务器放通 SSH、`authorized_keys` 有部署公钥。
- `dubious ownership in repository` → 目录属主不对：`chown -R deployer:deployer ...` 或 `git config --global --add safe.directory <repo>`。
- backend/scheduler 起不来且日志见 `InsecureSecretError` → env 缺 `APP_AUTH_SECRET_KEY`/`APP_CONFIG_MASTER_KEY`。
- scheduler crash-loop `No module named src` → 镜像须有 `ENV PYTHONPATH=/app`（Dockerfile.backend 已带，怀疑镜像旧就删掉重 build）。
- backend 连不上 DB → 中间件在跑？`ap-shared` 网络在？env 没覆盖 compose 的 `DATABASE_URL`？
- 迁移失败 → 部署目录里 `... exec -T backend python scripts/upgrade_db.py` 单独跑看报错（脚本已自动回滚应用栈，但**迁移不自动回退**，需人工判断）。
- 部署失败自动回滚后 → 修复问题重新 `bash scripts/deploy-<env>.sh` 即可；回滚只回镜像不动 git。
- 设置页保存了 Key 但决策链仍用 Mock → 看 scheduler 日志有没有 `runtime settings loaded from DB`；
  没有则多半 `APP_CONFIG_MASTER_KEY` 与写入时不一致（解密失败会跳过并告警）。

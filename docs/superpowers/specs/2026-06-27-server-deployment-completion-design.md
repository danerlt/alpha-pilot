# 服务器部署打通 — 设计 spec（2026-06-27）

> 目标：把 AlphaPilot 的服务器部署从"只起 API"补成"完整可自动交易"的部署，并加上部署前测试门禁、
> 部署后健康验证与回滚兜底。本 spec 是对现有 [`docs/deploy-ci.md`](../../deploy-ci.md)（操作指南）的补充：
> deploy-ci.md 讲"配好后怎么用"，本 spec 讲"还缺什么 + 怎么补"。

## 0. 敏感信息处理约定（强制）

- 本文档及仓库代码**不含任何真实凭据 / 服务器 IP / 域名 / 绝对路径 / 密钥**。
- 所有服务器标识一律用占位符：`<PUBLIC_DOMAIN>` / `<SSH_HOST>` / `<DEPLOY_DIR_*>` 等。
- 真实值只存在于两处，均不进 git：
  - **GitHub Actions Secrets**（`DEPLOY_SSH_HOST/USER/KEY/PORT`、`DEPLOY_DIR_DEV/UAT/PROD`）。
  - **服务器本地 `envs/<env>.env`**（已被 `.gitignore` 整目录忽略；Claude 黑名单禁止读取）。
- 本仓库可读写的唯一 env 模板是 `example.env`（仅占位字段，无真实值）。

## 1. 背景：现有基础设施盘点

### 1.1 已就绪 ✅

| 项 | 现状 |
|---|---|
| 三环境 CI/CD | `.github/workflows/deploy-{dev,uat,prod}.yml` + `_deploy.yml`：push 分支 → SSH 进服务器跑 `scripts/deploy-{dev,uat,prod}.sh` |
| compose（3 套） | `docker/docker-compose.{dev-server,uat,prod}.yml`：postgres + redis + backend(API) + frontend，端口绑 `127.0.0.1`（nginx 反代，不暴露公网） |
| 后端镜像 | `Dockerfile.backend`：`CMD = bash scripts/start.sh`（迁移 + uvicorn API） |
| 部署脚本 | git pull → `compose up -d --build` → 等 API `/health` → `upgrade_db.py` |
| nginx | `docker/nginx/alpha-pilot.conf`（子路径反代 `/ap`、`/ap-uat`、`/ap-dev`） |
| prod 审批门 | GitHub Environment `prod` 可配 Required reviewers，接 mainnet 前人工 Approve |
| 文档 | `deploy-ci.md`：分支模型 / secrets 清单 / 服务器一次性准备 |

### 1.2 核心缺口 ❌

| 编号 | 缺口 | 严重度 | 后果 |
|---|---|---|---|
| **G1** | **scheduler 进程未部署** | **P0 致命** | compose 只有 `backend`(API)，无 scheduler service。部署后**策略循环 / 持仓监控（止损止盈熔断）/ 异步任务消费（close-all）/ EventShuttle / 通知告警 consumer / 评分 job / 归因 job 全部不运行**——系统"部署了但不交易、不监控、不告警"。 |
| G2 | 部署前无 CI 测试门禁 | P1 | workflow 直接 SSH 部署，未先跑 pytest + 前端 build/test，坏代码可直达服务器。 |
| G3 | 部署后只检 API 健康 | P1 | deploy 脚本只 curl `/health`，不验证 scheduler 在跑、不跑关键端点冒烟。 |
| G4 | 迁移并发竞争隐患 | P2 | `start.sh` 与 deploy 脚本各跑一次 `upgrade_db`；引入 scheduler 后两个容器同时启动可能并发迁移。 |
| G5 | 无回滚兜底 | P2 | 部署失败无自动回滚到上一个可用 SHA。 |
| G6 | scheduler 无健康可观测 | P2 | API 有 healthcheck，scheduler 没有；进程挂了不易察觉。 |

> **G1 是本 spec 的重心**——它直接决定"服务器部署"到底是不是"打通"。其余 G2–G6 是稳健性增强。

## 2. 目标 / 非目标

### 目标
- **G1**：所有环境 compose 增加 `scheduler` service（与 API 同镜像、单副本、优雅退出），部署后定时/异步任务真实运行。
- **G2**：CI 在 SSH 部署前先跑后端 pytest + 前端 build/typecheck/vitest，绿灯才部署。
- **G3**：部署脚本扩展为"API 健康 + scheduler 存活 + 关键端点冒烟"三检。
- **G4**：迁移收敛为部署时单点执行，容器启动不各自迁移。
- **G5/G6**：回滚兜底 + scheduler healthcheck（增强项，可分阶段）。

### 非目标
- 不引入容器镜像 registry（当前服务器本地 `compose build` 可接受；未来量大再议）。
- 不改 nginx 子路径方案。
- 不在本 spec 内触碰任何真实 secrets / env（那是老板在 GitHub + 服务器侧的一次性配置）。
- 不实现 K8s / 多机 / 蓝绿（V0.x 单机足够）。

## 3. 设计

### 3.1 G1 — scheduler service（P0）

每个环境 compose 在 `backend` 之后增加一个 `scheduler` service，复用同一镜像，仅启动命令不同：

```yaml
  scheduler:
    build:
      context: ../backend
      dockerfile: ../docker/Dockerfile.backend
    env_file:
      - ../envs/<env>.env
    environment:
      DATABASE_URL: postgresql://alphapilot:${DB_PASSWORD:-alphapilot}@postgres:5432/alphapilot_<env>
      REDIS_URL: redis://redis:6379/0
    command: ["python", "scripts/start_scheduler.py"]   # 覆盖 Dockerfile 的 API CMD
    depends_on:
      postgres: { condition: service_healthy }
      redis:    { condition: service_healthy }
    restart: unless-stopped
    stop_grace_period: 60s     # 与 start_scheduler graceful shutdown 对齐（等运行中 job 收尾）
    # 单副本：APScheduler + 任务队列消费不可并发（避免策略循环重叠 / 重复消费）
```

要点：
- **单副本**（不设 replicas>1）：scheduler 内含 APScheduler 定时器 + BRPOP 任务消费 + EventShuttle + notifier，
  并发会导致策略循环重叠、任务重复消费。project.md §8 已定调"scheduler 单容器"。
- `command` 覆盖镜像 `CMD`，无需新 Dockerfile。
- **不设 ROOT_PATH / ports**：scheduler 不对外暴露 HTTP，纯后台进程。
- scheduler 不应再跑迁移（见 G4）；它依赖 API/部署脚本已迁移完成。

### 3.2 G2 — CI 测试门禁（P1）

改造 `deploy-{dev,uat,prod}.yml`：在 `deploy` job 前加 `test` job，`deploy` 用 `needs: test` 串行。

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env: { POSTGRES_USER: alphapilot, POSTGRES_PASSWORD: alphapilot, POSTGRES_DB: alphapilot }
        ports: ["5442:5432"]
        options: >-
          --health-cmd "pg_isready -U alphapilot" --health-interval 5s
          --health-timeout 5s --health-retries 5
      redis:
        image: redis:7-alpine
        ports: ["6389:6379"]
        options: --health-cmd "redis-cli ping" --health-interval 5s --health-timeout 5s --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - # 后端: uv sync + ALPHAPILOT_SKIP_SECRET_VALIDATION=1 pytest -q
      - # 前端: npm ci && npm run typecheck && npm run test && npm run build
  deploy:
    needs: test            # 测试绿才部署
    uses: ./.github/workflows/_deploy.yml
    with: { environment: <env>, deploy_script: scripts/deploy-<env>.sh }
    secrets: inherit
```

要点：
- 测试用 GitHub Actions `services` 起 PG(5442)/Redis(6389)，与本地 conftest 端口一致，零改动。
- 后端测试加 `ALPHAPILOT_SKIP_SECRET_VALIDATION=1`（CI 无真实密钥）。
- prod 的测试门禁 + 既有 Environment 审批门**双保险**。

### 3.3 G3 — 部署后三检（P1）

`scripts/deploy-<env>.sh` 健康检查段扩展：

1. **API 健康**：现有 `curl /health`（保留）。
2. **scheduler 存活**：`docker compose ps scheduler` 状态为 `running`，且近 N 行日志含 `APScheduler started`（`docker compose logs scheduler --tail=20 | grep -q "APScheduler started"`）。
3. **关键端点冒烟**：`/api/health` envelope 正确（可选：带一个只读端点的 200 校验）。

任一检失败 → 打印对应 service 日志 → 非零退出（CI 标红，触发 G5 回滚）。

### 3.4 G4 — 迁移单点执行（P2）

- 从 `Dockerfile.backend` 的启动链移除"容器内自动迁移"，即 `start.sh` 不再 `upgrade_db`，只跑 uvicorn。
- 迁移统一由 **deploy 脚本在 `compose up` 之后、健康检查之前**执行一次（`compose run --rm backend python scripts/upgrade_db.py` 或在 backend 容器内 exec）。
- 好处：api 与 scheduler 两容器同时启动时不会并发迁移；迁移失败即部署失败，不会留下半迁移状态的运行容器。
- 备选（更小改动）：保留 start.sh 迁移，但只让 `backend` 跑、`scheduler` 不跑（scheduler `command` 直接 `start_scheduler.py` 已天然不迁移）——但两 backend 副本仍可能竞争，故首选上面的单点方案。

### 3.5 G5 — 回滚兜底（P2，增强）

deploy 脚本开头记录当前 SHA，健康检查失败时回滚：

```bash
PREV_SHA=$(git rev-parse HEAD)
# ... git pull + up + 健康检查 ...
# 健康检查失败分支:
echo "❌ 部署失败，回滚到 $PREV_SHA"
git reset --hard "$PREV_SHA"
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build
exit 1
```

prod 谨慎：回滚也接 mainnet，建议 prod 回滚后仅恢复服务、不自动重试，留人工确认。

### 3.6 G6 — scheduler healthcheck（P2，增强）

scheduler 无 HTTP 端口，healthcheck 用进程/心跳两选一：
- **轻量**：`healthcheck` 检查主进程存活（`pgrep -f start_scheduler`）。
- **更实**：scheduler 周期性写一个 Redis 心跳 key（`SET scheduler:heartbeat <ts> EX 90`），healthcheck 检 key 新鲜度。后者能发现"进程在但 job 卡死"，但需少量代码（`OpsHeartbeat` 事件契约已存在，可复用）。V0.x 先用轻量版。

## 4. 实施阶段

| 阶段 | 内容 | 风险 | 验收 |
|---|---|---|---|
| P0 | G1：3 套 compose 加 scheduler service | 低（加 service，不改现有） | 本地 `docker compose up` 后 `docker compose ps` 见 scheduler running + 日志 `APScheduler started` |
| P1 | G2：workflow 加 test job（needs gate）；G3：deploy 脚本三检 | 中（CI 改造） | push dev 后 Actions 先跑 test 再 deploy；故意改红一个测试验证 deploy 被拦 |
| P2 | G4：迁移单点化；G5：回滚兜底；G6：scheduler healthcheck | 中（改启动链/部署脚本） | 迁移只执行一次；模拟健康失败触发回滚；scheduler healthcheck 生效 |

> 建议：P0 单独一个 PR 先合（这是"打通"的本体），P1/P2 各自独立 PR，逐个 dev 验证。

## 5. 验收标准（"部署打通"的定义）

1. push `dev` → CI 先跑测试（绿）→ SSH 部署 → 服务器上 `docker compose ps` 同时见 **backend + scheduler + frontend + postgres + redis** 五个 service 健康。
2. scheduler 日志可见 `APScheduler started` + 任务消费/EventShuttle/notifier 启动行。
3. 部署后 `/ap-dev/api/health` 返回正确 envelope；策略循环 job 在配置间隔触发（日志可见）。
4. 测试门禁生效：故意推一个失败测试，deploy job 不执行。
5. 全程无任何真实凭据/IP 进入 git；secrets 只在 GitHub + 服务器 `envs/`。

## 6. 老板侧一次性事项（不在代码范围，仅清单）

> 这些是 spec 落地后需要老板在自己的 GitHub/服务器侧操作的，Claude 不接触：

- GitHub Secrets 填好 `DEPLOY_SSH_*` 与 `DEPLOY_DIR_*`（见 deploy-ci.md §3.1）。
- 服务器三个 clone 目录各放好 `envs/<env>.env`（从 example.env 拷贝填真实密钥）。
- 每个 env 必填 `APP_AUTH_SECRET_KEY` / `APP_CONFIG_MASTER_KEY`（否则 `_validate_secrets` 拒绝启动）。
- prod Environment 配 Required reviewers（审批门）。
- nginx 并入 `docker/nginx/alpha-pilot.conf` 的 location 块并 reload。

## 7. 风险与回避

- **scheduler 双跑**：若误配多副本会重复下单/重复消费 → 强制单副本 + project.md §8 已定调，compose 不设 replicas。
- **迁移竞争**：G4 单点迁移规避；过渡期若先上 G1 未上 G4，scheduler 的 `command` 不含迁移，天然不与 backend 竞争（backend 仍 start.sh 迁移一次），可接受。
- **CI 测试拖慢部署**：后端全量 ~70s + 前端 build，可接受；如需提速可只在 deploy 分支跑、feat 分支跑轻量。
- **prod 回滚接 mainnet**：回滚只恢复服务不自动重试，留人工确认（§3.5）。

---

**End** — 落地顺序建议：先 P0（G1 scheduler service，一个 PR 即"打通"本体），再 P1（测试门禁 + 三检），最后 P2（迁移/回滚/心跳增强）。每阶段 dev 验证后再上 uat/prod。

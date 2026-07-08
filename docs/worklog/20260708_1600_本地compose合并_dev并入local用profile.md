# 本地 compose 合并：dev.yml 并入 local.yml，用 profile 区分两种模式

日期：2026-07-08
分支：dev
背景：本地有两个近乎重复的 compose——`docker-compose.dev.yml`（deps 栈：只 pg+redis，
`make deps-up`）和 `docker-compose.local.yml`（完整栈：+backend+frontend，`make local-up`）。
老板要求合并为一个 `local.yml`。

## 做了什么

- **合并进 `docker/docker-compose.local.yml`**：用 Compose profile 分流
  - `postgres`/`redis`：不带 profile → `make deps-up`（`docker compose ... up`）默认只起这俩，
    且不 build 后端/前端镜像，pytest 热路径依旧快。
  - `backend`/`frontend`：`profiles: ["full"]` → `make local-up`（`... --profile full up`）才起。
- **删除 `docker/docker-compose.dev.yml`**（`git rm -f`）。
- **Makefile**：`COMPOSE_DEPS` 与 `COMPOSE_LOCAL` 都指向 `local.yml`，后者追加 `--profile full`；
  命令名 `make deps-up` / `make local-up` **不变**，使用习惯零改动。补 `.PHONY` 缺失的 deps-*。

## 合并时对齐的差异（关键）

| 项 | 取值 | 理由 |
|---|---|---|
| `name` | `alpha-pilot`（保留，非 ap-local） | 容器名 `alpha-pilot-postgres-1` 被 conftest.py + 多处文档依赖 |
| `POSTGRES_DB` | `alphapilot`（原 local 是 alphapilot_dev） | conftest admin 连 `alphapilot`；full 后端 DATABASE_URL 同步改连 `alphapilot` |
| volume | `postgres_data`（原 local 是 postgres_local_data） | 与 deps/pytest 复用同卷，`make deps-up` 无缝复用现有容器 |
| 端口 | `127.0.0.1:5442/6389`（loopback） | 与安全收口一致；如需 WSL/他机连去掉 127.0.0.1 前缀 |

## 副作用（可选清理）

旧 `make local-up`（name=ap-local）遗留的 `ap-local-*` 容器与 `ap-local_postgres_local_data`
卷成为孤儿，无引用、无害；如需清理：`docker rm ap-local-{postgres,redis,backend,frontend}-1`
+ `docker volume rm ap-local_postgres_local_data`。

## 验证

- `docker compose -f docker-compose.local.yml config --services` → 仅 postgres/redis ✓
- `... --profile full config --services` → backend/frontend/postgres/redis 四个 ✓
- 端口渲染 5442/6389、`POSTGRES_DB=alphapilot` 正确 ✓
- 全仓无存活脚本/CI/Makefile 引用旧 dev.yml（残留仅历史 plans/specs 文档）✓

## 对应 commit

（待提交；建议与安全收口分两个 commit）

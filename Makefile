.PHONY: help \
        local-up local-down local-deploy \
        dev-up dev-down dev-deploy \
        test-up test-down \
        prod-deploy \
        dev-backend init-db upgrade-db \
        test test-unit test-integration lint fmt

# ── Docker Compose 文件 ───────────────────────────────────────────────────────
COMPOSE_LOCAL   = docker compose -f docker/docker-compose.local.yml
COMPOSE_DEV     = docker compose -f docker/docker-compose.dev-server.yml
COMPOSE_TEST    = docker compose -f docker/docker-compose.test.yml
COMPOSE_PROD    = docker compose -f docker/docker-compose.prod.yml

help:
	@echo "AlphaPilot 开发命令"
	@echo ""
	@echo "── 本地开发（Windows / Linux 本机，端口 8000/3000）──"
	@echo "  make local-up       启动本地完整栈（含前后端）"
	@echo "  make local-down     停止本地栈"
	@echo "  make local-deploy   构建并重启本地栈（自动迁移）"
	@echo ""
	@echo "── 服务器开发环境（/ap-dev，端口 8001/3001）──"
	@echo "  make dev-up         启动开发栈"
	@echo "  make dev-down       停止开发栈"
	@echo "  make dev-deploy     构建并重启开发栈（自动迁移）"
	@echo ""
	@echo "── 服务器测试环境（/ap-test，端口 8002/3002）──"
	@echo "  make test-up        启动测试栈"
	@echo "  make test-down      停止测试栈"
	@echo ""
	@echo "── 生产环境（/ap，端口 8003/3003，手动）──"
	@echo "  make prod-deploy    手动部署生产环境（需确认）"
	@echo ""
	@echo "── 后端开发（热重载，需本地 venv）──"
	@echo "  make dev-backend    启动 FastAPI 开发服务器"
	@echo "  make init-db        初始化数据库迁移（首次）"
	@echo "  make upgrade-db     运行数据库迁移"
	@echo ""
	@echo "── 测试 & 代码质量 ──"
	@echo "  make test           运行所有测试"
	@echo "  make test-unit      仅运行单元测试"
	@echo "  make test-integration 仅运行集成测试"
	@echo "  make lint           运行 ruff linter"
	@echo "  make fmt            运行 ruff formatter"

# ── 本地环境 ──────────────────────────────────────────────────────────────────
local-up:
	$(COMPOSE_LOCAL) --env-file .env.local up -d

local-down:
	$(COMPOSE_LOCAL) down

local-deploy:
	bash scripts/deploy-local.sh

# ── 服务器开发环境 ─────────────────────────────────────────────────────────────
dev-up:
	$(COMPOSE_DEV) --env-file .env.dev-server up -d

dev-down:
	$(COMPOSE_DEV) down

dev-deploy:
	bash scripts/deploy-dev.sh

# ── 服务器测试环境 ─────────────────────────────────────────────────────────────
test-up:
	$(COMPOSE_TEST) --env-file .env.test up -d

test-down:
	$(COMPOSE_TEST) down

# ── 生产环境（手动）─────────────────────────────────────────────────────────────
prod-deploy:
	bash scripts/deploy-prod.sh

# ── 后端开发（本地 venv）──────────────────────────────────────────────────────
dev-backend:
	cd backend && source .venv/bin/activate && uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

init-db:
	cd backend && source .venv/bin/activate && python scripts/init_db.py

upgrade-db:
	cd backend && source .venv/bin/activate && python scripts/upgrade_db.py

# ── 测试 & 代码质量 ───────────────────────────────────────────────────────────
test:
	cd backend && source .venv/bin/activate && pytest tests/ -v --cov=src --cov-report=term-missing

test-unit:
	cd backend && source .venv/bin/activate && pytest tests/unit/ -v

test-integration:
	cd backend && source .venv/bin/activate && pytest tests/integration/ -v

lint:
	cd backend && source .venv/bin/activate && ruff check src/ tests/

fmt:
	cd backend && source .venv/bin/activate && ruff format src/ tests/

#!/bin/bash
# test 环境部署脚本（Linux 服务器）
# 共享中间件架构：连 ap-postgres / ap-redis，database=alphapilot_test + Redis db=1。

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_DIR/docker/docker-compose.test.yml"
MIDDLEWARE_FILE="$PROJECT_DIR/docker/docker-compose.middleware.yml"
ENV_FILE="$PROJECT_DIR/envs/test.env"

echo "========================================"
echo " AlphaPilot Test 环境部署"
echo "========================================"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ 未找到 $ENV_FILE，请先从 example.env 拷贝填写"
    exit 1
fi

cd "$PROJECT_DIR"

PREV_SHA="$(git rev-parse HEAD)"
rollback() {
    echo "❌ 部署失败，回滚到 $PREV_SHA"
    git reset --hard "$PREV_SHA"
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build || true
    exit 1
}

echo "[1/5] 确保共享中间件在运行..."
docker compose -f "$MIDDLEWARE_FILE" up -d
RETRIES=30
until docker exec ap-postgres pg_isready -U alphapilot >/dev/null 2>&1; do
    RETRIES=$((RETRIES - 1)); [ $RETRIES -le 0 ] && { echo "❌ 中间件 postgres 未就绪"; exit 1; }
    sleep 2
done
docker exec ap-postgres psql -U alphapilot -tc \
    "SELECT 1 FROM pg_database WHERE datname='alphapilot_test'" | grep -q 1 || \
    docker exec ap-postgres psql -U alphapilot -c "CREATE DATABASE alphapilot_test"

echo "[2/5] 拉取最新代码..."
git pull origin test

echo "[3/5] 构建镜像并重启应用（backend + scheduler + frontend）..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build || rollback

echo "[4/5] 运行数据库迁移（单点执行）..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T backend python scripts/upgrade_db.py || rollback

echo "[5/5] 健康三检（API + scheduler）..."
RETRIES=30
until docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec -T backend \
        python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" >/dev/null 2>&1; do
    RETRIES=$((RETRIES - 1))
    if [ $RETRIES -le 0 ]; then
        echo "❌ API 健康检查超时"
        docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs backend --tail=50
        rollback
    fi
    sleep 2
done
if ! docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs scheduler --tail=30 2>/dev/null | grep -q "APScheduler started"; then
    echo "⚠️  scheduler 未见 'APScheduler started'，打印日志供排查："
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs scheduler --tail=30
    rollback
fi

echo ""
echo "✅ Test 环境部署完成（backend + scheduler + frontend 已就绪）"
echo "   前端: <PUBLIC_DOMAIN>/ap-test  ·  后端: <PUBLIC_DOMAIN>/ap-test/api"

#!/bin/bash
# 本地开发环境部署（Windows Git Bash / Linux 本机）
# 访问地址: http://localhost:3000（前端） http://localhost:8000（后端）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_DIR/docker/docker-compose.local.yml"
ENV_FILE="$PROJECT_DIR/envs/local.env"

echo "========================================"
echo " AlphaPilot 本地环境部署"
echo "========================================"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ 未找到 $ENV_FILE"
    echo "   请先复制 example.env 为 envs/local.env 并填写配置"
    exit 1
fi

cd "$PROJECT_DIR"

echo "[1/3] 构建镜像并启动服务..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build

echo "[2/3] 等待后端服务就绪 (port 8000)..."
RETRIES=30
until docker compose -f "$COMPOSE_FILE" exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" > /dev/null 2>&1; do
    RETRIES=$((RETRIES - 1))
    if [ $RETRIES -le 0 ]; then
        echo "❌ 后端服务启动超时"
        docker compose -f "$COMPOSE_FILE" logs backend --tail=50
        exit 1
    fi
    sleep 2
done

echo "[3/3] 运行数据库迁移..."
docker compose -f "$COMPOSE_FILE" exec -T backend python scripts/upgrade_db.py

echo ""
echo "✅ 本地环境启动完成"
echo "   前端: http://localhost:3000"
echo "   后端 API: http://localhost:8000/api"
echo "   API 文档: http://localhost:8000/docs"

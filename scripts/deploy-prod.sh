#!/bin/bash
# 生产环境手动部署脚本（Linux 服务器）
# 访问地址: https://www.danerlt.top/ap

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_DIR/docker/docker-compose.prod.yml"
ENV_FILE="$PROJECT_DIR/envs/prod.env"

echo "========================================"
echo " AlphaPilot 生产环境部署"
echo "========================================"
echo "⚠️  警告：这是生产环境，请确认已在 dev/test 环境验证通过"
read -p "确认部署到生产环境？(yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "已取消"
    exit 0
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ 未找到 $ENV_FILE"
    exit 1
fi

cd "$PROJECT_DIR"

echo "[1/4] 拉取最新代码..."
git pull origin main

echo "[2/4] 构建镜像并重启服务..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build

echo "[3/4] 等待后端服务就绪 (port 8003)..."
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

echo "[4/4] 运行数据库迁移..."
docker compose -f "$COMPOSE_FILE" exec -T backend python scripts/upgrade_db.py

echo ""
echo "✅ 生产环境部署完成"
echo "   前端: https://www.danerlt.top/ap"
echo "   后端: https://www.danerlt.top/ap/api"

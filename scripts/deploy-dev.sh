#!/bin/bash
# 开发环境自动部署脚本（Linux 服务器）
# 每次完成阶段任务后由 Claude 自动调用
# 访问地址: https://www.danerlt.top/ap-dev

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_DIR/docker/docker-compose.dev-server.yml"
ENV_FILE="$PROJECT_DIR/envs/dev.env"

echo "========================================"
echo " AlphaPilot Dev 环境自动部署"
echo "========================================"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ 未找到 $ENV_FILE"
    echo "   请先复制 example.env 为 envs/dev.env 并填写配置"
    exit 1
fi

cd "$PROJECT_DIR"

echo "[1/4] 拉取最新代码 (dev 分支)..."
git pull origin dev

echo "[2/4] 构建镜像并重启服务..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build

echo "[3/4] 等待后端服务就绪 (port 8001)..."
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
echo "✅ 开发环境部署完成"
echo "   前端: https://www.danerlt.top/ap-dev  (本机: http://localhost:3001)"
echo "   后端: https://www.danerlt.top/ap-dev/api  (本机: http://localhost:8001)"
echo "   API文档: https://www.danerlt.top/ap-dev/docs"

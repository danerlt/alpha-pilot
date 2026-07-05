#!/bin/bash
# build-once / deploy-many 公共部署逻辑（被 scripts/deploy-{dev,test,prod}.sh source 调用）
# 设计见 docs/superpowers/specs/2026-06-28-build-once-deploy-many-design.md
#
# 拓扑：
#   本库与 deploy-*.sh 位于【构建目录】(alpha-pilot-build) 的 scripts/ 下（有源码）。
#   - 构建目录：按目标 commit checkout + docker build 出 :<sha> 镜像
#   - 部署目录：仅 compose + envs + tag 文件，用 image: 起容器（无源码）
#
# 调用方（deploy-<env>.sh）需 export：
#   DEPLOY_ENV          dev|test|prod
#   COMPOSE_BASENAME    docker-compose.<x>.yml
#   FRONTEND_BASE_PATH  /ap-dev | /ap-test | /ap   （前端 basePath，构建期烘焙）
# 可选覆盖（环境变量）：
#   BUILD_DIR DEPLOY_DIR MIDDLEWARE_DIR SOURCE_REMOTE SOURCE_REF DB_NAME REQUIRE_CONFIRM
#
# 注：全部逻辑封装在 run_deploy() 内，调用方仅在最后调用一次 —— bash 先完整解析整个
# 函数体再执行，因此 [2] 步 git checkout 改写磁盘上的脚本不会破坏正在运行的进程。

run_deploy() {
    set -euo pipefail

    : "${DEPLOY_ENV:?需 export DEPLOY_ENV}"
    : "${COMPOSE_BASENAME:?需 export COMPOSE_BASENAME}"
    : "${FRONTEND_BASE_PATH:?需 export FRONTEND_BASE_PATH}"

    local BUILD_DIR="${BUILD_DIR:-$(cd "$(dirname "${BASH_SOURCE[1]}")/.." && pwd)}"
    local DEPLOY_DIR="${DEPLOY_DIR:-/workspace/alpha-pilot-deploy/$DEPLOY_ENV}"
    local MIDDLEWARE_DIR="${MIDDLEWARE_DIR:-/workspace/alpha-pilot-deploy/middleware}"
    local SOURCE_REMOTE="${SOURCE_REMOTE:-origin}"
    local SOURCE_REF="${SOURCE_REF:-$DEPLOY_ENV}"
    local DB_NAME="${DB_NAME:-alphapilot_$DEPLOY_ENV}"
    local ENV_FILE="$DEPLOY_DIR/envs/$DEPLOY_ENV.env"
    local COMPOSE_FILE="$DEPLOY_DIR/docker/$COMPOSE_BASENAME"

    echo "======== AlphaPilot 部署 [$DEPLOY_ENV] (build-once) ========"
    echo " 构建目录: $BUILD_DIR"
    echo " 部署目录: $DEPLOY_DIR"
    echo " 源:       $SOURCE_REMOTE/$SOURCE_REF"

    [ -f "$ENV_FILE" ] || { echo "❌ 未找到 $ENV_FILE（从 example.env 拷贝填写）"; exit 1; }

    if [ "${REQUIRE_CONFIRM:-0}" = "1" ]; then
        read -r -p "⚠️  即将部署到 [$DEPLOY_ENV]，输入 yes 继续: " ans
        [ "$ans" = "yes" ] || { echo "已取消"; exit 1; }
    fi

    # ── [1/7] 共享中间件（已健康则不动，避免每次部署重建共享中间件）──
    echo "[1/7] 确保共享中间件运行..."
    if ! docker ps --filter name=ap-postgres --filter health=healthy -q | grep -q .; then
        docker compose -f "$MIDDLEWARE_DIR/docker-compose.middleware.yml" up -d
    fi
    # 等 postgres 真正可接受查询（pg_isready 通过后仍有窗口）
    local R=60
    until docker exec ap-postgres psql -U alphapilot -tAc "SELECT 1" >/dev/null 2>&1; do
        R=$((R-1)); [ $R -le 0 ] && { echo "❌ 中间件 postgres 未就绪"; exit 1; }; sleep 2
    done
    # 幂等建库（卷已存在时 init 脚本不跑）；容错 already-exists / 并发
    docker exec ap-postgres psql -U alphapilot -tAc \
        "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1 || \
        docker exec ap-postgres createdb -U alphapilot "$DB_NAME" 2>/dev/null || true

    # ── [2/7] 构建目录 checkout 目标 commit ──────────────────
    echo "[2/7] 同步源码到目标 commit..."
    cd "$BUILD_DIR"
    git fetch "$SOURCE_REMOTE" "$SOURCE_REF"
    git checkout -q FETCH_HEAD
    local SHA; SHA="$(git rev-parse --short=12 HEAD)"
    local IMAGE_TAG="$SHA"
    local FRONTEND_TAG="$SHA-$DEPLOY_ENV"
    # webapp 镜像零环境烘焙（真 build-once），跨环境同一 tag；
    # export 使所有 compose 调用可插值（compose 文件未引用该服务时无副作用）
    export WEBAPP_TAG="$SHA"
    echo "    SHA = $SHA"

    # ── [3/7] inspect-or-build 镜像 ──────────────────────────
    echo "[3/7] 构建/复用镜像..."
    if docker image inspect "alphapilot-backend:$IMAGE_TAG" >/dev/null 2>&1; then
        echo "    backend:$IMAGE_TAG 已存在，复用（build-once）"
    else
        echo "    构建 backend:$IMAGE_TAG"
        docker build -t "alphapilot-backend:$IMAGE_TAG" -f docker/Dockerfile.backend backend
    fi
    if docker image inspect "alphapilot-frontend:$FRONTEND_TAG" >/dev/null 2>&1; then
        echo "    frontend:$FRONTEND_TAG 已存在，复用"
    else
        echo "    构建 frontend:$FRONTEND_TAG (BASE_PATH=$FRONTEND_BASE_PATH)"
        docker build -t "alphapilot-frontend:$FRONTEND_TAG" \
            --build-arg "BASE_PATH=$FRONTEND_BASE_PATH" \
            --build-arg "NEXT_PUBLIC_API_BASE=$FRONTEND_BASE_PATH/api" \
            -f docker/Dockerfile.frontend frontend
    fi
    # webapp（仅当目标 compose 引用了该服务才构建）
    if grep -q "alphapilot-webapp" "$BUILD_DIR/docker/$COMPOSE_BASENAME"; then
        if docker image inspect "alphapilot-webapp:$WEBAPP_TAG" >/dev/null 2>&1; then
            echo "    webapp:$WEBAPP_TAG 已存在，复用（build-once）"
        else
            echo "    构建 webapp:$WEBAPP_TAG"
            docker build -t "alphapilot-webapp:$WEBAPP_TAG" -f docker/Dockerfile.webapp webapp
        fi
    fi

    # ── [4/7] 同步 compose 到部署目录 ────────────────────────
    echo "[4/7] 同步 compose 到部署目录..."
    mkdir -p "$DEPLOY_DIR/docker"
    cp "$BUILD_DIR/docker/$COMPOSE_BASENAME" "$COMPOSE_FILE"

    local dc=(docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE")
    _up() { IMAGE_TAG="$1" FRONTEND_TAG="$2" "${dc[@]}" up -d; }
    _rollback() {
        echo "❌ 部署失败"
        if [ -f "$DEPLOY_DIR/last-good.tag" ]; then
            local LG; LG="$(cat "$DEPLOY_DIR/last-good.tag")"
            echo "↩️  回滚到上一个可用镜像 $LG（不动 git）"
            export WEBAPP_TAG="$LG"   # webapp 与 backend 同 SHA 轨回滚
            _up "$LG" "$LG-$DEPLOY_ENV" || true
            echo "$LG" > "$DEPLOY_DIR/current.tag"
        else
            echo "（首次部署，无回滚点）"
        fi
        exit 1
    }

    # ── [5/7] 记录回滚点 + 起栈 ──────────────────────────────
    echo "[5/7] 起应用栈..."
    [ -f "$DEPLOY_DIR/current.tag" ] && cp "$DEPLOY_DIR/current.tag" "$DEPLOY_DIR/last-good.tag"
    _up "$IMAGE_TAG" "$FRONTEND_TAG" || _rollback
    echo "$SHA" > "$DEPLOY_DIR/current.tag"

    # ── [6/7] 迁移（单点）────────────────────────────────────
    echo "[6/7] 数据库迁移..."
    IMAGE_TAG="$IMAGE_TAG" FRONTEND_TAG="$FRONTEND_TAG" "${dc[@]}" exec -T backend python scripts/upgrade_db.py || _rollback

    # ── [7/7] 健康三检 ───────────────────────────────────────
    echo "[7/7] 健康三检（API + scheduler）..."
    R=30
    until IMAGE_TAG="$IMAGE_TAG" FRONTEND_TAG="$FRONTEND_TAG" "${dc[@]}" exec -T backend \
            python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/health')" >/dev/null 2>&1; do
        R=$((R-1))
        if [ $R -le 0 ]; then
            echo "❌ API 健康检查超时"
            IMAGE_TAG="$IMAGE_TAG" FRONTEND_TAG="$FRONTEND_TAG" "${dc[@]}" logs backend --tail=50
            _rollback
        fi
        sleep 2
    done
    # scheduler 健康：以「容器 running 且非 crash-loop」为准。
    # （启动标记 'APScheduler started' 会因容器长跑滚出 tail，不能作为硬判据）
    sleep 5
    local scid; scid="$(IMAGE_TAG="$IMAGE_TAG" FRONTEND_TAG="$FRONTEND_TAG" "${dc[@]}" ps -q scheduler 2>/dev/null)"
    local sstate srestart
    sstate="$(docker inspect -f '{{.State.Status}}' "$scid" 2>/dev/null || echo missing)"
    srestart="$(docker inspect -f '{{.State.Restarting}}' "$scid" 2>/dev/null || echo true)"
    if [ "$sstate" != "running" ] || [ "$srestart" = "true" ]; then
        echo "❌ scheduler 状态异常: status=$sstate restarting=$srestart"
        IMAGE_TAG="$IMAGE_TAG" FRONTEND_TAG="$FRONTEND_TAG" "${dc[@]}" logs scheduler --tail=50
        _rollback
    fi
    if IMAGE_TAG="$IMAGE_TAG" FRONTEND_TAG="$FRONTEND_TAG" "${dc[@]}" logs scheduler 2>/dev/null | grep -q "APScheduler started"; then
        echo "    scheduler 启动标记确认 ✓"
    else
        echo "    （未找到启动标记，但容器 running 且非重启，视为正常）"
    fi

    echo ""
    echo "✅ [$DEPLOY_ENV] 部署完成 (SHA=$SHA)：backend + scheduler + frontend 就绪"
}

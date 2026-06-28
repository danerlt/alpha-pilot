#!/bin/bash
# prod 部署入口（build-once / deploy-many）
# 详见 scripts/lib/deploy_common.sh 与 docs/superpowers/specs/2026-06-28-build-once-deploy-many-design.md
# 接 Binance mainnet：CI 经 GitHub Environment 审批门把关；交互式终端会二次确认。
# backend/scheduler 复用已验证的 :<sha> 镜像；frontend 按 /ap 构建。SOURCE_REF=main。
set -euo pipefail
export DEPLOY_ENV=prod
export COMPOSE_BASENAME=docker-compose.prod.yml
export FRONTEND_BASE_PATH=/ap
export SOURCE_REF="${SOURCE_REF:-main}"
# 交互式终端二次确认（CI 无 TTY 时跳过，由 GitHub Environment 审批门把关）
if [ -t 0 ] && [ "${FORCE_DEPLOY:-0}" != "1" ]; then
    export REQUIRE_CONFIRM=1
fi
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/deploy_common.sh"
run_deploy

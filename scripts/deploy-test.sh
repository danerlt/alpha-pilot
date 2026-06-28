#!/bin/bash
# test 部署入口（build-once / deploy-many）
# 详见 scripts/lib/deploy_common.sh 与 docs/superpowers/specs/2026-06-28-build-once-deploy-many-design.md
# backend/scheduler 复用 dev 阶段已构建的 :<sha> 镜像；frontend 按 /ap-test 构建。
set -euo pipefail
export DEPLOY_ENV=test
export COMPOSE_BASENAME=docker-compose.test.yml
export FRONTEND_BASE_PATH=/ap-test
export SOURCE_REF="${SOURCE_REF:-test}"
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/deploy_common.sh"
run_deploy

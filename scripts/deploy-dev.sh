#!/bin/bash
# dev 部署入口（build-once / deploy-many）
# 详见 scripts/lib/deploy_common.sh 与 docs/superpowers/specs/2026-06-28-build-once-deploy-many-design.md
#
# CI:     cd <构建目录> && bash scripts/deploy-dev.sh
# 本地验证: SOURCE_REMOTE=<开发目录> SOURCE_REF=dev bash scripts/deploy-dev.sh
set -euo pipefail
export DEPLOY_ENV=dev
export COMPOSE_BASENAME=docker-compose.dev-server.yml
export FRONTEND_BASE_PATH=/ap-dev
export SOURCE_REF="${SOURCE_REF:-dev}"
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/deploy_common.sh"
run_deploy

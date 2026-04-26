# 2026-04-26 — 安全审计修复 + 老板必须手动执行的清单

## 背景

post-Plan5 完整 codereview 后又派 code-reviewer 做了一轮深度安全审计,
找到 6 个 Critical + 11 个 High + 多项 M/L 安全问题. 代码层面已全部修复
并 push 到 main (HEAD: 15436fa), 但有些事项**必须老板在 dev/prod 服务器
手动执行**才能真正生效.

## 已完成 (代码层)

13 个 commit, 详见 git log ea0dfa2..15436fa.

| 优先级 | # | 问题 | commit |
|--------|---|------|--------|
| Critical | C1 | APP_AUTH_SECRET_KEY 默认值硬编码 — JWT 任意伪造 | ea0dfa2 |
| Critical | C2 | APP_CONFIG_MASTER_KEY 默认值硬编码 — Fernet 解密泄露 | ea0dfa2 |
| Critical | C3 | 真实 admin 邮箱+密码 commit 进 git history | ea0dfa2 |
| Critical | C4 | /api/config/runtime 无鉴权 — 配置泄露 | ea0dfa2 |
| Critical | C5 | /api/auth/register 完全开放 — 任何人能拿 USER 角色读全部数据 | ea0dfa2 |
| Critical | C6 | NaN/Inf stop_loss 绕过 ExecutionGuard 全链路 | ea0dfa2 |
| High | H1 | WebSocket 鉴权后不查 user.status — 旧 token 12h 内失效后仍可用 | 15436fa |
| High | H4 | login brute-force 无防护 + user enumeration | 15436fa |
| High | H5 | nginx 没限流 + WS access log 写 token 到磁盘 | 15436fa |
| High | H7 | JWT TTL 12h 过长 → 降到 1h | 15436fa |
| High | H9 | KillSwitch cycle 中段 pause 不立即生效 | 15436fa |
| Medium | M1 | DB/Redis 端口暴露公网 | 15436fa |
| Medium | M3 | list endpoint limit 无上限 → DoS | 15436fa |
| Low | L9 | mainnet 关闭 /docs /redoc | 15436fa |

测试: 378 → 407 passed (+29 新单测).

## 老板必须手动执行 (无法代办)

按紧急度排序; 最迟在 dev-server 部署前必须做到 0~3, 上 mainnet 之前必须
做到 0~6 全部.

### 0. **立即** 改 dev-server 的 admin 密码 + 轮换其他网站的同套密码

> **C3 凭据已 effective 公开** — `Alpha123456@#$` 这个密码字符串已被 commit
> 进 git 至少 2 周; 一旦仓库公开/克隆/被扫描, 立即被撞库. 老板这个密码
> 在其他网站的复用账号也建议同时轮换.

SSH 到 dev-server 执行:

```bash
# 1. 编辑 .env.dev-server (这个文件不在 git 里, 是部署时手填的)
nano /path/to/alpha-pilot/.env.dev-server

# 改这三行为新值 (DEFAULT_ADMIN_PASSWORD 用强随机, 至少 16 位混合):
DEFAULT_ADMIN_EMAIL=<new-or-same-email>
DEFAULT_ADMIN_USERNAME=<keep-or-change>
DEFAULT_ADMIN_PASSWORD=<new-strong-password-16+chars>

# 2. 加上两个新强随机密钥 (C1+C2 必须):
echo "APP_AUTH_SECRET_KEY=$(openssl rand -hex 32)" >> .env.dev-server
echo "APP_CONFIG_MASTER_KEY=$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" >> .env.dev-server

# 3. 重启服务让 admin_bootstrap 用新密码同步, 让密钥校验通过
bash scripts/deploy-dev.sh
```

注意: 重启后所有现有 JWT 立即作废 (新密钥签的才认), 你需要重新登录.

### 1. **强烈推荐** 重写 git history 删除 .env.dev-server.example 里的旧凭据

这一步只在仓库公开前做, 私有仓库可不急, 但 push 到 GitHub 公开 repo 之前
必须做 (否则历史 commit 仍然能 log 出旧密码).

仓库当前是私有. 如果计划公开, 先做这一步:

```bash
# 在本地 (不要在 server 上):
cd /path/to/local/clone
git clone --mirror git@github.com:danerlt/alpha-pilot.git ap-mirror.git
cd ap-mirror.git

# 装 git-filter-repo (推荐, 比 BFG 干净)
pip install git-filter-repo

# 用 sed expression 把那三行密码从所有 commit 替换成空
git filter-repo --replace-text <(cat <<'EOF'
danerlt001@gmail.com==>REDACTED
danerlt001==>REDACTED
Alpha123456@#$==>REDACTED
2QJd4n6s8h4R2Q9UjH4o9v1Q0s9PzD8YQkW2M4q8LxA===>REDACTED
EOF
)

# 强推
git push --mirror --force origin
```

注意: 这是破坏性操作, 所有协作者 (如果有) 必须重新 clone. 私有仓库 + 单人
项目情况下风险可控. **如果不做这一步, 旧密码会永远在 git history 里能搜到.**

### 2. **dev-server 部署** SSH 跑 deploy-dev.sh

代码已 push, 直接:

```bash
# SSH 到 dev-server
cd /path/to/alpha-pilot
bash scripts/deploy-dev.sh
```

脚本会自动 git pull + 重建镜像 + alembic upgrade.

启动时如果 .env.dev-server 还没填 APP_AUTH_SECRET_KEY / APP_CONFIG_MASTER_KEY
**容器会启动失败** (post-Plan5 C1+C2 强制必填). 必须先做步骤 0.

### 3. **配置 nginx** 加 limit_req + 安全头 + WS access log 不写 query

`docker/nginx/alpha-pilot.conf` 已经更新了 location 块, 但有些指令必须放在
nginx http{} 块顶层 (server{} 外), 老板手动加到 `/etc/nginx/conf.d/` 某个
配置:

```nginx
# /etc/nginx/conf.d/00-alphapilot-limits.conf
limit_req_zone $binary_remote_addr zone=ap_login:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=ap_api:10m rate=60r/m;

# 自定义 log_format 不写 query string (避免 ws ?token= 泄露到 access log)
log_format ap_log_no_args '$remote_addr - $remote_user [$time_local] '
                          '"$request_method $uri $server_protocol" '
                          '$status $body_bytes_sent "$http_referer" '
                          '"$http_user_agent" "$http_x_forwarded_for"';
```

server{} 块加安全头 (放在已有的 https server 块内):

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
```

然后:

```bash
sudo nginx -t      # 检查配置
sudo nginx -s reload
```

### 4. 测试限流是否生效

```bash
# 应该在第 6 次请求开始返 429
for i in {1..10}; do
  echo "Attempt $i:"
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST https://www.danerlt.top/ap-dev/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"nobody@test","password":"wrong"}'
done
```

### 5. **mainnet 上线前** 生成 prod 专用密钥

```bash
# .env.prod 必须用与 dev 不同的随机密钥
# 不要复用 dev key
echo "APP_AUTH_SECRET_KEY=$(openssl rand -hex 32)" >> .env.prod
echo "APP_CONFIG_MASTER_KEY=$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" >> .env.prod

# 加默认 admin (强口令)
nano .env.prod  # 填 DEFAULT_ADMIN_*
```

### 6. **定期** 检查 nginx access log 是否真的不含 query string

```bash
# 不应出现 ?token= 这种 pattern
sudo tail -100 /var/log/nginx/ap_dev_ws.log
sudo grep "token=" /var/log/nginx/ap_dev_ws.log  # 应为空
```

## 验证清单 (每个步骤完成后跑)

```bash
# C1+C2: 启动时拒默认密钥
docker compose -f docker/docker-compose.dev-server.yml logs backend | grep "Refusing to start"
# 应该没有 (因为已填强随机), 如果有就是密钥还没填

# C4: runtime config 现在要 admin
curl -s -o /dev/null -w "%{http_code}\n" https://www.danerlt.top/ap-dev/api/config/runtime
# 应该 401

# C5: register 已禁
curl -s -X POST https://www.danerlt.top/ap-dev/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"x","email":"x@y.com","password":"strongpass123"}'
# 应该 403

# H1: 用旧 (12h 前签的) token 连 ws 应该被拒
# (难自动测, 等下次重启自然观察)

# H4: 限流
# 见步骤 4

# L9: mainnet 关 docs (testnet 不影响)
curl -s -o /dev/null -w "%{http_code}\n" https://www.danerlt.top/ap/docs
# mainnet 应 404
curl -s -o /dev/null -w "%{http_code}\n" https://www.danerlt.top/ap-dev/docs
# dev 应 200
```

## 后续 V0.1.x 安全跟进

| 项 | 描述 | 优先级 |
|----|------|--------|
| H2 | account_id 隔离: positions/trades/decisions/risk-events/catchup/ws 全按 user.account_id 过滤 (V0.1.x 引入第二账户前) | 中 |
| H7+ | JWT 加 jti 撤销表 + logout 端点 + sliding window refresh | 中 |
| H10 | manual_close_all 改 sub-transaction 防"一仓失败回滚整批" + Position 加乐观锁 | 中 |
| M2 | AuditLog 写入 ip + user_agent | 低 |
| L3 | WebSocket per-IP/user 连接数上限 + 心跳超时 | 低 |
| L1 | Docker 容器跑非 root | 低 |
| L2 | 密码 hash 升级 argon2id | 低 |
| FA - | 引入第二账户时务必把 H2 + H3 的 IDOR 一起补 (commands.close-all body.account_id 不要从 client 传) | 中 |

## 对应 commit

```
ea0dfa2  C1-C6 critical 安全审计 6 项
15436fa  H1/H4/H5/H7/H9 + M1/M3 + L9 — 8 项部署纵深
```

# dev 前端切换 webapp 接管 /ap-dev —— 服务器落地记录

- 时间：2026-07-06 晚
- 对应代码：`95a8e68`（老板提交：dev 下线 Next.js frontend，webapp 直接挂 /ap-dev）
- 执行者：服务器 Claude Code

## 做了什么

1. **部署**：push 后 CI 自动部署 `95a8e68`（backend/scheduler/webapp 三 service），
   `current.tag` 翻转确认；未手动重跑 deploy 脚本（避免与 CI 撞车）。
2. **清孤儿**：compose 删除 frontend service 后残留 `ap-dev-frontend-1`（deploy 脚本 `up -d`
   不带 `--remove-orphans`），在部署目录以 `IMAGE_TAG/WEBAPP_TAG=current.tag` 补跑
   `up -d --remove-orphans` 清掉（副作用：三 service 被重建一次，restarts=0 无 crash-loop）。
3. **nginx**（`/etc/nginx/conf.d/openclaw.conf`，备份 `openclaw.conf.bak-20260706`）：
   - `location /ap-dev`（→3001）删除，改为 `location = /ap-dev { return 301 /ap-dev/; }`；
   - 新增 `location /ap-dev/ { proxy_pass http://127.0.0.1:3004/; }`（带斜杠剥前缀）；
   - 删除 `/ap-dev-next` 两段；`nginx -t` + reload。

## 如何验证（全过）

- `https://www.danerlt.top/ap-dev/api/health` → success envelope（api/ws 前缀更长优先匹配，未受影响）
- `/ap-dev` → 301 → `/ap-dev/` → 200（webapp）；SPA `/ap-dev/login` → 200
- `/ap-dev/config.js` → `apiBaseUrl:"/ap-dev"`、`basePath:"/ap-dev"`
- WS：`/ap-dev/ws` 经 nginx 握手 101（首测 502 为容器重建启动窗口的瞬态，重测即过）
- `/ap-dev-next/` 不再代理到 webapp（落到站点默认 upstream）
- scheduler 日志：`APScheduler started` + `runtime settings loaded from DB`

## 备注 / 待办

- deploy 脚本 `_up()` 不带 `--remove-orphans`：下次再有 service 下线仍会留孤儿，
  可考虑在 `deploy_common.sh` 补该参数（本次未动脚本）。
- 浏览器端登录后 WS 事件流实测留给老板（路由层握手已验证）。
- Binance testnet Key 失效（-2015）老板知晓，暂不处理。

/**
 * WS 令牌内存持有 —— 后端 WS 握手只认 `?token=`（不读 cookie，缺口已写档）。
 * 登录响应的 access_token 仅存内存（不落 storage）；页面刷新后丢失 →
 * WS 实时降级直到重新登录，REST 不受影响（cookie 会话仍在）。
 */
let wsToken: string | null = null;

export function setWsToken(token: string | null): void {
  wsToken = token;
}

export function getWsToken(): string | null {
  return wsToken;
}

/** 路由守卫 —— 未登录（/api/auth/me 失败）一律重定向 /login。 */
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useMe } from "./auth";

export function RequireAuth() {
  const { data: user, isLoading, isError } = useMe();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-bg-0">
        <span className="font-mono text-sm text-fg-4">验证登录态…</span>
      </div>
    );
  }
  if (isError || !user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <Outlet />;
}

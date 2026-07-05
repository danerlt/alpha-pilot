/**
 * 权限 hook —— 矩阵由后端 `/api/admin/roles` 下发（前端不留第二份真相），
 * 结合当前用户角色判定；矩阵未加载完成时保守返回 false（禁用写入口）。
 */
import { usePermissions } from "@/api/queries";
import { useMe } from "./auth";

export function usePermission() {
  const { data: user } = useMe();
  const { data: matrix } = usePermissions();

  const can = (key: string): boolean => {
    if (!user || !matrix) return false;
    const row = matrix.find((p) => p.key === key);
    if (!row) return false;
    return row.granted[user.role] === true;
  };

  return { can, role: user?.role ?? null, user: user ?? null };
}

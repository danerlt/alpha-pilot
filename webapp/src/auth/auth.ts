/**
 * 认证状态 —— 会话由 httpOnly cookie 承载（后端 B3），前端不存 token；
 * `/api/auth/me` 是登录态唯一判据（mock 下 MSW 用 sessionStorage 模拟会话）。
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { authApi } from "@/api/services";
import type { User } from "@/api/types";

export const AUTH_ME_KEY = ["auth", "me"] as const;

export function useMe() {
  return useQuery<User>({
    queryKey: AUTH_ME_KEY,
    queryFn: authApi.me,
    retry: false,
    staleTime: 5 * 60_000,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      authApi.login(email, password),
    onSuccess: (user) => {
      queryClient.setQueryData(AUTH_ME_KEY, user);
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: authApi.logout,
    onSettled: () => {
      queryClient.setQueryData(AUTH_ME_KEY, null);
      queryClient.removeQueries({ queryKey: AUTH_ME_KEY });
    },
  });
}

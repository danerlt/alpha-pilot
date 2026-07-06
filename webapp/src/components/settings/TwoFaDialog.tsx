/**
 * 2FA 开启/关闭弹窗（handoff 3.7）——
 * 开启：setup 拿 secret+otpauth_uri → 用户扫码/手输 → verify 动态码开启；
 * 关闭：输入当前动态码 disable。secret 明文只在本弹窗生命周期内展示。
 */
import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { authApi } from "@/api/services";
import { AUTH_ME_KEY } from "@/auth/auth";

export function TwoFaDialog({
  open,
  mode,
  onClose,
}: {
  open: boolean;
  mode: "enable" | "disable";
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [secret, setSecret] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) {
      setSecret(null);
      setCode("");
      setError("");
      return;
    }
    if (mode === "enable") {
      authApi
        .twoFaSetup()
        .then((r) => setSecret(r.secret))
        .catch((e) => setError(e instanceof Error ? e.message : "初始化失败"));
    }
  }, [open, mode]);

  const submit = async () => {
    if (code.length !== 6) return;
    setBusy(true);
    setError("");
    try {
      if (mode === "enable") await authApi.twoFaVerify(code);
      else await authApi.twoFaDisable(code);
      await queryClient.invalidateQueries({ queryKey: AUTH_ME_KEY });
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "动态码校验失败");
      setCode("");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={mode === "enable" ? "开启双重验证" : "关闭双重验证"}
    >
      <div className="flex flex-col gap-4">
        {mode === "enable" ? (
          <>
            <div className="text-sm leading-relaxed text-fg-2">
              在验证器 App（Google Authenticator / 1Password 等）中添加密钥，随后输入其显示的 6 位动态码完成绑定。
            </div>
            <div className="flex flex-col gap-1.5">
              <div className="text-xs text-fg-3">手动输入密钥：</div>
              <div className="break-all rounded-sm border border-line bg-bg-4 px-3 py-2.5 font-mono text-sm text-fg-1">
                {secret ?? "获取中…"}
              </div>
            </div>
          </>
        ) : (
          <div className="text-sm leading-relaxed text-fg-2">
            关闭后登录将不再需要二次验证，账户安全性降低。请输入当前验证器动态码确认。
          </div>
        )}
        <div className="flex flex-col gap-1.5">
          <div className="text-xs text-fg-3">6 位动态码</div>
          <input
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
            inputMode="numeric"
            placeholder="000000"
            autoFocus
            className="rounded-sm border border-line bg-bg-4 px-3 py-2 text-center font-mono text-lg tracking-[.3em] text-fg-1 outline-none focus:border-mint"
          />
        </div>
        {error && <div className="text-xs text-rose">{error}</div>}
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>
            取消
          </Button>
          <Button
            variant={mode === "enable" ? "primary" : "danger"}
            disabled={code.length !== 6 || busy || (mode === "enable" && !secret)}
            onClick={submit}
          >
            {busy ? "验证中…" : mode === "enable" ? "确认开启" : "确认关闭"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}

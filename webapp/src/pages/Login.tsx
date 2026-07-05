/**
 * 登录 / 注册 / 2FA（handoff/02 P1）—— 左品牌面板 + 右表单，双栏满屏，无 PageShell。
 * 2FA 六位逐格输入：自动跳格、全满自动提交。
 */
import { useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ChevronLeft, Eye, Lock, Mail, Shield } from "lucide-react";
import { useLogin } from "@/auth/auth";

type Mode = "login" | "register" | "twofa";

function AuthInput({
  icon: Icon,
  type = "text",
  value,
  onChange,
  placeholder,
  autoFocus,
}: {
  icon: typeof Mail;
  type?: string;
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
  autoFocus?: boolean;
}) {
  const [focus, setFocus] = useState(false);
  const [show, setShow] = useState(false);
  const isPw = type === "password";
  return (
    <div className="relative flex items-center">
      <Icon size={15} className={`absolute left-[13px] ${focus ? "text-mint" : "text-fg-4"}`} />
      <input
        type={isPw && show ? "text" : type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        autoFocus={autoFocus}
        onFocus={() => setFocus(true)}
        onBlur={() => setFocus(false)}
        className={`box-border w-full rounded-[11px] border bg-bg-2 py-[13px] pl-10 text-sm text-fg-1 outline-none transition-all duration-150 placeholder:text-fg-5 ${
          focus ? "border-mint" : "border-line"
        }`}
        style={{
          boxShadow: focus ? "0 0 0 3px rgba(0,211,149,.1)" : "none",
          paddingRight: isPw ? 44 : 14,
        }}
      />
      {isPw && (
        <button
          onClick={() => setShow((s) => !s)}
          className="absolute right-[13px] flex cursor-pointer"
          tabIndex={-1}
        >
          <Eye size={15} className={show ? "text-mint" : "text-fg-4"} />
        </button>
      )}
    </div>
  );
}

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const login = useLogin();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");
  const [pw2, setPw2] = useState("");
  const [error, setError] = useState("");
  const [registered, setRegistered] = useState(false);
  const [code, setCode] = useState<string[]>(["", "", "", "", "", ""]);
  const codeRefs = useRef<(HTMLInputElement | null)[]>([]);

  const dest = (location.state as { from?: string } | null)?.from ?? "/";

  const submit = () => {
    setError("");
    if (!email || !pw) {
      setError("请输入邮箱和密码");
      return;
    }
    if (mode === "register") {
      if (pw !== pw2) {
        setError("两次输入的密码不一致");
        return;
      }
      setRegistered(true);
      return;
    }
    // 密码校验通过后进入 2FA；会话在 2FA 全满时建立
    login.mutate(
      { email, password: pw },
      {
        onSuccess: () => setMode("twofa"),
        onError: (e) => setError(e instanceof Error ? e.message : "登录失败"),
      },
    );
  };

  const demoLogin = () => {
    login.mutate(
      { email: "demo@alphapilot.local", password: "demo" },
      {
        onSuccess: () => navigate(dest, { replace: true }),
        onError: (e) => setError(e instanceof Error ? e.message : "登录失败"),
      },
    );
  };

  const onCode = (i: number, v: string) => {
    if (!/^[0-9]?$/.test(v)) return;
    const next = [...code];
    next[i] = v;
    setCode(next);
    if (v && i < 5) codeRefs.current[i + 1]?.focus();
    if (next.every((c) => c !== ""))
      setTimeout(() => navigate(dest, { replace: true }), 350);
  };

  return (
    <div className="fixed inset-0 z-[100] flex bg-bg-0">
      {/* 左品牌面板 */}
      <div className="relative flex min-w-0 flex-1 flex-col justify-between overflow-hidden px-14 py-12">
        <svg className="absolute inset-0 h-full w-full opacity-35">
          <defs>
            <pattern id="authgrid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="var(--ap-line-soft)" strokeWidth="1" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#authgrid)" />
        </svg>
        <div className="relative flex items-center gap-2.5">
          <div
            className="flex h-9 w-9 items-center justify-center rounded-[9px] text-[17px] font-extrabold text-bg-0"
            style={{ background: "linear-gradient(135deg,var(--ap-mint),var(--ap-violet))" }}
          >
            α
          </div>
          <span className="text-[17px] font-bold text-fg-1">
            Alpha<span className="text-mint">Pilot</span>
          </span>
        </div>
        <div className="relative max-w-[440px]">
          <div className="mb-4 text-[34px] font-bold leading-[1.25] tracking-[-.03em] text-fg-1">
            AI 自主交易
            <br />
            <span className="text-mint">在边界内</span>运行
          </div>
          <div className="text-sm leading-[1.7] text-fg-3">
            结构化决策 · 硬风控守卫 · 执行闭环 · 受控进化。
            <br />
            不是又一个发信号的助手，而是可托付的交易系统。
          </div>
          <div className="mt-7 flex gap-4">
            {(
              [
                ["85", "累计交易"],
                ["57%", "胜率"],
                ["1.84", "Sharpe"],
                ["−4.2%", "最大回撤"],
              ] as const
            ).map(([v, l]) => (
              <div key={l}>
                <div className="font-mono text-h2 font-bold text-fg-1">{v}</div>
                <div className="mt-0.5 text-[10.5px] text-fg-4">{l}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="relative font-mono text-xs text-fg-5">
          Binance 现货 · Testnet & Mainnet · v0.1
        </div>
      </div>

      {/* 右表单面板 */}
      <div className="flex w-[460px] shrink-0 flex-col justify-center border-l border-line bg-bg-1 px-14">
        {mode !== "twofa" ? (
          registered ? (
            <>
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-[11px] bg-mint-soft">
                <Shield size={20} className="text-mint" />
              </div>
              <div className="mb-1.5 text-h2 font-bold text-fg-1">注册申请已提交</div>
              <div className="mb-7 text-sm leading-relaxed text-fg-3">
                账户处于 <b className="text-amber">待批准</b> 状态。管理员批准并分配角色后，你将收到邮件通知，届时即可登录。
              </div>
              <button
                onClick={() => {
                  setRegistered(false);
                  setMode("login");
                }}
                className="w-full cursor-pointer rounded-[11px] border border-line bg-bg-2 py-3 text-sm font-semibold text-fg-2"
              >
                返回登录
              </button>
            </>
          ) : (
            <>
              <div className="mb-1.5 text-h2 font-bold text-fg-1">
                {mode === "login" ? "欢迎回来" : "创建账户"}
              </div>
              <div className="mb-7 text-sm text-fg-3">
                {mode === "login" ? "登录以进入你的交易控制台" : "注册后需管理员批准并分配角色"}
              </div>
              <div className="flex flex-col gap-3">
                <AuthInput icon={Mail} value={email} onChange={setEmail} placeholder="邮箱" autoFocus />
                <AuthInput icon={Lock} type="password" value={pw} onChange={setPw} placeholder="密码" />
                {mode === "register" && (
                  <AuthInput icon={Lock} type="password" value={pw2} onChange={setPw2} placeholder="确认密码" />
                )}
              </div>
              {error && <div className="mt-2.5 text-xs text-rose">{error}</div>}
              {mode === "login" && (
                <div className="mt-2.5 text-right">
                  <span className="cursor-pointer text-xs text-fg-4">忘记密码？</span>
                </div>
              )}
              <button
                onClick={submit}
                disabled={login.isPending}
                className="mt-[22px] w-full cursor-pointer rounded-[11px] border-none bg-mint py-[13px] text-sm font-bold text-bg-0 hover:brightness-110 disabled:opacity-50"
              >
                {login.isPending ? "验证中…" : mode === "login" ? "登录" : "注册"}
              </button>
              <div className="my-[22px] flex items-center gap-3">
                <div className="h-px flex-1 bg-line-soft" />
                <span className="text-xs text-fg-5">或</span>
                <div className="h-px flex-1 bg-line-soft" />
              </div>
              <button
                onClick={demoLogin}
                disabled={login.isPending}
                className="w-full cursor-pointer rounded-[11px] border border-line bg-bg-2 py-3 text-sm font-semibold text-fg-2 hover:text-fg-1 disabled:opacity-50"
              >
                以演示账户进入 →
              </button>
              <div className="mt-6 text-center text-[12.5px] text-fg-4">
                {mode === "login" ? "还没有账户？" : "已有账户？"}
                <button
                  onClick={() => {
                    setMode(mode === "login" ? "register" : "login");
                    setError("");
                  }}
                  className="ml-1.5 cursor-pointer font-semibold text-mint"
                >
                  {mode === "login" ? "注册" : "登录"}
                </button>
              </div>
            </>
          )
        ) : (
          <>
            <button
              onClick={() => setMode("login")}
              className="mb-[26px] flex cursor-pointer items-center gap-1.5 text-xs text-fg-4"
            >
              <ChevronLeft size={12} /> 返回
            </button>
            <div className="mb-[18px] flex h-11 w-11 items-center justify-center rounded-[11px] bg-mint-soft">
              <Shield size={20} className="text-mint" />
            </div>
            <div className="mb-1.5 text-h2 font-bold text-fg-1">双重验证</div>
            <div className="mb-[26px] text-sm text-fg-3">
              输入验证器 App 中的 6 位动态码
              <br />
              <span className="font-mono text-xs text-fg-4">mock 模式：输入任意 6 位数字</span>
            </div>
            <div className="mb-6 flex gap-2.5">
              {code.map((c, i) => (
                <input
                  key={i}
                  ref={(el) => (codeRefs.current[i] = el)}
                  value={c}
                  onChange={(e) => onCode(i, e.target.value)}
                  autoFocus={i === 0}
                  maxLength={1}
                  inputMode="numeric"
                  className={`h-14 w-12 rounded-[11px] border bg-bg-2 text-center font-mono text-[22px] font-bold text-fg-1 outline-none ${
                    c ? "border-mint" : "border-line"
                  }`}
                />
              ))}
            </div>
            <div className="text-xs text-fg-4">
              收不到验证码？
              <span className="cursor-pointer font-semibold text-mint">使用恢复码</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

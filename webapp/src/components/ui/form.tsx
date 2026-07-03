/** 设置页表单原子 —— 对齐设计稿 settings.jsx 的 SField/SInput/SMasked/SSwitch/SSeg/SSelect/STestBtn */
import { useState, type ReactNode } from "react";
import { Check, ChevronDown, X } from "lucide-react";
import { Dot } from "./atoms";

export function Field({
  label,
  hint,
  children,
}: {
  label: ReactNode;
  hint?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="mb-3.5 flex flex-col gap-1.5">
      <div className="flex flex-wrap items-center gap-2 text-xs font-semibold leading-normal tracking-[.04em] text-fg-3">
        {label}
        {hint && <span className="font-normal tracking-normal text-fg-4">{hint}</span>}
      </div>
      {children}
    </div>
  );
}

export function Input({
  value,
  onChange,
  placeholder,
  mono = true,
  type = "text",
  right,
  readOnly = false,
}: {
  value: string;
  onChange?: (v: string) => void;
  placeholder?: string;
  mono?: boolean;
  type?: string;
  right?: ReactNode;
  readOnly?: boolean;
}) {
  const [focus, setFocus] = useState(false);
  return (
    <div className="relative flex items-center">
      <input
        type={type}
        value={value}
        readOnly={readOnly}
        onChange={(e) => onChange?.(e.target.value)}
        placeholder={placeholder}
        onFocus={() => setFocus(true)}
        onBlur={() => setFocus(false)}
        className={`box-border w-full rounded-[10px] border bg-bg-3 px-[13px] py-[11px] text-sm text-fg-1 outline-none transition-all duration-150 placeholder:text-fg-5 ${
          mono ? "font-mono" : ""
        } ${focus ? "border-mint" : "border-line"}`}
        style={{
          boxShadow: focus ? "0 0 0 3px rgba(0,211,149,.12)" : "none",
          paddingRight: right ? 78 : 13,
        }}
      />
      {right && <div className="absolute right-2">{right}</div>}
    </div>
  );
}

export function MaskedInput({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange?: (v: string) => void;
  placeholder?: string;
}) {
  const [show, setShow] = useState(false);
  return (
    <Input
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      type={show ? "text" : "password"}
      right={
        <button
          onClick={() => setShow((s) => !s)}
          className="cursor-pointer rounded-xs border border-line bg-bg-4 px-2 py-1 font-mono text-micro text-fg-3"
        >
          {show ? "隐藏" : "显示"}
        </button>
      }
    />
  );
}

export function Switch({ on, onToggle }: { on: boolean; onToggle: () => void }) {
  return (
    <button
      onClick={onToggle}
      role="switch"
      aria-checked={on}
      className={`relative h-6 w-[42px] shrink-0 cursor-pointer rounded-pill transition-colors duration-150 ${
        on ? "bg-mint" : "bg-bg-4"
      }`}
    >
      <span
        className="absolute top-[3px] h-[18px] w-[18px] rounded-full bg-fg-1 transition-all duration-150"
        style={{ left: on ? 21 : 3 }}
      />
    </button>
  );
}

export function Segmented<T extends string>({
  options,
  value,
  onChange,
}: {
  options: { v: T; l: string; dot?: string }[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <div className="inline-flex rounded-[9px] border border-line bg-bg-3 p-[3px]">
      {options.map((o) => (
        <button
          key={o.v}
          onClick={() => onChange(o.v)}
          className={`flex cursor-pointer items-center gap-1.5 rounded-xs px-3.5 py-1.5 text-xs font-medium transition-colors duration-150 ${
            value === o.v ? "bg-bg-4 text-fg-1" : "text-fg-3"
          }`}
        >
          {o.dot && <Dot color={o.dot} glow={value === o.v} />}
          {o.l}
        </button>
      ))}
    </div>
  );
}

export function Select({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (v: string) => void;
  options: { v: string; l: string }[];
}) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full cursor-pointer appearance-none rounded-[10px] border border-line bg-bg-3 py-[11px] pl-[13px] pr-9 text-sm text-fg-1 outline-none"
      >
        {options.map((o) => (
          <option key={o.v} value={o.v} className="bg-bg-2">
            {o.l}
          </option>
        ))}
      </select>
      <ChevronDown
        size={14}
        className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-fg-3"
      />
    </div>
  );
}

export type TestState = "idle" | "testing" | "ok" | "fail";

export function TestButton({
  state,
  onTest,
}: {
  state: TestState;
  onTest: () => void;
}) {
  const cfg = {
    idle: { l: "测试连接", cls: "bg-bg-4 text-fg-1 border-line" },
    testing: { l: "测试中…", cls: "bg-bg-4 text-fg-3 border-line" },
    ok: { l: "连接成功", cls: "bg-mint-soft text-mint border-mint" },
    fail: { l: "连接失败", cls: "bg-rose-soft text-rose border-rose" },
  }[state];
  return (
    <button
      onClick={onTest}
      disabled={state === "testing"}
      className={`flex cursor-pointer items-center gap-1.5 rounded-[9px] border px-4 py-[9px] text-xs font-semibold ${cfg.cls}`}
    >
      {state === "ok" && <Check size={13} strokeWidth={2.4} />}
      {state === "fail" && <X size={13} strokeWidth={2.4} />}
      {state === "testing" && (
        <span className="h-1.5 w-1.5 rounded-full bg-current" style={{ animation: "apblink 1s infinite" }} />
      )}
      {cfg.l}
    </button>
  );
}

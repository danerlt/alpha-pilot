import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "ghost" | "danger" | "violet" | "subtle";

const variants: Record<Variant, string> = {
  primary:
    "bg-mint text-bg-0 font-semibold hover:brightness-110 border border-transparent",
  ghost:
    "bg-transparent text-fg-2 border border-line hover:bg-bg-3 hover:text-fg-1",
  subtle: "bg-bg-3 text-fg-2 border border-line-soft hover:bg-bg-4",
  danger:
    "bg-rose-soft text-rose border border-rose/30 hover:bg-rose hover:text-fg-1",
  violet:
    "bg-violet-soft text-violet border border-violet/35 hover:brightness-110",
};

export function Button({
  variant = "ghost",
  size = "md",
  className = "",
  children,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: "sm" | "md";
  children: ReactNode;
}) {
  const pad = size === "sm" ? "px-2.5 py-1 text-xs" : "px-3.5 py-1.5 text-sm";
  return (
    <button
      className={`inline-flex cursor-pointer items-center justify-center gap-1.5 rounded-sm font-medium transition-all duration-150 ease-ap active:scale-[0.98] disabled:pointer-events-none disabled:opacity-40 ${pad} ${variants[variant]} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}

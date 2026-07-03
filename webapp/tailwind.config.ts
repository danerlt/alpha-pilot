import type { Config } from "tailwindcss";

/**
 * Tailwind 只做 CSS 变量映射，权威 token 源是 src/styles/design-system.css。
 * 业务代码禁止硬编码色值 —— 一律使用下面映射出的语义类。
 */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    colors: {
      transparent: "transparent",
      current: "currentColor",
      inherit: "inherit",
      bg: {
        0: "var(--ap-bg-0)",
        1: "var(--ap-bg-1)",
        2: "var(--ap-bg-2)",
        3: "var(--ap-bg-3)",
        4: "var(--ap-bg-4)",
      },
      fg: {
        1: "var(--ap-fg-1)",
        2: "var(--ap-fg-2)",
        3: "var(--ap-fg-3)",
        4: "var(--ap-fg-4)",
        5: "var(--ap-fg-5)",
      },
      line: {
        DEFAULT: "var(--ap-line)",
        soft: "var(--ap-line-soft)",
      },
      mint: {
        DEFAULT: "var(--ap-mint)",
        soft: "var(--ap-mint-soft)",
        dim: "var(--ap-mint-dim)",
      },
      rose: {
        DEFAULT: "var(--ap-rose)",
        soft: "var(--ap-rose-soft)",
        dim: "var(--ap-rose-dim)",
      },
      violet: {
        DEFAULT: "var(--ap-violet)",
        soft: "var(--ap-violet-soft)",
      },
      amber: {
        DEFAULT: "var(--ap-amber)",
        soft: "var(--ap-amber-soft)",
      },
      cyan: {
        DEFAULT: "var(--ap-cyan)",
        soft: "var(--ap-cyan-soft)",
      },
    },
    fontFamily: {
      sans: "var(--ap-font-sans)",
      mono: "var(--ap-font-mono)",
    },
    fontSize: {
      display: ["32px", { lineHeight: "1.1", letterSpacing: "-0.03em" }],
      h1: ["24px", { lineHeight: "1.2", letterSpacing: "-0.02em" }],
      h2: ["20px", { lineHeight: "1.25", letterSpacing: "-0.01em" }],
      h3: ["17px", { lineHeight: "1.3" }],
      body: ["15px", { lineHeight: "1.5" }],
      sm: ["13px", { lineHeight: "1.45" }],
      xs: ["11px", { lineHeight: "1.4" }],
      micro: ["10px", { lineHeight: "1.35" }],
    },
    borderRadius: {
      none: "0",
      xs: "var(--ap-r-xs)",
      sm: "var(--ap-r-sm)",
      md: "var(--ap-r-md)",
      lg: "var(--ap-r-lg)",
      xl: "var(--ap-r-xl)",
      pill: "var(--ap-r-pill)",
      full: "9999px",
    },
    boxShadow: {
      1: "var(--ap-shadow-1)",
      2: "var(--ap-shadow-2)",
      3: "var(--ap-shadow-3)",
      "glow-mint": "var(--ap-shadow-glow-mint)",
      "glow-rose": "var(--ap-shadow-glow-rose)",
      none: "none",
    },
    extend: {
      spacing: {
        // --ap-s-1..8 与 Tailwind 默认 4px 基数刻度一致，无需覆盖
      },
      transitionTimingFunction: {
        ap: "cubic-bezier(0.4, 0, 0.2, 1)",
      },
    },
  },
  plugins: [],
} satisfies Config;

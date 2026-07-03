/**
 * 设置（handoff/02 P11）—— 四分区：交易所连接 / AI 模型 / 通知 / 账户偏好。
 * 密钥只显示脱敏值；紧急停止 = close-all + 暂停引擎（requireText 二次确认）。
 */
import { useState } from "react";
import {
  AlertTriangle,
  Bell,
  BrainCircuit,
  Check,
  Layers,
  Settings as SettingsIcon,
} from "lucide-react";
import { PageShell } from "@/components/shell/PageShell";
import { Card, Pill } from "@/components/ui/atoms";
import {
  Field,
  Input,
  MaskedInput,
  Segmented,
  Select,
  Switch,
  TestButton,
  type TestState,
} from "@/components/ui/form";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { commandsApi } from "@/api/services";

type Tab = "exchange" | "llm" | "notify" | "account";

const TABS: { id: Tab; label: string; icon: typeof Layers }[] = [
  { id: "exchange", label: "交易所连接", icon: Layers },
  { id: "llm", label: "AI 模型", icon: BrainCircuit },
  { id: "notify", label: "通知", icon: Bell },
  { id: "account", label: "账户偏好", icon: SettingsIcon },
];

export default function Settings() {
  const [tab, setTab] = useState<Tab>("exchange");
  return (
    <PageShell title="设置" sub="SETTINGS">
      <div className="flex max-w-[1000px] gap-6">
        {/* 子导航 */}
        <div className="flex w-[200px] shrink-0 flex-col gap-0.5">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex cursor-pointer items-center gap-2.5 rounded-[9px] border px-3 py-2.5 text-left text-sm font-medium ${
                tab === t.id
                  ? "border-line-soft bg-bg-2 text-fg-1"
                  : "border-transparent text-fg-3 hover:text-fg-2"
              }`}
            >
              <t.icon size={15} className={tab === t.id ? "text-mint" : "text-current"} />
              {t.label}
            </button>
          ))}
        </div>
        {/* 内容 */}
        <div className="flex min-w-0 flex-1 flex-col gap-5">
          {tab === "exchange" && <ExchangeSection />}
          {tab === "llm" && <LlmSection />}
          {tab === "notify" && <NotifySection />}
          {tab === "account" && <AccountSection />}
        </div>
      </div>
    </PageShell>
  );
}

// ---------- 交易所 ----------
function ExchangeSection() {
  const [net, setNet] = useState<"mainnet" | "testnet">("testnet");
  const [test, setTest] = useState<TestState>("idle");
  const [key, setKey] = useState("bnx_test_8a3f2c91d4e7");
  const [secret, setSecret] = useState("****************3f2a");
  const isTestnet = net === "testnet";
  const runTest = () => {
    setTest("testing");
    setTimeout(() => setTest("ok"), 1200);
  };
  return (
    <>
      <Card title="交易所">
        <div className="flex gap-3">
          {[
            { id: "binance", name: "Binance", sub: "USDT 现货 · MVP 首选", active: true },
            { id: "hyperliquid", name: "Hyperliquid", sub: "去中心化 · 钱包授权", active: false },
          ].map((ex) => (
            <div
              key={ex.id}
              className={`relative flex-1 cursor-pointer rounded-md border bg-bg-3 p-4 ${
                ex.active ? "border-mint" : "border-line-soft"
              }`}
            >
              {ex.active && (
                <div className="absolute right-3 top-3">
                  <Pill tone="mint">已连接</Pill>
                </div>
              )}
              <div className="mb-0.5 text-sm font-semibold text-fg-1">{ex.name}</div>
              <div className="text-xs text-fg-3">{ex.sub}</div>
            </div>
          ))}
        </div>
      </Card>

      <Card title="Binance · 网络与 API" right={<TestButton state={test} onTest={runTest} />}>
        <Field
          label="运行网络"
          hint={isTestnet ? "· 测试盘使用模拟资金，安全演练" : "· 主网为真实资金交易，请谨慎"}
        >
          <Segmented
            value={net}
            onChange={(v) => {
              setNet(v);
              setTest("idle");
            }}
            options={[
              { v: "mainnet", l: "主网 Mainnet", dot: "var(--ap-rose)" },
              { v: "testnet", l: "测试网 Testnet", dot: "var(--ap-cyan)" },
            ]}
          />
        </Field>

        {isTestnet ? (
          <div className="mb-3.5 flex items-start gap-2 rounded-sm border border-cyan/20 bg-cyan-soft px-3 py-2.5">
            <AlertTriangle size={14} className="mt-px shrink-0 text-cyan" />
            <span className="text-xs leading-normal text-fg-2">
              当前为 <b className="text-cyan">测试网</b>。所有成交为模拟，不涉及真实资金。建议先在测试网验证策略，再切主网。
            </span>
          </div>
        ) : (
          <div className="mb-3.5 flex items-start gap-2 rounded-sm border border-rose/20 bg-rose-soft px-3 py-2.5">
            <AlertTriangle size={14} className="mt-px shrink-0 text-rose" />
            <span className="text-xs leading-normal text-fg-2">
              当前为 <b className="text-rose">主网</b>，AI 将使用真实资金下单。请确认 API 仅开启「现货交易」权限，
              <b>切勿</b>开启「提现」权限。
            </span>
          </div>
        )}

        <Field label="API Key">
          <Input value={key} onChange={setKey} placeholder="输入 Binance API Key" />
        </Field>
        <Field label="API Secret">
          <MaskedInput value={secret} onChange={setSecret} placeholder="输入 Binance API Secret" />
        </Field>

        <Field label="权限校验" hint="· 自动检测 API 权限范围">
          <div className="flex flex-col gap-1.5">
            {[
              { l: "读取账户与持仓", ok: true, wantOff: false },
              { l: "现货交易（下单/撤单）", ok: true, wantOff: false },
              { l: "提现权限", ok: false, wantOff: true },
            ].map((p) => (
              <div key={p.l} className="flex items-center gap-2 rounded-sm bg-bg-3 px-3 py-2 text-xs">
                <span
                  className={`flex h-4 w-4 items-center justify-center rounded-[4px] ${
                    p.wantOff
                      ? p.ok
                        ? "bg-rose-soft"
                        : "bg-mint-soft"
                      : p.ok
                        ? "bg-mint-soft"
                        : "bg-bg-4"
                  }`}
                >
                  {p.wantOff && p.ok ? (
                    <AlertTriangle size={11} strokeWidth={2.6} className="text-rose" />
                  ) : (
                    <Check
                      size={11}
                      strokeWidth={2.6}
                      className={p.ok || p.wantOff ? "text-mint" : "text-fg-4"}
                    />
                  )}
                </span>
                <span className={`flex-1 ${p.wantOff && p.ok ? "text-rose" : "text-fg-2"}`}>
                  {p.l}
                </span>
                {p.wantOff && !p.ok && (
                  <span className="font-mono text-micro text-mint">已关闭</span>
                )}
                {p.wantOff && p.ok && (
                  <span className="font-mono text-micro text-rose">建议关闭</span>
                )}
              </div>
            ))}
          </div>
        </Field>

        <div className="mt-1.5 flex gap-2">
          <button className="cursor-pointer rounded-[10px] border-none bg-mint px-[18px] py-2.5 text-sm font-bold text-bg-0 hover:brightness-110">
            保存配置
          </button>
          <button className="cursor-pointer rounded-[10px] border border-line bg-bg-3 px-[18px] py-2.5 text-sm font-medium text-fg-2">
            断开连接
          </button>
        </div>
      </Card>
    </>
  );
}

// ---------- LLM ----------
const PROVIDERS = {
  deepseek: { models: ["deepseek-chat", "deepseek-reasoner"], base: "https://api.deepseek.com/v1", rec: true },
  openai: { models: ["gpt-5", "o1", "gpt-4o"], base: "https://api.openai.com/v1", rec: false },
  anthropic: { models: ["claude-sonnet-4.5", "claude-opus-4.1"], base: "https://api.anthropic.com/v1", rec: false },
  custom: { models: ["custom-model"], base: "https://your-endpoint/v1", rec: false },
} as const;

type Provider = keyof typeof PROVIDERS;

function LlmSection() {
  const [provider, setProvider] = useState<Provider>("deepseek");
  const [model, setModel] = useState("deepseek-chat");
  const [test, setTest] = useState<TestState>("idle");
  const [temp, setTemp] = useState(0.3);
  const [key, setKey] = useState("sk-****************a1b2");
  const [maxTokens, setMaxTokens] = useState("4096");
  const [timeout_, setTimeout_] = useState("30");
  const cur = PROVIDERS[provider];
  const runTest = () => {
    setTest("testing");
    setTimeout(() => setTest("ok"), 1100);
  };
  return (
    <>
      <Card title="模型提供方">
        <div className="grid grid-cols-2 gap-2.5 min-[800px]:grid-cols-4">
          {(
            [
              { id: "deepseek", l: "DeepSeek", sub: "性价比首选" },
              { id: "openai", l: "OpenAI", sub: "GPT-5 / o1" },
              { id: "anthropic", l: "Anthropic", sub: "Claude" },
              { id: "custom", l: "自定义", sub: "兼容 OpenAI" },
            ] as { id: Provider; l: string; sub: string }[]
          ).map((p) => (
            <button
              key={p.id}
              onClick={() => {
                setProvider(p.id);
                setModel(PROVIDERS[p.id].models[0]);
                setTest("idle");
              }}
              className={`relative cursor-pointer rounded-[10px] border bg-bg-3 px-3.5 py-3 text-left ${
                provider === p.id ? "border-violet" : "border-line-soft"
              }`}
            >
              {PROVIDERS[p.id].rec && (
                <div className="absolute right-2 top-2">
                  <Pill tone="violet">推荐</Pill>
                </div>
              )}
              <div className="mb-0.5 text-sm font-semibold text-fg-1">{p.l}</div>
              <div className="text-[10.5px] text-fg-3">{p.sub}</div>
            </button>
          ))}
        </div>
      </Card>

      <Card title="模型配置" right={<TestButton state={test} onTest={runTest} />}>
        <div className="grid grid-cols-1 gap-3.5 min-[700px]:grid-cols-2">
          <Field label="模型">
            <Select value={model} onChange={setModel} options={cur.models.map((m) => ({ v: m, l: m }))} />
          </Field>
          <Field label="API Base URL">
            <Input value={cur.base} readOnly />
          </Field>
        </div>
        <Field label="API Key">
          <MaskedInput value={key} onChange={setKey} placeholder="sk-..." />
        </Field>
        <Field label={`温度 · ${temp.toFixed(2)}`} hint="· 越低越确定，交易决策建议 0.2–0.4">
          <div className="flex items-center gap-3.5">
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={temp}
              onChange={(e) => setTemp(parseFloat(e.target.value))}
              className="flex-1"
              style={{ accentColor: "var(--ap-violet)" }}
            />
            <span className="w-10 text-right font-mono text-sm font-semibold text-violet">
              {temp.toFixed(2)}
            </span>
          </div>
        </Field>
        <div className="grid grid-cols-1 gap-3.5 min-[700px]:grid-cols-2">
          <Field label="最大 Token">
            <Input value={maxTokens} onChange={setMaxTokens} />
          </Field>
          <Field label="超时 (秒)">
            <Input value={timeout_} onChange={setTimeout_} />
          </Field>
        </div>
        <button className="mt-1.5 cursor-pointer rounded-[10px] border-none bg-violet px-[18px] py-2.5 text-sm font-bold text-fg-1 hover:brightness-110">
          保存模型配置
        </button>
      </Card>

      <Card title="Agent 模型分工" right={<span className="font-mono text-xs text-fg-3">可分别指定</span>}>
        {[
          { a: "决策 Agent", m: "deepseek-reasoner", desc: "交易决策推理" },
          { a: "信号 Agent", m: "deepseek-chat", desc: "市场信号识别" },
          { a: "复盘 Agent", m: "deepseek-chat", desc: "归因与诊断" },
        ].map((r, i, arr) => (
          <div
            key={r.a}
            className={`flex items-center gap-3 py-[11px] ${i < arr.length - 1 ? "border-b border-line-soft" : ""}`}
          >
            <div className="flex h-[30px] w-[30px] items-center justify-center rounded-sm bg-violet-soft">
              <BrainCircuit size={15} className="text-violet" />
            </div>
            <div className="flex-1">
              <div className="text-sm font-semibold text-fg-1">{r.a}</div>
              <div className="text-xs text-fg-3">{r.desc}</div>
            </div>
            <Pill>{r.m}</Pill>
          </div>
        ))}
      </Card>
    </>
  );
}

// ---------- 通知 ----------
function NotifySection() {
  const [tg, setTg] = useState(true);
  const [dc, setDc] = useState(false);
  const [events, setEvents] = useState<Record<string, boolean>>({
    open: true,
    close: true,
    halt: true,
    reject: false,
    daily: true,
  });
  const toggle = (k: string) => setEvents((e) => ({ ...e, [k]: !e[k] }));
  return (
    <>
      <Card title="推送渠道">
        <div className="flex items-center gap-3 border-b border-line-soft py-[11px]">
          <div className="flex h-8 w-8 items-center justify-center rounded-sm bg-cyan-soft">
            <Bell size={16} className="text-cyan" />
          </div>
          <div className="flex-1">
            <div className="text-sm font-semibold text-fg-1">Telegram</div>
            <div className="font-mono text-xs text-fg-3">@alphapilot_bot · 已绑定</div>
          </div>
          <Switch on={tg} onToggle={() => setTg(!tg)} />
        </div>
        <div className="flex items-center gap-3 py-[11px]">
          <div className="flex h-8 w-8 items-center justify-center rounded-sm bg-violet-soft">
            <Bell size={16} className="text-violet" />
          </div>
          <div className="flex-1">
            <div className="text-sm font-semibold text-fg-1">Discord</div>
            <div className="text-xs text-fg-3">未绑定</div>
          </div>
          <Switch on={dc} onToggle={() => setDc(!dc)} />
        </div>
      </Card>

      <Card title="推送事件">
        {[
          { k: "open", l: "开仓成交", d: "AI 开仓并成交时", warn: false },
          { k: "close", l: "平仓成交", d: "止盈/止损/手动平仓", warn: false },
          { k: "halt", l: "熔断触发", d: "日亏/连亏触发熔断（强烈建议开启）", warn: true },
          { k: "reject", l: "守卫拦截", d: "决策被守卫拒绝时", warn: false },
          { k: "daily", l: "每日报告", d: "每日收盘 AI 日报", warn: false },
        ].map((e, i, arr) => (
          <div
            key={e.k}
            className={`flex items-center gap-3 py-[11px] ${i < arr.length - 1 ? "border-b border-line-soft" : ""}`}
          >
            <div className="flex-1">
              <div className="flex items-center gap-2 text-sm font-medium text-fg-1">
                {e.l}
                {e.warn && <Pill tone="rose">关键</Pill>}
              </div>
              <div className="mt-0.5 text-xs text-fg-3">{e.d}</div>
            </div>
            <Switch on={events[e.k]} onToggle={() => toggle(e.k)} />
          </div>
        ))}
      </Card>
    </>
  );
}

// ---------- 账户偏好 ----------
function AccountSection() {
  const [lang, setLang] = useState<"zh" | "en">("zh");
  const [tz, setTz] = useState("utc8");
  const [twofa, setTwofa] = useState(true);
  const [stopOpen, setStopOpen] = useState(false);
  const [stopping, setStopping] = useState(false);

  const emergencyStop = async () => {
    setStopping(true);
    try {
      await commandsApi.closeAll();
      await commandsApi.pause();
      setStopOpen(false);
    } finally {
      setStopping(false);
    }
  };

  return (
    <>
      <Card title="偏好">
        <div className="grid grid-cols-1 gap-3.5 min-[700px]:grid-cols-2">
          <Field label="界面语言">
            <Segmented
              value={lang}
              onChange={setLang}
              options={[
                { v: "zh", l: "中文" },
                { v: "en", l: "English" },
              ]}
            />
          </Field>
          <Field label="时区">
            <Select
              value={tz}
              onChange={setTz}
              options={[
                { v: "utc8", l: "UTC+8 北京" },
                { v: "utc0", l: "UTC 世界时" },
                { v: "utc-5", l: "UTC-5 纽约" },
              ]}
            />
          </Field>
        </div>
      </Card>

      <Card title="安全">
        <div className="flex items-center gap-3 border-b border-line-soft py-[11px]">
          <div className="flex-1">
            <div className="text-sm font-medium text-fg-1">双重验证 2FA</div>
            <div className="text-xs text-fg-3">登录与敏感操作需二次验证</div>
          </div>
          <Pill tone="mint">已启用</Pill>
          <Switch on={twofa} onToggle={() => setTwofa(!twofa)} />
        </div>
        <div className="flex items-center gap-3 py-[11px]">
          <div className="flex-1">
            <div className="text-sm font-medium text-fg-1">会话与设备</div>
            <div className="font-mono text-xs text-fg-3">2 个活跃会话</div>
          </div>
          <button className="cursor-pointer rounded-sm border border-line bg-bg-3 px-3.5 py-[7px] text-xs text-fg-2">
            管理
          </button>
        </div>
      </Card>

      <Card title="危险区" style={{ borderColor: "rgba(255,77,109,.25)" }}>
        <div className="flex items-center gap-3">
          <div className="flex-1">
            <div className="text-sm font-medium text-rose">清空所有持仓并停止引擎</div>
            <div className="text-xs text-fg-3">立即市价平掉所有仓位并暂停自动交易</div>
          </div>
          <button
            onClick={() => setStopOpen(true)}
            className="cursor-pointer rounded-[9px] border border-rose bg-rose-soft px-4 py-[9px] text-xs font-semibold text-rose hover:brightness-110"
          >
            紧急停止
          </button>
        </div>
      </Card>

      <ConfirmDialog
        open={stopOpen}
        onClose={() => setStopOpen(false)}
        onConfirm={emergencyStop}
        busy={stopping}
        title="紧急停止 · 全平 + 停机"
        confirmLabel="确认紧急停止"
        requireText="STOP"
        body={
          <>
            将<b className="text-rose">市价平掉所有持仓</b>并
            <b className="text-rose">暂停自动交易引擎</b>
            。平仓在波动行情下可能产生滑点损失，恢复需手动执行。
          </>
        }
      />
    </>
  );
}

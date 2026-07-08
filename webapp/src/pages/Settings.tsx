/**
 * 设置（handoff/02 P11，后端 P4 契约接真）—— 四分区：交易所 / AI 模型 / 通知 / 账户偏好。
 * 密钥只显示脱敏尾 4 位（输入留空 = 不修改）；紧急停止 = close-all + 暂停引擎（口令确认）。
 */
import { useEffect, useRef, useState } from "react";
import {
  AlertTriangle,
  Bell,
  BrainCircuit,
  Check,
  Layers,
  Lock,
  Settings as SettingsIcon,
  X,
} from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { PageShell } from "@/components/shell/PageShell";
import { Card, Pill } from "@/components/ui/atoms";
import {
  Field,
  Input,
  MaskedInput,
  Segmented,
  Switch,
  TestButton,
  type TestState,
} from "@/components/ui/form";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { TwoFaDialog } from "@/components/settings/TwoFaDialog";
import { commandsApi, settingsApi } from "@/api/services";
import {
  useExchangeSettings,
  useLlmSettings,
  useNotificationSettings,
} from "@/api/queries";
import { qk } from "@/api/queryClient";
import { useMe } from "@/auth/auth";
import type { ExchangeTestResult } from "@/api/types";

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

function useSaveState() {
  const [state, setState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [msg, setMsg] = useState("");
  return { state, setState, msg, setMsg };
}

// ---------- 交易所 ----------
function ExchangeSection() {
  const queryClient = useQueryClient();
  const { data: ex } = useExchangeSettings();
  // net = 正在「配置/查看」哪个网络（纯视图，切换不影响系统运行网络）
  const [net, setNet] = useState<"mainnet" | "testnet">("testnet");
  const [key, setKey] = useState("");
  const [secret, setSecret] = useState("");
  const [test, setTest] = useState<TestState>("idle");
  const [testResult, setTestResult] = useState<ExchangeTestResult | null>(null);
  const [switchOpen, setSwitchOpen] = useState(false);
  const [switching, setSwitching] = useState(false);
  const save = useSaveState();

  // 首次加载把视图默认到系统当前运行网络；之后用户自由切换，不再被拉回
  const inited = useRef(false);
  useEffect(() => {
    if (ex && !inited.current) {
      setNet(ex.network);
      inited.current = true;
    }
  }, [ex]);

  const isTestnet = net === "testnet";
  // 按当前选择的网络取脱敏状态（两网络独立，不再串）
  const cur = net === "mainnet" ? ex?.mainnet : ex?.testnet;
  // 视图网络 ≠ 系统运行网络 → 提示可切换
  const isRunning = ex?.network === net;

  const switchActive = async () => {
    setSwitching(true);
    try {
      await settingsApi.setActiveNetwork(net);
      await queryClient.invalidateQueries({ queryKey: qk.settingsExchange });
      setSwitchOpen(false);
    } finally {
      setSwitching(false);
    }
  };

  const runTest = async () => {
    setTest("testing");
    setTestResult(null);
    try {
      const r = await settingsApi.testExchange({
        network: net,
        apiKey: key || undefined,
        apiSecret: secret || undefined,
      });
      setTestResult(r);
      setTest(r.ok ? "ok" : "fail");
    } catch (e) {
      setTestResult({
        ok: false,
        permissions: null,
        warning: null,
        error: e instanceof Error ? e.message : "请求失败",
      });
      setTest("fail");
    }
  };

  const doSave = async () => {
    save.setState("saving");
    try {
      await settingsApi.updateExchange({
        network: net,
        apiKey: key || undefined,
        apiSecret: secret || undefined,
      });
      await queryClient.invalidateQueries({ queryKey: qk.settingsExchange });
      setKey("");
      setSecret("");
      save.setState("saved");
      setTimeout(() => save.setState("idle"), 2000);
    } catch (e) {
      save.setMsg(e instanceof Error ? e.message : "保存失败");
      save.setState("error");
    }
  };

  const perms = testResult?.permissions;

  return (
    <>
      <Card title="交易所">
        <div className="flex gap-3">
          {[
            { id: "binance", name: "Binance", sub: "USDT 现货 · MVP 首选", active: true },
            { id: "hyperliquid", name: "Hyperliquid", sub: "去中心化 · 规划中", active: false },
          ].map((exch) => (
            <div
              key={exch.id}
              className={`relative flex-1 rounded-md border bg-bg-3 p-4 ${
                exch.active ? "border-mint" : "border-line-soft opacity-60"
              }`}
            >
              {exch.active && (
                <div className="absolute right-3 top-3">
                  <Pill tone={cur?.hasSecret ? "mint" : "amber"}>
                    {cur?.hasSecret ? "已配置" : "未配置"}
                  </Pill>
                </div>
              )}
              <div className="mb-0.5 text-sm font-semibold text-fg-1">{exch.name}</div>
              <div className="text-xs text-fg-3">{exch.sub}</div>
            </div>
          ))}
        </div>
      </Card>

      <Card title="Binance · 网络与 API" right={<TestButton state={test} onTest={runTest} />}>
        {/* 测试结果醒目横幅 */}
        {test === "fail" && testResult?.error && (
          <div className="mb-3.5 flex items-start gap-2 rounded-sm border border-rose/30 bg-rose-soft px-3 py-2.5">
            <AlertTriangle size={14} className="mt-px shrink-0 text-rose" />
            <div className="min-w-0 flex-1">
              <div className="mb-0.5 text-xs font-semibold text-rose">测试失败</div>
              <div className="break-words font-mono text-[11px] leading-relaxed text-fg-2">
                {testResult.error}
              </div>
            </div>
          </div>
        )}
        {test === "ok" && (
          <div className="mb-3.5 flex items-center gap-2 rounded-sm border border-mint/30 bg-mint-soft px-3 py-2.5">
            <Check size={14} className="shrink-0 text-mint" />
            <span className="text-xs font-semibold text-mint">连接成功 · 权限已实测（见下方清单）</span>
          </div>
        )}
        {/* 系统当前运行网络（只读展示，切换是下方独立操作） */}
        <div className="mb-3.5 flex items-center gap-2 rounded-sm bg-bg-3 px-3 py-2.5">
          <span className="text-xs text-fg-3">系统当前运行网络</span>
          <Pill tone={ex?.network === "mainnet" ? "rose" : "cyan"}>
            {ex?.network === "mainnet" ? "主网 Mainnet" : "测试网 Testnet"}
          </Pill>
          <span className="ml-auto font-mono text-micro text-fg-4">
            决策/下单实际走这个网络
          </span>
        </div>

        <Field
          label="配置网络"
          hint="· 选择要查看/配置哪个网络的 API Key（不影响系统运行网络）"
        >
          <Segmented
            value={net}
            onChange={(v) => {
              // 纯视图切换：清空输入 + 重置测试态（避免把 A 网络输入的 key 误配到 B）
              setNet(v);
              setTest("idle");
              setTestResult(null);
              setKey("");
              setSecret("");
            }}
            options={[
              { v: "mainnet", l: "主网 Mainnet", dot: "var(--ap-rose)" },
              { v: "testnet", l: "测试网 Testnet", dot: "var(--ap-cyan)" },
            ]}
          />
        </Field>

        {/* 视图网络 ≠ 运行网络：给独立的切换入口（重操作，二次确认） */}
        {ex && !isRunning && (
          <div className="mb-3.5 flex items-center gap-2.5 rounded-sm border border-amber/25 bg-amber-soft px-3 py-2.5">
            <AlertTriangle size={14} className="shrink-0 text-amber" />
            <span className="flex-1 text-xs text-fg-2">
              系统当前运行在
              <b>{ex.network === "mainnet" ? "主网" : "测试网"}</b>
              ，是否把运行网络切换到
              <b>{isTestnet ? "测试网" : "主网"}</b>？
            </span>
            <button
              onClick={() => setSwitchOpen(true)}
              className="shrink-0 cursor-pointer rounded-sm border border-amber/40 bg-transparent px-3 py-1.5 text-xs font-semibold text-amber hover:brightness-110"
            >
              切换运行网络
            </button>
          </div>
        )}

        {isTestnet ? (
          <div className="mb-3.5 flex items-start gap-2 rounded-sm border border-cyan/20 bg-cyan-soft px-3 py-2.5">
            <AlertTriangle size={14} className="mt-px shrink-0 text-cyan" />
            <span className="text-xs leading-normal text-fg-2">
              当前为 <b className="text-cyan">测试网</b>。所有成交为模拟，不涉及真实资金。
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

        <Field
          label={`API Key · ${isTestnet ? "测试网" : "主网"}`}
          hint={cur?.apiKeyMasked ? `· 当前 ${cur.apiKeyMasked}，留空不修改` : "· 该网络尚未配置"}
        >
          <Input
            value={key}
            onChange={setKey}
            placeholder={`输入${isTestnet ? "测试网" : "主网"} Binance API Key`}
            name="ap-bn-key"
            autoComplete="off"
          />
        </Field>
        <Field label="API Secret" hint={cur?.hasSecret ? "· 已加密存储，留空不修改" : "· 该网络尚未配置"}>
          <MaskedInput
            value={secret}
            onChange={setSecret}
            placeholder="输入新的 Binance API Secret"
            name="ap-bn-secret"
          />
        </Field>

        <Field label="权限校验" hint="· 点右上「测试连接」实测 API 权限">
          <div className="flex flex-col gap-1.5">
            {(
              [
                { l: "读取账户与持仓", v: perms?.read, wantOff: false },
                { l: "现货交易（下单/撤单）", v: perms?.trade, wantOff: false },
                { l: "提现权限", v: perms?.withdraw, wantOff: true },
              ] as const
            ).map((p) => (
              <div key={p.l} className="flex items-center gap-2 rounded-sm bg-bg-3 px-3 py-2 text-xs">
                <span
                  className={`flex h-4 w-4 items-center justify-center rounded-[4px] ${
                    p.v === undefined
                      ? "bg-bg-4"
                      : (p.wantOff ? !p.v : p.v)
                        ? "bg-mint-soft"
                        : "bg-rose-soft"
                  }`}
                >
                  {p.v === undefined ? null : p.wantOff ? (
                    // 提现权限：开启=危险(红三角)，关闭=安全(绿锁，而非易混淆的绿勾)
                    p.v ? (
                      <AlertTriangle size={11} strokeWidth={2.6} className="text-rose" />
                    ) : (
                      <Lock size={11} strokeWidth={2.6} className="text-mint" />
                    )
                  ) : p.v ? (
                    <Check size={11} strokeWidth={2.6} className="text-mint" />
                  ) : (
                    <X size={11} strokeWidth={2.6} className="text-rose" />
                  )}
                </span>
                <span className={`flex-1 ${p.wantOff && p.v ? "text-rose" : "text-fg-2"}`}>{p.l}</span>
                <span className="font-mono text-micro text-fg-4">
                  {p.v === undefined ? "未检测" : p.wantOff ? (p.v ? "必须关闭!" : "已关闭") : p.v ? "正常" : "缺失"}
                </span>
              </div>
            ))}
          </div>
        </Field>
        {testResult?.warning && (
          <div className="mb-2 text-xs text-amber">{testResult.warning}</div>
        )}

        <div className="mt-1.5 flex items-center gap-2">
          <button
            onClick={doSave}
            disabled={save.state === "saving"}
            className="cursor-pointer rounded-[10px] border-none bg-mint px-[18px] py-2.5 text-sm font-bold text-bg-0 hover:brightness-110 disabled:opacity-50"
          >
            {save.state === "saving"
              ? "保存中…"
              : `保存${isTestnet ? "测试网" : "主网"} Key`}
          </button>
          {save.state === "saved" && (
            <span className="text-xs text-mint">已保存（仅存 Key，不切换运行网络）</span>
          )}
          {save.state === "error" && <span className="text-xs text-rose">{save.msg}</span>}
        </div>
      </Card>

      {/* 切换系统运行网络：重操作，主网需口令确认 */}
      <ConfirmDialog
        open={switchOpen}
        onClose={() => setSwitchOpen(false)}
        onConfirm={switchActive}
        busy={switching}
        title={`切换系统运行网络 → ${isTestnet ? "测试网" : "主网"}`}
        confirmLabel="确认切换"
        requireText={isTestnet ? undefined : "MAINNET"}
        body={
          isTestnet ? (
            <>
              系统将切到<b className="text-cyan">测试网</b>运行，后续所有决策与下单走测试盘模拟资金。
              请确认对应网络的 API Key 已配置。
            </>
          ) : (
            <>
              系统将切到<b className="text-rose">主网</b>运行，AI 将用<b className="text-rose">真实资金</b>下单。
              输入 <b className="font-mono text-rose">MAINNET</b> 确认。
            </>
          )
        }
      />
    </>
  );
}

// ---------- LLM ----------
const PROVIDER_PRESETS = [
  { id: "deepseek", l: "DeepSeek", sub: "性价比首选", base: "https://api.deepseek.com/v1", rec: true },
  { id: "openai", l: "OpenAI", sub: "GPT-5 / o1", base: "https://api.openai.com/v1", rec: false },
  { id: "anthropic", l: "Anthropic", sub: "Claude", base: "https://api.anthropic.com/v1", rec: false },
  { id: "custom", l: "自定义", sub: "兼容 OpenAI", base: "", rec: false },
] as const;

const AGENT_LABELS: Record<string, { name: string; desc: string }> = {
  decision: { name: "决策 Agent", desc: "交易决策推理" },
  signal: { name: "信号 Agent", desc: "市场信号识别" },
  review: { name: "复盘 Agent", desc: "归因与诊断" },
};

function LlmSection() {
  const queryClient = useQueryClient();
  const { data: llm } = useLlmSettings();
  const [model, setModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [key, setKey] = useState("");
  const [temp, setTemp] = useState(0.3);
  const [timeoutSec, setTimeoutSec] = useState("30");
  const [test, setTest] = useState<TestState>("idle");
  const [latency, setLatency] = useState<number | null>(null);
  const save = useSaveState();

  useEffect(() => {
    if (!llm) return;
    setModel(llm.model);
    setBaseUrl(llm.baseUrl);
    setTemp(llm.temperature);
    setTimeoutSec(String(llm.timeoutSeconds));
  }, [llm]);

  const provider =
    PROVIDER_PRESETS.find((p) => p.base && baseUrl.startsWith(p.base))?.id ?? "custom";

  const [testError, setTestError] = useState<string | null>(null);
  const runTest = async () => {
    setTest("testing");
    setTestError(null);
    try {
      const r = await settingsApi.testLlm({
        model,
        baseUrl,
        apiKey: key || undefined,
      });
      setLatency(r.latencyMs);
      setTestError(r.error);
      setTest(r.ok ? "ok" : "fail");
    } catch (e) {
      setTestError(e instanceof Error ? e.message : "请求失败");
      setTest("fail");
    }
  };

  const doSave = async () => {
    save.setState("saving");
    try {
      await settingsApi.updateLlm({
        model,
        baseUrl,
        apiKey: key || undefined,
        temperature: temp,
        timeoutSeconds: Number(timeoutSec) || 30,
      });
      await queryClient.invalidateQueries({ queryKey: qk.settingsLlm });
      setKey("");
      save.setState("saved");
      setTimeout(() => save.setState("idle"), 2000);
    } catch (e) {
      save.setMsg(e instanceof Error ? e.message : "保存失败");
      save.setState("error");
    }
  };

  return (
    <>
      <Card title="模型提供方">
        <div className="grid grid-cols-2 gap-2.5 min-[800px]:grid-cols-4">
          {PROVIDER_PRESETS.map((p) => (
            <button
              key={p.id}
              onClick={() => {
                if (p.base) setBaseUrl(p.base);
                setTest("idle");
              }}
              className={`relative cursor-pointer rounded-[10px] border bg-bg-3 px-3.5 py-3 text-left ${
                provider === p.id ? "border-violet" : "border-line-soft"
              }`}
            >
              {p.rec && (
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
        {/* 测试结果醒目横幅：失败时完整显示后端返回的真实原因 */}
        {test === "fail" && testError && (
          <div className="mb-3.5 flex items-start gap-2 rounded-sm border border-rose/30 bg-rose-soft px-3 py-2.5">
            <AlertTriangle size={14} className="mt-px shrink-0 text-rose" />
            <div className="min-w-0 flex-1">
              <div className="mb-0.5 text-xs font-semibold text-rose">测试失败</div>
              <div className="break-words font-mono text-[11px] leading-relaxed text-fg-2">
                {testError}
              </div>
            </div>
          </div>
        )}
        {test === "ok" && (
          <div className="mb-3.5 flex items-center gap-2 rounded-sm border border-mint/30 bg-mint-soft px-3 py-2.5">
            <Check size={14} className="shrink-0 text-mint" />
            <span className="text-xs font-semibold text-mint">
              连接成功{latency != null ? ` · 延迟 ${latency}ms` : ""}
            </span>
          </div>
        )}
        <div className="grid grid-cols-1 gap-3.5 min-[700px]:grid-cols-2">
          <Field label="模型" hint="· DeepSeek 用 deepseek-v4-pro；其他提供方见其官方文档">
            <Input value={model} onChange={setModel} placeholder="deepseek-v4-pro" />
          </Field>
          <Field label="API Base URL">
            <Input value={baseUrl} onChange={setBaseUrl} placeholder="https://.../v1" />
          </Field>
        </div>
        <Field label="API Key" hint={llm?.apiKeyMasked ? `· 当前 ${llm.apiKeyMasked}，留空不修改` : "· 尚未配置"}>
          <MaskedInput value={key} onChange={setKey} placeholder="sk-..." name="ap-llm-key" />
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
          <Field label="超时 (秒)">
            <Input value={timeoutSec} onChange={setTimeoutSec} />
          </Field>
          <Field label="连通性">
            <div className="py-2 font-mono text-xs">
              {test === "ok" && latency != null ? (
                <span className="text-mint">延迟 {latency}ms</span>
              ) : test === "fail" ? (
                <span className="text-rose">失败（见上方原因）</span>
              ) : (
                <span className="text-fg-3">尚未测试</span>
              )}
            </div>
          </Field>
        </div>
        <div className="mt-1.5 flex items-center gap-2">
          <button
            onClick={doSave}
            disabled={save.state === "saving"}
            className="cursor-pointer rounded-[10px] border-none bg-violet px-[18px] py-2.5 text-sm font-bold text-fg-1 hover:brightness-110 disabled:opacity-50"
          >
            {save.state === "saving" ? "保存中…" : "保存模型配置"}
          </button>
          {save.state === "saved" && <span className="text-xs text-mint">已保存（落审计日志）</span>}
          {save.state === "error" && <span className="text-xs text-rose">{save.msg}</span>}
        </div>
      </Card>

      <Card title="Agent 模型分工" right={<span className="font-mono text-xs text-fg-3">runtime config</span>}>
        {Object.entries(llm?.agentModels ?? {}).map(([k, m], i, arr) => (
          <div
            key={k}
            className={`flex items-center gap-3 py-[11px] ${i < arr.length - 1 ? "border-b border-line-soft" : ""}`}
          >
            <div className="flex h-[30px] w-[30px] items-center justify-center rounded-sm bg-violet-soft">
              <BrainCircuit size={15} className="text-violet" />
            </div>
            <div className="flex-1">
              <div className="text-sm font-semibold text-fg-1">
                {AGENT_LABELS[k]?.name ?? k}
              </div>
              <div className="text-xs text-fg-3">{AGENT_LABELS[k]?.desc ?? ""}</div>
            </div>
            <Pill>{m}</Pill>
          </div>
        ))}
      </Card>
    </>
  );
}

// ---------- 通知 ----------
const SUB_LABELS: Record<string, { l: string; d: string; warn?: boolean }> = {
  circuit_breaker: { l: "熔断触发", d: "日亏/连亏触发熔断（强烈建议开启）", warn: true },
  order_filled: { l: "订单成交", d: "AI/手动下单成交时" },
  position_closed: { l: "平仓", d: "止盈/止损/手动平仓" },
  daily_report: { l: "每日报告", d: "每日收盘 AI 日报" },
};

function NotifySection() {
  const queryClient = useQueryClient();
  const { data: notify } = useNotificationSettings();

  const patch = async (u: {
    channels?: Record<string, boolean>;
    subscriptions?: Record<string, boolean>;
  }) => {
    await settingsApi.updateNotifications(u);
    await queryClient.invalidateQueries({ queryKey: qk.settingsNotify });
  };

  if (!notify) return null;

  return (
    <>
      <Card title="推送渠道">
        <div className="flex items-center gap-3 border-b border-line-soft py-[11px]">
          <div className="flex h-8 w-8 items-center justify-center rounded-sm bg-cyan-soft">
            <Bell size={16} className="text-cyan" />
          </div>
          <div className="flex-1">
            <div className="text-sm font-semibold text-fg-1">Telegram</div>
            <div className="font-mono text-xs text-fg-3">
              {notify.telegramBotTokenMasked
                ? `bot ${notify.telegramBotTokenMasked} · chat ${notify.telegramChatId ?? "—"}`
                : "未绑定"}
            </div>
          </div>
          <Switch
            on={notify.channels.telegram ?? false}
            onToggle={() =>
              patch({ channels: { ...notify.channels, telegram: !notify.channels.telegram } })
            }
          />
        </div>
        <div className="flex items-center gap-3 py-[11px]">
          <div className="flex h-8 w-8 items-center justify-center rounded-sm bg-violet-soft">
            <Bell size={16} className="text-violet" />
          </div>
          <div className="flex-1">
            <div className="text-sm font-semibold text-fg-1">Discord</div>
            <div className="text-xs text-fg-3">未绑定</div>
          </div>
          <Switch
            on={notify.channels.discord ?? false}
            onToggle={() =>
              patch({ channels: { ...notify.channels, discord: !notify.channels.discord } })
            }
          />
        </div>
      </Card>

      <Card title="推送事件">
        {Object.entries(SUB_LABELS).map(([k, meta], i, arr) => (
          <div
            key={k}
            className={`flex items-center gap-3 py-[11px] ${i < arr.length - 1 ? "border-b border-line-soft" : ""}`}
          >
            <div className="flex-1">
              <div className="flex items-center gap-2 text-sm font-medium text-fg-1">
                {meta.l}
                {meta.warn && <Pill tone="rose">关键</Pill>}
              </div>
              <div className="mt-0.5 text-xs text-fg-3">{meta.d}</div>
            </div>
            <Switch
              on={notify.subscriptions[k] ?? false}
              onToggle={() =>
                patch({
                  subscriptions: { ...notify.subscriptions, [k]: !notify.subscriptions[k] },
                })
              }
            />
          </div>
        ))}
      </Card>
    </>
  );
}

// ---------- 账户偏好 ----------
function AccountSection() {
  const { data: me } = useMe();
  const [stopOpen, setStopOpen] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [twoFaOpen, setTwoFaOpen] = useState(false);

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
      <Card title="安全">
        <div className="flex items-center gap-3 border-b border-line-soft py-[11px]">
          <div className="flex-1">
            <div className="text-sm font-medium text-fg-1">双重验证 2FA</div>
            <div className="text-xs text-fg-3">登录二段式验证（TOTP 验证器）</div>
          </div>
          <Pill tone={me?.twoFa ? "mint" : "default"}>
            {me?.twoFa ? "已启用" : "未启用"}
          </Pill>
          <button
            onClick={() => setTwoFaOpen(true)}
            className={`cursor-pointer rounded-sm border px-3 py-[7px] text-xs ${
              me?.twoFa
                ? "border-rose/40 text-rose"
                : "border-mint/40 text-mint"
            }`}
          >
            {me?.twoFa ? "关闭" : "开启"}
          </button>
        </div>
        <div className="flex items-center gap-3 py-[11px]">
          <div className="flex-1">
            <div className="text-sm font-medium text-fg-1">当前账户</div>
            <div className="font-mono text-xs text-fg-3">
              {me ? `${me.email} · ${me.role.toUpperCase()}` : "—"}
            </div>
          </div>
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

      <TwoFaDialog
        open={twoFaOpen}
        mode={me?.twoFa ? "disable" : "enable"}
        onClose={() => setTwoFaOpen(false)}
      />

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

/**
 * 后台管理（handoff/02 P12）—— 三分区：用户管理 / 角色权限矩阵 / 管理日志。
 */
import { useEffect, useState } from "react";
import { Check, Key, List, Settings as SettingsIcon, Users, X } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { PageShell } from "@/components/shell/PageShell";
import { Card, Pill, Stat } from "@/components/ui/atoms";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Field, Input, Select } from "@/components/ui/form";
import { useAuditLogs, usePermissions, useUsers } from "@/api/queries";
import { qk } from "@/api/queryClient";
import { adminApi } from "@/api/services";
import type { PermissionRow, Role, User } from "@/api/types";

const ROLE_OPTIONS = [
  { v: "admin", l: "Admin" },
  { v: "trader", l: "Trader" },
  { v: "viewer", l: "Viewer" },
];

const ROLE_CFG: Record<Role, { l: string; tone: "violet" | "rose" | "mint" | "cyan"; desc: string }> = {
  owner: { l: "Owner", tone: "violet", desc: "所有权限 + 转让所有权" },
  admin: { l: "Admin", tone: "rose", desc: "用户/权限/系统配置管理" },
  trader: { l: "Trader", tone: "mint", desc: "交易操作与策略管理" },
  viewer: { l: "Viewer", tone: "cyan", desc: "只读访问" },
};

const ROLE_ORDER: Role[] = ["owner", "admin", "trader", "viewer"];

function Avatar({ name, size = 30 }: { name: string; size?: number }) {
  const hue = (name.charCodeAt(0) * 37) % 360;
  return (
    <div
      className="flex shrink-0 items-center justify-center rounded-full font-bold text-fg-1"
      style={{
        width: size,
        height: size,
        background: `oklch(0.45 0.09 ${hue})`,
        fontSize: size * 0.38,
      }}
    >
      {name.split(" ").map((w) => w[0]).join("")}
    </div>
  );
}

function StatusPill({ s }: { s: User["status"] }) {
  return (
    <Pill tone={s === "active" ? "mint" : s === "pending" ? "amber" : "default"}>
      {s === "active" ? "活跃" : s === "pending" ? "待批准" : "已停用"}
    </Pill>
  );
}

// ---------- 用户管理 ----------
function UsersTab() {
  const queryClient = useQueryClient();
  const { data: users = [] } = useUsers();
  const [inviteOpen, setInviteOpen] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);
  const refresh = () => queryClient.invalidateQueries({ queryKey: qk.users });
  const approve = async (id: string) => {
    await adminApi.approveUser(id);
    await refresh();
  };
  const toggleDisable = async (u: User) => {
    await adminApi.updateUser(u.id, {
      status: u.status === "disabled" ? "active" : "disabled",
    });
    await refresh();
  };
  const twoFaPct = users.length
    ? Math.round((users.filter((u) => u.twoFa).length / users.length) * 100)
    : 0;
  return (
    <>
      <div className="grid grid-cols-2 gap-3 min-[900px]:grid-cols-4">
        <Card dense><Stat label="总用户" value={users.length} size="sm" /></Card>
        <Card dense>
          <Stat label="活跃" value={users.filter((u) => u.status === "active").length} size="sm" tone="pos" />
        </Card>
        <Card dense>
          <Stat label="待批准" value={users.filter((u) => u.status === "pending").length} size="sm" />
        </Card>
        <Card dense><Stat label="2FA 覆盖" value={`${twoFaPct}%`} size="sm" /></Card>
      </div>

      <Card
        title="用户"
        right={
          <button
            onClick={() => setInviteOpen(true)}
            className="cursor-pointer rounded-sm border-none bg-mint px-3 py-1.5 text-xs font-bold text-bg-0 hover:brightness-110"
          >
            + 邀请用户
          </button>
        }
      >
        <div className="-mx-[18px] -my-4 overflow-x-auto">
          <table className="w-full border-collapse text-xs">
            <thead>
              <tr className="border-b border-line">
                {["用户", "角色", "状态", "2FA", "最近活跃", "操作"].map((h) => (
                  <th key={h} className="px-3.5 py-2.5 text-left text-micro font-medium uppercase tracking-[.06em] text-fg-3">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const self = u.role === "owner";
                return (
                  <tr key={u.id} className="border-b border-line-soft" style={{ opacity: u.status === "disabled" ? 0.55 : 1 }}>
                    <td className="px-3.5 py-[11px]">
                      <div className="flex items-center gap-2.5">
                        <Avatar name={u.name} />
                        <div>
                          <div className="flex items-center gap-1.5 font-semibold text-fg-1">
                            {u.name}
                            {self && <span className="text-micro text-fg-4">（你）</span>}
                          </div>
                          <div className="font-mono text-[11px] text-fg-4">{u.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-3.5 py-[11px]">
                      <Pill tone={ROLE_CFG[u.role].tone}>{ROLE_CFG[u.role].l}</Pill>
                    </td>
                    <td className="px-3.5 py-[11px]"><StatusPill s={u.status} /></td>
                    <td className="px-3.5 py-[11px]">
                      {u.twoFa ? (
                        <Check size={14} strokeWidth={2.4} className="text-mint" />
                      ) : (
                        <X size={14} strokeWidth={2.4} className="text-fg-4" />
                      )}
                    </td>
                    <td className="px-3.5 py-[11px] font-mono text-[11px] text-fg-3">{u.lastActive}</td>
                    <td className="px-3.5 py-[11px]">
                      <div className="flex gap-1.5">
                        {u.status === "pending" ? (
                          <>
                            <button
                              onClick={() => approve(u.id)}
                              className="cursor-pointer rounded-xs border-none bg-mint px-[11px] py-1 text-[11px] font-bold text-bg-0"
                            >
                              批准
                            </button>
                            <button className="cursor-pointer rounded-xs border border-line bg-transparent px-[11px] py-1 text-[11px] text-fg-3">
                              拒绝
                            </button>
                          </>
                        ) : (
                          !self && (
                            <>
                              <button
                                onClick={() => setEditing(u)}
                                className="cursor-pointer rounded-xs border border-line bg-bg-3 px-[11px] py-1 text-[11px] text-fg-2"
                              >
                                编辑
                              </button>
                              <button
                                onClick={() => toggleDisable(u)}
                                className="cursor-pointer rounded-xs border border-rose/35 bg-transparent px-[11px] py-1 text-[11px] text-rose"
                              >
                                {u.status === "disabled" ? "启用" : "停用"}
                              </button>
                            </>
                          )
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      <InviteUserModal
        open={inviteOpen}
        onClose={() => setInviteOpen(false)}
        onDone={refresh}
      />
      <EditUserModal
        user={editing}
        onClose={() => setEditing(null)}
        onDone={refresh}
      />
    </>
  );
}

function InviteUserModal({
  open,
  onClose,
  onDone,
}: {
  open: boolean;
  onClose: () => void;
  onDone: () => void;
}) {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("viewer");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const submit = async () => {
    setBusy(true);
    setError("");
    try {
      await adminApi.createUser({ username, email, password, role, status: "active" });
      onDone();
      onClose();
      setUsername("");
      setEmail("");
      setPassword("");
      setRole("viewer");
    } catch (e) {
      setError(e instanceof Error ? e.message : "创建失败");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="邀请用户（建号）">
      <div className="flex flex-col gap-3">
        <Field label="用户名">
          <Input value={username} onChange={setUsername} mono={false} placeholder="张三" />
        </Field>
        <Field label="邮箱">
          <Input value={email} onChange={setEmail} mono={false} placeholder="user@example.com" />
        </Field>
        <Field label="初始密码">
          <Input value={password} onChange={setPassword} mono={false} placeholder="强密码" />
        </Field>
        <Field label="角色">
          <Select value={role} onChange={setRole} options={ROLE_OPTIONS} />
        </Field>
        {error && <div className="text-xs text-rose">{error}</div>}
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>
            取消
          </Button>
          <Button
            variant="primary"
            disabled={busy || !username || !email || !password}
            onClick={submit}
          >
            {busy ? "创建中…" : "创建用户"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}

function EditUserModal({
  user,
  onClose,
  onDone,
}: {
  user: User | null;
  onClose: () => void;
  onDone: () => void;
}) {
  const [role, setRole] = useState("viewer");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (user) setRole(user.role);
  }, [user]);

  const submit = async () => {
    if (!user) return;
    setBusy(true);
    try {
      await adminApi.updateUser(user.id, { role });
      onDone();
      onClose();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal
      open={user !== null}
      onClose={onClose}
      title={user ? `编辑用户 · ${user.name}` : ""}
    >
      {user && (
        <div className="flex flex-col gap-3">
          <div className="font-mono text-xs text-fg-4">{user.email}</div>
          <Field label="角色">
            <Select
              value={role}
              onChange={setRole}
              options={ROLE_OPTIONS}
            />
          </Field>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={onClose}>
              取消
            </Button>
            <Button variant="primary" disabled={busy} onClick={submit}>
              {busy ? "保存中…" : "保存"}
            </Button>
          </div>
        </div>
      )}
    </Modal>
  );
}

// ---------- 角色权限 ----------
function RolesTab() {
  const { data: perms = [] } = usePermissions();
  const { data: users = [] } = useUsers();
  const groups: { key: PermissionRow["group"]; l: string }[] = [
    { key: "trade", l: "交易" },
    { key: "strategy", l: "策略" },
    { key: "system", l: "系统" },
  ];
  return (
    <>
      <div className="grid grid-cols-2 gap-3 min-[900px]:grid-cols-4">
        {ROLE_ORDER.map((k) => (
          <Card key={k} dense>
            <div className="mb-1.5 flex items-center gap-2">
              <Pill tone={ROLE_CFG[k].tone}>{ROLE_CFG[k].l}</Pill>
              <span className="font-mono text-xs text-fg-4">
                {users.filter((u) => u.role === k).length} 人
              </span>
            </div>
            <div className="text-[11.5px] leading-normal text-fg-3">{ROLE_CFG[k].desc}</div>
          </Card>
        ))}
      </div>

      <Card title="权限矩阵" right={<span className="font-mono text-[10.5px] text-fg-4">Owner 权限不可修改</span>}>
        <div className="-mx-[18px] -my-4 overflow-x-auto">
          <table className="w-full border-collapse text-xs">
            <thead>
              <tr className="border-b border-line">
                <th className="px-3.5 py-2.5 text-left text-micro font-medium uppercase tracking-[.06em] text-fg-3">
                  权限
                </th>
                {ROLE_ORDER.map((r) => (
                  <th key={r} className="px-3.5 py-2.5 text-center text-micro font-semibold uppercase tracking-[.06em] text-fg-2">
                    {ROLE_CFG[r].l}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {groups.map((g) => (
                <FragmentGroup key={g.key} label={g.l} rows={perms.filter((p) => p.group === g.key)} />
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  );
}

function FragmentGroup({ label, rows }: { label: string; rows: PermissionRow[] }) {
  return (
    <>
      <tr className="bg-bg-3">
        <td colSpan={5} className="px-3.5 py-[7px] text-micro font-bold tracking-[.08em] text-fg-3">
          {label}
        </td>
      </tr>
      {rows.map((p) => (
        <tr key={p.key} className="border-b border-line-soft">
          <td className="px-3.5 py-[9px] text-fg-2">{p.label}</td>
          {ROLE_ORDER.map((role) => (
            <td key={role} className="px-3.5 py-[9px] text-center">
              <span
                className={`inline-flex h-[18px] w-[18px] items-center justify-center rounded-[5px] border ${
                  p.granted[role]
                    ? "border-mint/40 bg-mint-soft"
                    : "border-line bg-bg-3"
                } ${role === "owner" ? "cursor-not-allowed" : "cursor-pointer"}`}
              >
                {p.granted[role] && <Check size={11} strokeWidth={2.8} className="text-mint" />}
              </span>
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}

// ---------- 管理日志 ----------
function LogTab() {
  const { data: logs = [] } = useAuditLogs();
  return (
    <Card title="管理操作日志" right={<span className="font-mono text-[10.5px] text-fg-4">不可删除</span>}>
      {logs.map((l, i) => (
        <div
          key={l.id}
          className={`flex gap-3 py-[11px] ${i < logs.length - 1 ? "border-b border-line-soft" : ""}`}
        >
          {l.system ? (
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-bg-3">
              <SettingsIcon size={13} className="text-fg-4" />
            </div>
          ) : (
            <Avatar name={l.actor} size={28} />
          )}
          <div className="min-w-0 flex-1">
            <div className="text-xs leading-normal text-fg-1">
              <b>{l.system ? "系统" : l.actor}</b> · {l.detail}
            </div>
            <div className="mt-0.5 font-mono text-[10.5px] text-fg-4">
              {l.ts} · {l.action}
            </div>
          </div>
          <Pill tone={l.action.startsWith("guard") ? "violet" : l.action.startsWith("config") ? "rose" : "default"}>
            {l.action.split(".")[0]}
          </Pill>
        </div>
      ))}
    </Card>
  );
}

// ---------- 页面 ----------
type Tab = "users" | "roles" | "log";

export default function Admin() {
  const [tab, setTab] = useState<Tab>("users");
  const tabs: { id: Tab; label: string; icon: typeof Users }[] = [
    { id: "users", label: "用户管理", icon: Users },
    { id: "roles", label: "角色权限", icon: Key },
    { id: "log", label: "管理日志", icon: List },
  ];
  return (
    <PageShell title="后台管理" sub="ADMIN">
      <div className="flex max-w-[1100px] gap-6">
        <div className="flex w-[180px] shrink-0 flex-col gap-0.5">
          {tabs.map((t) => (
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
          <div className="mt-3.5 rounded-[9px] border border-amber/20 bg-amber-soft px-3 py-2.5">
            <div className="text-[10.5px] leading-normal text-fg-2">
              所有管理操作均记录审计日志，不可删除。
            </div>
          </div>
        </div>
        <div className="flex min-w-0 flex-1 flex-col gap-4">
          {tab === "users" && <UsersTab />}
          {tab === "roles" && <RolesTab />}
          {tab === "log" && <LogTab />}
        </div>
      </div>
    </PageShell>
  );
}

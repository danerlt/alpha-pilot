/** 事件流行 —— 对齐设计稿 pages.jsx WEventRow */
import {
  BrainCircuit,
  Check,
  Circle,
  Clock,
  Shield,
  Siren,
} from "lucide-react";
import type { EventItem, EventTone } from "@/api/types";

const toneColor: Record<EventTone, string> = {
  mint: "var(--ap-mint)",
  rose: "var(--ap-rose)",
  amber: "var(--ap-amber)",
  violet: "var(--ap-violet)",
  cyan: "var(--ap-cyan)",
  fg: "var(--ap-fg-2)",
};

const kindIcon = {
  fill: Check,
  order: Clock,
  guard: Shield,
  ai: BrainCircuit,
  breaker: Siren,
  system: Circle,
} as const;

export function EventRow({ e }: { e: EventItem }) {
  const IconCmp = kindIcon[e.kind] ?? Circle;
  return (
    <div className="flex gap-2.5 border-b border-line-soft px-0.5 py-2.5">
      <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-xs bg-bg-3">
        <IconCmp size={12} style={{ color: toneColor[e.tone] }} />
      </div>
      <div className="min-w-0 flex-1">
        <div className="text-xs leading-normal text-fg-1">{e.msg}</div>
        <div className="mt-0.5 font-mono text-micro tracking-[.02em] text-fg-4">
          {e.ts}
        </div>
      </div>
    </div>
  );
}

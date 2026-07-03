/** AI 决策卡变体偏好 —— 存 localStorage（handoff/01 §3.3） */
export type CardVariant = "stepper" | "timeline" | "graph";

const KEY = "ap.decision_card_variant";

export function getVariant(): CardVariant {
  const v = localStorage.getItem(KEY);
  return v === "timeline" || v === "graph" ? v : "stepper";
}

export function setVariant(v: CardVariant) {
  localStorage.setItem(KEY, v);
}

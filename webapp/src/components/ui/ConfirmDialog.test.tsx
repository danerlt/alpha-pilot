/** 危险操作确认 —— 拒绝路径：口令不对时确认按钮必须不可点 */
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ConfirmDialog } from "./ConfirmDialog";

describe("ConfirmDialog requireText", () => {
  it("未输入口令时确认按钮禁用，onConfirm 不触发", async () => {
    const onConfirm = vi.fn();
    render(
      <ConfirmDialog
        open
        onClose={() => {}}
        onConfirm={onConfirm}
        title="紧急停止"
        body="将全平所有持仓"
        confirmLabel="确认紧急停止"
        requireText="STOP"
      />,
    );
    const btn = screen.getByRole("button", { name: "确认紧急停止" });
    expect(btn).toBeDisabled();
    await userEvent.click(btn);
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("口令错误仍禁用；输入正确后可确认", async () => {
    const onConfirm = vi.fn();
    render(
      <ConfirmDialog
        open
        onClose={() => {}}
        onConfirm={onConfirm}
        title="紧急停止"
        body="将全平所有持仓"
        confirmLabel="确认紧急停止"
        requireText="STOP"
      />,
    );
    const input = screen.getByPlaceholderText("STOP");
    const btn = screen.getByRole("button", { name: "确认紧急停止" });

    await userEvent.type(input, "stop");
    expect(btn).toBeDisabled();

    await userEvent.clear(input);
    await userEvent.type(input, "STOP");
    expect(btn).toBeEnabled();
    await userEvent.click(btn);
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });
});

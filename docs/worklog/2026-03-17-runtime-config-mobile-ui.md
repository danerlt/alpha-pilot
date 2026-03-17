# 2026-03-17 Runtime Config Mobile UI

## 做了什么

针对配置中心“页面太长、移动端观感不佳”的问题，完成了第一轮移动端 UI 收口：

1. 将配置中心从三大块并排输入，调整为 **概览卡片 + 单段编辑区** 模式
2. 新增三个切换卡片：
   - 运行模式
   - Testnet 凭据
   - Mainnet 凭据
3. 同时只展示一个编辑分段，减少手机端纵向滚动长度
4. 切换到 `mainnet` 时增加额外确认
5. 强化手机端 header / card / 按钮间距，提升触控友好性

## 为什么做

之前配置中心虽然可用，但在移动端：
- 页面过长
- 三块表单一起展开，信息密度过高
- 主网凭据区域不够聚焦

这轮调整后，配置中心更接近“移动端设置页”而不是“大桌面表单页”。

## 如何验证

- `cd frontend && npm run build`
- `cd backend && .venv/bin/pytest -q`
- `bash scripts/deploy-dev.sh`

结果：
- 前端 build 通过
- backend **64 passed**
- dev server 自动部署成功

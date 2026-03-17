# 2026-03-17 Env Access Policy

## 新规则

从现在开始，开发过程中：

- **禁止读取真实 env 文件**
  - `.env`
  - `.env.local`
  - `.env.dev-server`
  - `.env.test`
  - `.env.prod`
- **允许读取 example / 模板文件**
  - `.env.example`
  - `*.example`

## 目的

- 避免在开发和自动化推进过程中接触真实密钥
- 配置迁移工作优先围绕：
  - example 文件
  - 代码结构
  - 数据库配置中心

## 对后续工作的影响

- 调整配置时，不再以真实 env 内容为依据
- 需要补配置说明时，参考 `.env.example`
- 需要迁移配置到数据库时，按代码引用与 example 模板推断，不读取真实密钥文件

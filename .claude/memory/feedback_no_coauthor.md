---
name: no co-authored-by in commits
description: git commit 消息中不加 Co-Authored-By 行
type: feedback
---

git commit 消息中不要添加 `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>` 这一行。

**Why:** 用户不希望 commit 历史中出现 Claude 署名。

**How to apply:** 所有 git commit 消息只写功能描述，不附加任何 Co-Authored-By 行。

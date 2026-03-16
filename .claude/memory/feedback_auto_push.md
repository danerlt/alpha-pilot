---
name: auto push after each task
description: After completing each implementation chunk, always commit AND push to remote
type: feedback
---

每次完成一个实现块后，必须自动提交（git commit）并立即推送（git push）到远程仓库。

**Why:** 用户需要跨机器开发，push 确保代码在远程可用，切换设备后直接 pull 即可继续。

**How to apply:** 每次 `git commit` 之后，紧接着执行 `git push`。不需要询问用户是否 push，直接执行。

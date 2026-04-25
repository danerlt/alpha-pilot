"""Control Plane 控制面 (spec §7.1)。

KillSwitch / 手动操作 / NotifyRouter (V0.2+) / 审计扩展等。
所有写操作走事件契约 + audit_logs，控制面绝不内含业务逻辑。
"""

"""顶层 Pydantic Schemas 目录 (spec §3.1).

按领域分文件收纳所有 HTTP 入参/出参 Schema, 命名遵循:
  - xxxCreate  POST 入参
  - xxxUpdate  PATCH/PUT 入参
  - xxxRead    GET 出参
  - xxxOut     响应包装 (例如分页 list 外层)
  - xxxQuery   查询参数

`Paginated[T]` 已在 `src.common.pagination` 提供, 不在此重复。
"""

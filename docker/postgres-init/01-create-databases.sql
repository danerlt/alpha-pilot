-- 共享 PostgreSQL 实例的多库初始化（仅数据卷为空的首次启动执行一次）。
-- dev/test/prod 三环境共用一个 PG 实例，靠不同 database 隔离。
-- 若中间件卷已存在（非首次），需手动 CREATE DATABASE。
CREATE DATABASE alphapilot_dev;
CREATE DATABASE alphapilot_test;
CREATE DATABASE alphapilot_prod;

import os
from unittest.mock import patch

from scripts import init_db, upgrade_db


def test_init_db_runs_existing_migrations_only():
    with patch("scripts.init_db.subprocess.run") as run_mock:
        init_db.main()

    run_mock.assert_called_once_with(["alembic", "-c", "src/db/alembic.ini", "upgrade", "head"], check=True)


@patch("scripts.upgrade_db.subprocess.run")
def test_upgrade_db_runs_head_migration(run_mock):
    upgrade_db.main()

    run_mock.assert_called_once()
    args, kwargs = run_mock.call_args
    assert args[0] == ["alembic", "-c", "src/db/alembic.ini", "upgrade", "head"]
    assert kwargs["check"] is True
    # 注入 PYTHONPATH=ROOT，保证 alembic 子进程能 import src（见 upgrade_db.main 注释）
    assert kwargs["env"]["PYTHONPATH"].split(os.pathsep)[0] == upgrade_db.ROOT

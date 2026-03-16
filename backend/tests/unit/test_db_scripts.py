from unittest.mock import patch

from scripts import init_db, upgrade_db


def test_init_db_runs_existing_migrations_only():
    with patch("scripts.init_db.subprocess.run") as run_mock:
        init_db.main()

    run_mock.assert_called_once_with(["alembic", "upgrade", "head"], check=True)


def test_upgrade_db_runs_head_migration():
    with patch("scripts.upgrade_db.subprocess.run") as run_mock:
        upgrade_db.main()

    run_mock.assert_called_once_with(["alembic", "upgrade", "head"], check=True)

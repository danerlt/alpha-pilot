from unittest.mock import patch

from scripts import init_db, upgrade_db


def test_init_db_runs_existing_migrations_only():
    with patch("scripts.init_db.subprocess.run") as run_mock:
        init_db.main()

    run_mock.assert_called_once_with(["alembic", "upgrade", "head"], check=True)


@patch("scripts.upgrade_db.get_base_settings")
@patch("scripts.upgrade_db._needs_legacy_stamp")
@patch("scripts.upgrade_db.subprocess.run")
def test_upgrade_db_runs_head_migration(run_mock, needs_stamp_mock, settings_mock):
    settings_mock.return_value.DATABASE_URL = "postgresql://test"
    needs_stamp_mock.return_value = False

    upgrade_db.main()

    needs_stamp_mock.assert_called_once_with("postgresql://test")
    run_mock.assert_called_once_with(["alembic", "upgrade", "head"], check=True)


@patch("scripts.upgrade_db.get_base_settings")
@patch("scripts.upgrade_db._needs_legacy_stamp")
@patch("scripts.upgrade_db.subprocess.run")
def test_upgrade_db_stamps_legacy_schema_before_upgrade(run_mock, needs_stamp_mock, settings_mock):
    settings_mock.return_value.DATABASE_URL = "postgresql://test"
    needs_stamp_mock.return_value = True

    upgrade_db.main()

    assert run_mock.call_args_list == [
        ((["alembic", "stamp", "20260316_0001"],), {"check": True}),
        ((["alembic", "upgrade", "head"],), {"check": True}),
    ]

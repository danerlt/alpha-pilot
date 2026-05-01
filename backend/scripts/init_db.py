"""初始化数据库：执行现有 Alembic 迁移链到最新版本。"""
import os
import subprocess

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    print("Applying existing migrations to database...")
    subprocess.run(["alembic", "-c", "src/db/alembic.ini", "upgrade", "head"], check=True)
    print("Database initialized successfully.")


if __name__ == "__main__":
    main()

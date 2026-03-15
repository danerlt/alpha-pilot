"""初始化数据库：生成初始 Alembic 迁移并执行"""
import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    print("Generating initial migration...")
    result = subprocess.run(
        ["alembic", "revision", "--autogenerate", "-m", "initial_schema"],
        check=True,
    )
    print("Running migrations...")
    subprocess.run(["alembic", "upgrade", "head"], check=True)
    print("Database initialized successfully.")


if __name__ == "__main__":
    main()

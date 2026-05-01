"""运行所有待执行的 Alembic 迁移。"""
import os
import subprocess
import sys

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    print("Running pending migrations...")
    subprocess.run(["alembic", "-c", "src/db/alembic.ini", "upgrade", "head"], check=True)
    print("Migrations complete.")


if __name__ == "__main__":
    main()

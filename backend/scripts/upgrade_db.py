"""运行所有待执行的 Alembic 迁移"""
import subprocess
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    print("Running pending migrations...")
    subprocess.run(["alembic", "upgrade", "head"], check=True)
    print("Migrations complete.")


if __name__ == "__main__":
    main()

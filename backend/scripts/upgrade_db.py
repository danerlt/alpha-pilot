"""运行所有待执行的 Alembic 迁移。"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)


def main():
    print("Running pending migrations...")
    # alembic 是 console_script，不会像 uvicorn 那样自动把 cwd 加入 sys.path，
    # 否则 env.py 的 `from src...` 会 ModuleNotFoundError。显式注入 PYTHONPATH=ROOT。
    env = dict(os.environ)
    env["PYTHONPATH"] = ROOT + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    subprocess.run(
        ["alembic", "-c", "src/db/alembic.ini", "upgrade", "head"],
        check=True,
        env=env,
    )
    print("Migrations complete.")


if __name__ == "__main__":
    main()

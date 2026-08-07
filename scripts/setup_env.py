"""
Environment setup script for SentinelML.
Creates local .env from .env.example if missing.
"""
import os
import shutil
from pathlib import Path


def setup():
    root = Path(__file__).resolve().parent.parent
    env_file = root / ".env"
    env_example = root / ".env.example"

    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("Created .env from .env.example")
    elif env_file.exists():
        print(".env already exists")
    else:
        print(".env.example missing")


if __name__ == "__main__":
    setup()

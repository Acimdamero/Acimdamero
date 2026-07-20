"""Load config.yaml + .env."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def load_config() -> dict[str, Any]:
    load_dotenv()
    path = ROOT / "config.yaml"
    if not path.exists():
        path = ROOT / "config.example.yaml"
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text()) or {}

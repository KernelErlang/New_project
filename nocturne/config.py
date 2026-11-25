"""Where the Codex keeps its private files."""

from __future__ import annotations

import os
import sys
from pathlib import Path

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 6613
DB_NAME = "codex.sqlite3"
STATIC_DIR = Path(__file__).resolve().parent / "static"


def default_data_dir() -> Path:
    """The per-user data directory (override with ``NOCTURNE_HOME``)."""
    override = os.environ.get("NOCTURNE_HOME")
    if override:
        return Path(override).expanduser()
    home = Path.home()
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or home / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = home / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or home / ".local" / "share")
    return base / "NocturneCodex"

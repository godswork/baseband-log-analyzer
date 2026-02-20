from __future__ import annotations

import re
from pathlib import Path

ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]|\x1B\][^\x07]*\x07")


def strip_ansi(s: str) -> str:
    """Remove ANSI escape sequences from terminal output."""
    return ANSI_RE.sub("", s or "")


def sanitize_token(s: str, max_len: int = 40) -> str:
    """
    Turn an arbitrary string into a safe filename token:
    - strip ansi
    - replace spaces
    - keep [A-Za-z0-9._-]
    """
    s = strip_ansi(s or "").strip().replace(" ", "_")
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:max_len] if len(s) > max_len else s


def project_dir() -> Path:
    """Directory where this package resides (repo/bb_analyzer)."""
    return Path(__file__).resolve().parent


def repo_root() -> Path:
    """Repository root (repo/)."""
    return project_dir().parent

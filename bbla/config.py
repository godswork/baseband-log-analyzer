from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .utils import repo_root


@dataclass(frozen=True)
class Secrets:
    bb_user: str
    bb_passwords: list[str]
    sftp_password: str


@dataclass(frozen=True)
class SftpConfig:
    enabled: bool
    host: str
    port: int
    username: str
    remote_base_dir: str


@dataclass(frozen=True)
class AlarmFilter:
    noise_exact: list[str]
    noise_prefix: list[str]


@dataclass(frozen=True)
class AppArgs:
    ip: str
    moshell_path: Path
    out_dir: Path
    no_upload: bool
    config_dir: Path


def _load_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return default
    merged = default.copy()
    merged.update(data)
    return merged


def load_alarm_filter(config_dir: Path) -> AlarmFilter:
    data = _load_json(config_dir / "alarm_filter.json", {"noise_exact": [], "noise_prefix": []})
    noise_exact = data.get("noise_exact") or []
    noise_prefix = data.get("noise_prefix") or []
    if not isinstance(noise_exact, list):
        noise_exact = []
    if not isinstance(noise_prefix, list):
        noise_prefix = []
    return AlarmFilter(
        noise_exact=[str(x) for x in noise_exact],
        noise_prefix=[str(x) for x in noise_prefix],
    )


def load_secrets(config_dir: Path) -> Secrets:
    """
    secrets.json:
    {
      "baseband": {"username":"rbs", "passwords":["rbs","..."]},
      "sftp": {"password":"..."}
    }
    """
    data = _load_json(
        config_dir / "secrets.json",
        {"baseband": {"username": "rbs", "passwords": []}, "sftp": {"password": ""}},
    )
    bb = data.get("baseband", {}) or {}
    sftp = data.get("sftp", {}) or {}

    user = str(bb.get("username") or "rbs")
    pw_list = bb.get("passwords") or []
    if not isinstance(pw_list, list):
        pw_list = []
    pw_list = [str(p).strip() for p in pw_list if str(p).strip()]

    return Secrets(
        bb_user=user,
        bb_passwords=pw_list,
        sftp_password=str(sftp.get("password") or ""),
    )


def load_sftp_config(config_dir: Path) -> SftpConfig:
    """
    sftp.json:
    {"enabled":true,"host":"...","port":22,"username":"...","remote_base_dir":"/upload/bb-cases"}
    """
    data = _load_json(config_dir / "sftp.json", {"enabled": False})
    return SftpConfig(
        enabled=bool(data.get("enabled", False)),
        host=str(data.get("host") or ""),
        port=int(data.get("port") or 22),
        username=str(data.get("username") or ""),
        remote_base_dir=str(data.get("remote_base_dir") or "").rstrip("/"),
    )


def default_config_dir() -> Path:
    """
    By default use repo_root/configs (committed examples live there too).
    Users will create real configs in this folder locally.
    """
    return repo_root() / "configs"

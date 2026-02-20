from __future__ import annotations

import os
import posixpath
from pathlib import Path

from .config import SftpConfig


def sftp_mkdir_p(sftp, remote_dir: str) -> None:
    """
    mkdir -p for SFTP.
    """
    parts = []
    d = remote_dir
    while d not in ("/", ""):
        parts.append(d)
        d = posixpath.dirname(d)
    for p in reversed(parts):
        try:
            sftp.stat(p)
        except IOError:
            sftp.mkdir(p)


def upload_dir(local_dir: Path, cfg: SftpConfig, password: str) -> str:
    """
    Upload local_dir recursively to cfg.remote_base_dir/<case_dir_name>.
    """
    try:
        import paramiko
    except Exception as e:
        raise RuntimeError("paramiko is required for SFTP upload: pip install -r requirements.txt") from e

    if not (cfg.host and cfg.username and cfg.remote_base_dir):
        raise RuntimeError("SFTP enabled but sftp.json missing host/username/remote_base_dir")
    if not password:
        raise RuntimeError("SFTP enabled but secrets.json has empty sftp.password")

    transport = paramiko.Transport((cfg.host, cfg.port))
    transport.connect(username=cfg.username, password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)

    try:
        remote_case_dir = f"{cfg.remote_base_dir}/{local_dir.name}"
        sftp_mkdir_p(sftp, remote_case_dir)

        for root, _, files in os.walk(local_dir):
            root_path = Path(root)
            rel = root_path.relative_to(local_dir)
            remote_root = remote_case_dir if str(rel) == "." else f"{remote_case_dir}/{str(rel).replace(os.sep, '/')}"
            sftp_mkdir_p(sftp, remote_root)

            for fn in files:
                lp = root_path / fn
                rp = f"{remote_root}/{fn}"
                sftp.put(str(lp), rp)

        return remote_case_dir
    finally:
        try:
            sftp.close()
        except Exception:
            pass
        transport.close()

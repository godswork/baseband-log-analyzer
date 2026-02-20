from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from .config import (
    AppArgs,
    default_config_dir,
    load_alarm_filter,
    load_secrets,
    load_sftp_config,
)
from .moshell import MoShellSession
from .parsers import parse_hwpid, parse_llog, parse_lga
from .report import render_report
from .sftp_upload import upload_dir
from .utils import sanitize_token


def make_initial_case_dir(out_dir: Path, ip: str, ts: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    case_dir = out_dir / f"{ts}_{ip.replace('.', '_')}"
    (case_dir / "raw").mkdir(parents=True, exist_ok=True)
    return case_dir


def rename_case_dir(case_dir: Path, ts: str, hw) -> Path:
    market = sanitize_token(hw.market_name or "MARKET", 40)
    rev = sanitize_token(hw.product_revision or "REV", 10)
    sn = sanitize_token(hw.serial or "NOSERIAL", 30)

    new_base = f"{market}_{rev}_{sn}_{ts}"
    parent = case_dir.parent
    candidate = parent / new_base
    i = 2
    while candidate.exists():
        candidate = parent / f"{new_base}_{i}"
        i += 1

    import shutil

    shutil.move(str(case_dir), str(candidate))
    return candidate


def parse_args() -> AppArgs:
    p = argparse.ArgumentParser(description="BB log collector (MoShell): hwpid + llog -l + lga")
    p.add_argument("ip", help="Target IP, e.g. 169.254.2.2")
    p.add_argument("--out", default=str(Path.home() / "cases"), help="Output base dir (default: ~/cases)")
    p.add_argument("--moshell", default=str(Path.home() / "moshell/moshell"), help="Path to moshell script")
    p.add_argument("--config-dir", default=str(default_config_dir()), help="Config dir (default: repo/configs)")
    p.add_argument("--no-upload", action="store_true", help="Disable SFTP upload even if enabled in sftp.json")
    args = p.parse_args()

    moshell_path = Path(args.moshell).expanduser()
    if not moshell_path.is_absolute():
        moshell_path = Path.home() / moshell_path
    if not moshell_path.exists():
        raise SystemExit(f"ERROR: moshell not found: {moshell_path}")

    return AppArgs(
        ip=args.ip.strip(),
        moshell_path=moshell_path,
        out_dir=Path(args.out).expanduser(),
        no_upload=bool(args.no_upload),
        config_dir=Path(args.config_dir).expanduser(),
    )


def main() -> int:
    args = parse_args()
    ts = time.strftime("%Y%m%d_%H%M%S")

    alarm_filter = load_alarm_filter(args.config_dir)
    secrets = load_secrets(args.config_dir)
    sftp_cfg = load_sftp_config(args.config_dir)

    # case.json skeleton (we update along the way)
    meta: dict[str, Any] = {
        "timestamp": ts,
        "ip": args.ip,
        "moshell_script": str(args.moshell_path),
        "paths": {},
        "login": {},
        "commands": {},
        "hw": {},
        "report": {"generated": False},
        "upload": {"enabled": bool(sftp_cfg.enabled) and not args.no_upload, "attempted": False},
    }

    print(f"Connecting to moshell {args.ip} ...")

    case_dir = make_initial_case_dir(args.out_dir, args.ip, ts)
    raw_dir = case_dir / "raw"
    meta["paths"]["case_dir_initial"] = str(case_dir)
    meta["paths"]["raw_dir_initial"] = str(raw_dir)

    def save_meta(where: Path) -> None:
        (where / "case.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    sess = MoShellSession(args.moshell_path, args.ip)

    try:
        sess.open()
        prompt = sess.login_with_passwords(secrets.bb_user, secrets.bb_passwords)
        meta["login"] = {"ok": True, "prompt": prompt}
        print(f"Login OK, prompt: {prompt}")

        def collect(name: str, cmd: str, timeout: int, filename: str) -> str:
            out, dur = sess.run(cmd, timeout=timeout)
            (raw_dir / filename).write_text(out, encoding="utf-8")
            meta["commands"][name] = {
                "cmd": cmd,
                "ok": True,
                "timeout_s": timeout,
                "duration_s": round(dur, 3),
                "file": f"raw/{filename}",
            }
            return out

        hwpid_txt = collect("hwpid", "hwpid", timeout=300, filename="hwpid.txt")
        llog_txt = collect("llog", "llog -l", timeout=300, filename="llog.txt")
        lga_txt = collect("lga", "lga", timeout=1200, filename="lga.txt")

        hw = parse_hwpid(hwpid_txt)
        meta["hw"] = {
            "market_name": hw.market_name,
            "product_revision": hw.product_revision,
            "serial": hw.serial,
            "product_date": hw.product_date,
            "product_name": hw.product_name,
            "product_number": hw.product_number,
        }

        new_case_dir = rename_case_dir(case_dir, ts, hw)
        raw_dir = new_case_dir / "raw"
        meta["paths"]["case_dir"] = str(new_case_dir)
        meta["paths"]["raw_dir"] = str(raw_dir)

        # report always
        restarts = parse_llog(llog_txt)
        alarms = parse_lga(lga_txt)
        report_text = render_report(ts, hw, restarts, alarms, alarm_filter)

        (new_case_dir / "report.txt").write_text(report_text, encoding="utf-8")
        meta["report"] = {"generated": True, "file": "report.txt"}

        save_meta(new_case_dir)

        # print report
        print("\n" + report_text)

        # upload
        if meta["upload"]["enabled"] and sftp_cfg.enabled:
            meta["upload"]["attempted"] = True
            try:
                remote = upload_dir(new_case_dir, sftp_cfg, secrets.sftp_password)
                meta["upload"]["ok"] = True
                meta["upload"]["remote_path"] = remote
                save_meta(new_case_dir)
                print(f"Uploaded to SFTP: {remote}")
            except Exception as e:
                meta["upload"]["ok"] = False
                meta["upload"]["error"] = str(e)
                save_meta(new_case_dir)
                print(f"SFTP upload failed: {e}", file=sys.stderr)

        print(f"Saved raw files to: {new_case_dir / 'raw'}")
        print(f"Saved report: {new_case_dir / 'report.txt'}")
        print(f"Saved case.json: {new_case_dir / 'case.json'}")
        print(f"Case: {new_case_dir}")
        return 0

    except Exception as e:
        meta["error"] = str(e)
        try:
            save_meta(case_dir)
        except Exception:
            pass
        raise
    finally:
        sess.close()


if __name__ == "__main__":
    raise SystemExit(main())

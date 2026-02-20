from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

RE_LLOG_NO = re.compile(r"^\s*No:\s*\d+\s*$")
RE_LLOG_FIELD = re.compile(r"^\s*([A-Za-z]+)\s*:\s*(.*)$")
RE_LGA_ROW = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\s")


@dataclass(frozen=True)
class HwInfo:
    market_name: str | None = None
    product_revision: str | None = None
    serial: str | None = None
    product_date: str | None = None
    product_name: str | None = None
    product_number: str | None = None


@dataclass(frozen=True)
class RestartEvent:
    no: str | None
    time: str | None
    reason: str | None
    rank: str | None
    extra: str | None
    program: str | None
    pid: str | None
    signal: str | None
    pmd: str | None


@dataclass(frozen=True)
class AlarmEvent:
    time: str
    typ: str
    sev: str
    desc: str
    details: str


def parse_hwpid(text: str) -> HwInfo:
    def get(label: str) -> Optional[str]:
        m = re.search(rf"^{re.escape(label)}\s*:\s*(.+)$", text, flags=re.M)
        return m.group(1).strip() if m else None

    return HwInfo(
        market_name=get("Market Name"),
        product_revision=get("Product Revision"),
        serial=get("Product Serial Number"),
        product_date=get("Product Date"),
        product_name=get("Product Name"),
        product_number=get("Product Number"),
    )


def parse_llog(text: str) -> list[RestartEvent]:
    """
    Robust parser for llog -l:
    - detects entries by 'No:' anchors
    - supports multiline fields (continuation lines)
    """
    lines = text.splitlines()
    starts = [i for i, ln in enumerate(lines) if RE_LLOG_NO.match(ln)]
    if not starts:
        return []
    starts.append(len(lines))

    events: list[RestartEvent] = []
    for a, b in zip(starts, starts[1:]):
        block = lines[a:b]
        raw: dict[str, str] = {}
        cur_key: str | None = None

        for ln in block:
            m = RE_LLOG_FIELD.match(ln)
            if m:
                key = m.group(1).strip().lower()
                val = m.group(2).rstrip().strip()
                raw[key] = val
                cur_key = key
            else:
                if cur_key and ln.strip():
                    raw[cur_key] = (raw.get(cur_key, "") + "\n" + ln.rstrip()).strip()

        ev = RestartEvent(
            no=raw.get("no"),
            time=raw.get("time"),
            reason=raw.get("reason"),
            rank=raw.get("rank"),
            extra=raw.get("extra"),
            program=raw.get("program"),
            pid=raw.get("pid"),
            signal=raw.get("signal"),
            pmd=raw.get("pmd"),
        )
        if ev.no and ev.time:
            events.append(ev)

    events.sort(key=lambda e: e.time or "")
    return events


def parse_lga(text: str) -> list[AlarmEvent]:
    """
    Parse lga table output.
    """
    alarms: list[AlarmEvent] = []
    lines = text.splitlines()
    in_table = False

    for ln in lines:
        s = ln.rstrip()
        if not s:
            continue

        if s.startswith("Timestamp") and "Sev" in s:
            in_table = True
            continue
        if in_table and s.startswith("===="):
            continue
        if not in_table:
            continue

        if not RE_LGA_ROW.match(s):
            continue

        ts = s[:19]
        rest = s[19:].strip()
        m = re.match(r"^(?P<type>\S+)\s+(?P<sev>\S)\s+(?P<tail>.+)$", rest)
        if not m:
            continue

        typ = m.group("type")
        sev = m.group("sev")
        tail = m.group("tail")

        parts = re.split(r"\s{2,}", tail, maxsplit=1)
        desc = parts[0].strip()
        details = parts[1].strip() if len(parts) > 1 else ""

        alarms.append(AlarmEvent(time=ts, typ=typ, sev=sev, desc=desc, details=details))

    return alarms

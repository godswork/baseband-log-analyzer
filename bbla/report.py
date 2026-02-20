from __future__ import annotations

from collections import Counter

from .config import AlarmFilter
from .parsers import AlarmEvent, HwInfo, RestartEvent


def is_noise_desc(desc: str, flt: AlarmFilter) -> bool:
    if desc in set(flt.noise_exact):
        return True
    for p in flt.noise_prefix:
        if desc.startswith(p):
            return True
    return False


def crash_like_restarts(events: list[RestartEvent]) -> list[RestartEvent]:
    """
    Minimal engineering signal:
    - signal/program/pmd not '-'
    - or reason contains 'restart request'
    """
    out: list[RestartEvent] = []
    for e in events:
        reason = (e.reason or "").lower()
        if (
            (e.signal and e.signal != "-")
            or (e.program and e.program != "-")
            or (e.pmd and e.pmd != "-")
            or ("restart request" in reason)
        ):
            out.append(e)
    return out


def render_report(ts: str, hw: HwInfo, restarts: list[RestartEvent], alarms: list[AlarmEvent], flt: AlarmFilter) -> str:
    lines: list[str] = []
    lines.append(f"CASE: {ts}")
    lines.append(f"HW: {hw.market_name or '-'} | Rev {hw.product_revision or '-'} | SN {hw.serial or '-'}")
    lines.append("")

    sus = crash_like_restarts(restarts)
    lines.append("CRASH-LIKE RESTARTS")
    if not sus:
        lines.append("  - none detected")
    else:
        for e in sus:
            extra = (e.extra or "-").replace("\n", " ")
            if len(extra) > 180:
                extra = extra[:177] + "..."
            lines.append(
                f"  - [{e.no}] {e.time} | {e.reason} | Program={e.program} | Signal={e.signal} | PMD={e.pmd}"
            )
            lines.append(f"    Extra: {extra}")
    lines.append("")

    filtered = [a for a in alarms if a.desc and not is_noise_desc(a.desc, flt)]
    lines.append("POTENTIALLY IMPORTANT ALARMS")
    lines.append(f"Total alarms (filtered): {len(filtered)}")

    cnt = Counter(a.desc for a in filtered)
    if not cnt:
        lines.append("  - none (after filtering known noise)")
    else:
        for desc, n in cnt.most_common():
            lines.append(f"  - {desc}: {n}")

    return "\n".join(lines).rstrip() + "\n"

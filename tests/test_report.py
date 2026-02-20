from bb_analyzer.config import AlarmFilter
from bb_analyzer.parsers import HwInfo, RestartEvent, AlarmEvent
from bb_analyzer.report import render_report


def test_report_filters_noise_alarms_and_shows_crash_like():
    hw = HwInfo(market_name="Baseband 6648", product_revision="R3A", serial="TD3Q873261")

    restarts = [
        RestartEvent(
            no="2",
            time="2023-07-06 18:49:46",
            reason="Restart request",
            rank="Cold",
            extra="Recovery action initiated",
            program="ricm",
            pid="6967",
            signal="SIGABRT",
            pmd="pmd-bc_server-6967-20230706-184946",
        )
    ]

    alarms = [
        AlarmEvent(
            time="2025-11-11 10:40:13",
            typ="AL",
            sev="m",
            desc="SFP Not Present",
            details="FieldReplaceableUnit=BB52,SfpModule=A",
        ),
        AlarmEvent(
            time="2025-11-11 10:39:09",
            typ="AL",
            sev="C",
            desc="License Key File Fault",
            details="Lm=1 (Key file fault...)",
        ),
        AlarmEvent(
            time="2025-11-11 10:40:21",
            typ="AL",
            sev="m",
            desc="Ethernet Link Failure",
            details="EthernetPort=TN_A",
        ),
    ]

    flt = AlarmFilter(
        noise_exact=["SFP Not Present", "License Key File Fault"],
        noise_prefix=["Certificate Management "],
    )

    report = render_report("20260218_154508", hw, restarts, alarms, flt)

    # Crash-like restart should be present
    assert "CRASH-LIKE RESTARTS" in report
    assert "SIGABRT" in report
    assert "Restart request" in report

    # Noise alarms should be filtered out
    assert "SFP Not Present" not in report
    assert "License Key File Fault" not in report

    # Important alarm remains
    assert "Ethernet Link Failure" in report

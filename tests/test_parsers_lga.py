from bb_analyzer.parsers import parse_lga


def test_parse_lga_table_rows():
    sample = """
======================================================================================================
Timestamp (UTC)     Type Sev    Description
======================================================================================================
2025-11-11 10:39:09 AL   C      License Key File Fault              Lm=1  (Key file fault in Managed Element AI: eventId=1)
2025-11-11 10:40:13 AL   m      SFP Not Present                     FieldReplaceableUnit=BB52,SfpModule=A  (No SFP or electrical cable plugged in.)
2025-11-11 14:44:27 AL   m      Calendar Clock All NTP Servers Unavailable SysM=1  (No NTP server configured, or no NTP service available)
"""
    alarms = parse_lga(sample)
    assert len(alarms) == 3
    assert alarms[0].time == "2025-11-11 10:39:09"
    assert alarms[0].sev == "C"
    assert alarms[0].desc == "License Key File Fault"
    assert "eventId=1" in alarms[0].details

    assert alarms[1].desc == "SFP Not Present"
    assert alarms[2].desc.startswith("Calendar Clock All NTP Servers Unavailable")

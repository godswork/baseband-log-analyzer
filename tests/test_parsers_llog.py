from bb_analyzer.parsers import parse_llog


def test_parse_llog_basic_sample():
    sample = """
---------------------------------------------------
No:       1
Reason:   Ordered restart
Time:     2025-11-12 08:51:03
Program:  -
Pid:      -
Rank:     Cold With Test
Signal:   -
PMD:      -
Extra:    'Manual COLI restart'
---------------------------------------------------
No:       2
Reason:   Power on (SW)
Time:     2025-11-12 08:57:00
Program:  -
Pid:      -
Rank:     Cold
Signal:   -
PMD:      -
Extra:    -
---------------------------------------------------
"""
    events = parse_llog(sample)
    assert len(events) == 2
    assert events[0].no == "1"
    assert events[0].reason == "Ordered restart"
    assert events[0].time == "2025-11-12 08:51:03"
    assert events[0].rank == "Cold With Test"
    assert events[0].extra == "'Manual COLI restart'"
    assert events[1].reason == "Power on (SW)"


def test_parse_llog_crash_like_sample():
    sample = """
No: 2
Reason: Restart request
Time: 2023-07-06 18:49:46
Program: ricm
Pid: 6967
Rank: Cold
Signal: SIGABRT
PMD: pmd-bc_server-6967-20230706-184946
Extra: Recovery action initiated by DU via BCI, faultId: 0x300 (HwfForEvaluation),
 faultDescription: /repo/catbuilder/.../bc_restart.c:114

No: 4
Reason: Restart request
Time: 2023-07-06 18:52:37
Program: ricm
Pid: 6611
Rank: Cold With Test
Signal: SIGABRT
PMD: pmd-bc_server-6611-20230706-185237
Extra: Recovery action initiated by DU via BCI, faultId: 0x300 (HwfForEvaluation), faultDescription: /repo/.../bc_restart.c:114
"""
    events = parse_llog(sample)
    assert len(events) == 2
    assert events[0].program == "ricm"
    assert events[0].signal == "SIGABRT"
    assert events[0].pmd.startswith("pmd-bc_server-")
    # multiline extra should be preserved (may include newline)
    assert "Recovery action initiated" in (events[0].extra or "")

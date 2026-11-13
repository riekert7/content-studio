import pytest

from content_studio.beats import Beat, check_beats, parse_beats
from content_studio.cli import main

TABLE = """| Start | End | Beat | Carries |
|---|---|---|---|
| 0.0 | 2.0 | Lumen Coffee mug on the counter | the cup |
| 2.0 | 5.0 | Pour the pour-over | the mug |
| 5.0 | 7.0 | Drink the coffee | |
"""


def mk(*lengths, carries="x", first="Lumen Coffee mug", last="Lumen again"):
    out, t = [], 0.0
    for i, n in enumerate(lengths):
        text = first if i == 0 else last if i == len(lengths) - 1 else "middle"
        out.append(Beat(t, t + n, text, "" if i == len(lengths) - 1 else carries))
        t += n
    return out


def test_parse_ok():
    beats = parse_beats(TABLE)
    assert len(beats) == 3
    assert beats[1].carries == "the mug"
    assert beats[2].carries == ""


def test_hook_over_3s_flagged():
    assert any("hook" in f for f in check_beats(mk(3.5, 1.0, 2.0, 2.0)))


def test_beat_over_4s_flagged():
    assert any("beat" in f for f in check_beats(mk(2.0, 4.5, 1.0, 1.0)))


def test_uniform_lengths_flagged():
    assert any("vary" in f for f in check_beats(mk(2.0, 2.0, 2.0, 2.0)))


def test_varied_lengths_clean():
    assert check_beats(mk(1.0, 4.0, 1.5)) == []


def test_missing_carries_flagged():
    beats = mk(1.0, 4.0, 1.5)
    beats[0].carries = ""
    assert any("carries" in f for f in check_beats(beats))


def test_no_loop_flagged():
    assert any("loop" in f for f in check_beats(mk(1.0, 4.0, 1.5, last="zzz")))


def test_bad_table_error_has_line_number():
    with pytest.raises(ValueError, match="line 1"):
        parse_beats("no table")


def test_bad_time_and_order():
    with pytest.raises(ValueError, match="line 3"):
        parse_beats("| Start | End | Beat | Carries |\n|---|---|---|---|\n| a | 2 | x | y |")
    with pytest.raises(ValueError, match="end"):
        parse_beats("| Start | End | Beat | Carries |\n|---|---|---|---|\n| 2 | 2 | x | y |")


def test_cli_beats_exit_codes(tmp_path, capsys):
    ok = tmp_path / "ok.md"
    ok.write_text("| Start | End | Beat | Carries |\n|---|---|---|---|\n"
                  "| 0 | 1 | Lumen mug | a |\n| 1 | 5 | pour | b |\n| 5 | 6.5 | the Lumen mug | |\n")
    assert main(["beats", str(ok)]) == 0
    bad = tmp_path / "bad.md"
    bad.write_text("nope")
    assert main(["beats", str(bad)]) == 2
    assert main(["beats", str(tmp_path / "missing.md")]) == 2
    assert main(["beats", str(tmp_path / "t.md")]) == 2


def test_cli_passthrough(tmp_path, capsys):
    f = tmp_path / "a.txt"
    f.write_text("Lumen Coffee opens at six. We pour slowly.\n")
    assert main(["detect", str(f)]) in (0, 1)
    assert "SLOP" in capsys.readouterr().out.upper()
    assert main(["hookscore", "--hook", "I lost $18,000 on one missing contract."]) in (0, 1)

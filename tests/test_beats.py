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
    flags = check_beats(mk(3.5, 1.0, 2.0, 2.0))
    assert [f for f in flags if f.startswith("hook")] and not [f for f in flags if f.startswith("beat")]


def test_beat_over_4s_flagged():
    flags = check_beats(mk(2.0, 4.5, 1.0, 1.0))
    assert [f for f in flags if f.startswith("beat 2")] and not [f for f in flags if f.startswith("hook")]


def test_uniform_lengths_flagged():
    flags = check_beats(mk(2.0, 2.0, 2.0, 2.0))
    assert len(flags) == 1 and "vary" in flags[0]


def test_varied_lengths_clean():
    assert check_beats(mk(1.0, 4.0, 1.5)) == []


def test_missing_carries_flagged():
    beats = mk(1.0, 4.0, 1.5)
    beats[0].carries = ""
    flags = check_beats(beats)
    assert len(flags) == 1 and "carries" in flags[0]


def test_no_loop_flagged():
    flags = check_beats(mk(1.0, 4.0, 1.5, last="zzz"))
    assert len(flags) == 1 and "loop" in flags[0]


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


H = "| Start | End | Beat | Carries |\n|---|---|---|---|\n"


def test_blank_line_inside_table_is_fine():
    assert len(parse_beats(H + "| 0 | 1 | a | b |\n\n| 1 | 5 | c | d |\n")) == 2


def test_text_inside_table_raises():
    with pytest.raises(ValueError, match="line 4: unexpected text"):
        parse_beats(H + "| 0 | 1 | a | b |\nnote\n| 1 | 5 | c | d |\n")


def test_second_table_raises():
    with pytest.raises(ValueError, match="line 4"):
        parse_beats(H + "| 0 | 1 | a | b |\nmore:\n" + H)
    with pytest.raises(ValueError):
        parse_beats(H + "| 0 | 1 | a | b |\n\n" + H + "| 1 | 2 | c | d |\n")


def test_trailing_prose_is_fine():
    assert len(parse_beats(H + "| 0 | 1 | a | b |\n\nNotes: none.\n")) == 1


@pytest.mark.parametrize("bad", ["nan", "inf", "-inf", "-1"])
def test_non_finite_and_negative_start(bad):
    with pytest.raises(ValueError, match="line 3"):
        parse_beats(H + f"| {bad} | 2 | a | b |\n")


def test_non_finite_end():
    with pytest.raises(ValueError, match="line 3"):
        parse_beats(H + "| 0 | inf | a | b |\n")
    with pytest.raises(ValueError, match="line 3"):
        parse_beats(H + "| 0 | nan | a | b |\n")


def test_exact_boundaries_pass():
    assert check_beats(mk(3.0, 4.0, 0.75, last="Lumen again")) == []


def test_crlf_and_single_beat():
    beats = parse_beats((H + "| 0 | 2 | Lumen mug | |\n").replace("\n", "\r\n"))
    assert len(beats) == 1 and beats[0].carries == ""
    assert check_beats(beats) == []


def test_bom_file(tmp_path):
    f = tmp_path / "b.md"
    f.write_bytes(b"\xef\xbb\xbf" + (H + "| 0 | 2 | Lumen mug | |\n").encode())
    assert main(["beats", str(f)]) == 0


def test_truncated_file_exits_2(tmp_path):
    f = tmp_path / "t.md"
    f.write_text(H + "| 0 | 1 | a | b |\nnote\n| 1 | 5 | c | d |\n")
    assert main(["beats", str(f)]) == 2


def test_zero_length_beat_no_crash():
    beats = [Beat(0.0, 1.0, "Lumen", "x"), Beat(1.0, 1.0, "mid", "x"), Beat(1.0, 2.0, "Lumen", "")]
    flags = check_beats(beats)
    assert any("zero" in f for f in flags)


def test_argv_restored():
    import sys
    before = list(sys.argv)
    main(["hookscore", "--json", "--hook", "I lost $18,000 on one missing contract."])
    assert sys.argv == before

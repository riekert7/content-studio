import json
import subprocess
from pathlib import Path

from content_studio.check import check_video
from content_studio.cli import main
from content_studio.cover import make_cover, make_sheet

FIXTURE = Path(__file__).parent / "fixtures" / "ref.mp4"


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True)


def test_fixture_is_9_16_with_audio():
    r = check_video(FIXTURE)
    assert r["info"]["audio"] and r["info"]["width"] * 16 == r["info"]["height"] * 9
    assert not any("9:16" in f or "audio" in f for f in r["flags"])


def test_silent_video_flagged(tmp_path):
    out = tmp_path / "silent.mp4"
    ffmpeg("-i", FIXTURE, "-an", "-c:v", "copy", out)
    assert any("audio" in f for f in check_video(out)["flags"])


def test_landscape_flagged(tmp_path):
    out = tmp_path / "wide.mp4"
    ffmpeg("-i", FIXTURE, "-vf", "scale=480:270,setsar=1", "-c:a", "copy", out)
    assert any("9:16" in f for f in check_video(out)["flags"])


def test_fps_flagged(tmp_path):
    out = tmp_path / "24.mp4"
    ffmpeg("-i", FIXTURE, "-r", "24", "-c:a", "copy", out)
    assert any("fps" in f for f in check_video(out)["flags"])


def quiet(tmp_path):
    out = tmp_path / "quiet.mp4"
    ffmpeg("-i", FIXTURE, "-af", "volume=-20dB", "-c:v", "copy", out)
    return out


def test_loudness_reported_and_clean_fixture_not_flagged():
    r = check_video(FIXTURE)
    assert isinstance(r["info"]["lufs"], float) and r["flags"] == []


def test_quiet_video_flagged(tmp_path):
    assert any("loud" in f for f in check_video(quiet(tmp_path))["flags"])


def test_unreadable_file_raises(tmp_path):
    bad = tmp_path / "x.mp4"
    bad.write_bytes(b"nope")
    import pytest
    with pytest.raises(ValueError):
        check_video(bad)


def test_check_cli_exit_codes(tmp_path, capsys):
    assert main(["check", str(FIXTURE)]) == 0
    capsys.readouterr()
    assert main(["check", str(quiet(tmp_path))]) == 1
    assert "loud" in capsys.readouterr().out
    assert main(["check", str(tmp_path / "missing.mp4")]) == 2
    assert "cs check" in capsys.readouterr().err


def test_check_cli_json(capsys):
    main(["check", str(FIXTURE), "--json"])
    assert json.loads(capsys.readouterr().out)["info"]["fps"] == 30


def test_cover_is_1080x1920_and_grid_preview(tmp_path):
    out = make_cover(FIXTURE, tmp_path / "cover.jpg", at=1.0, title="Lumen Coffee runs out at nine")
    assert out.exists() and (tmp_path / "cover.grid.jpg").exists()
    size = lambda p: subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(p)],  # noqa: E731
                                    capture_output=True, text=True).stdout.strip()
    assert size(out) == "1080,1920" and size(tmp_path / "cover.grid.jpg") == "1080,1440"


def test_cover_title_with_quotes_and_colons(tmp_path):
    make_cover(FIXTURE, tmp_path / "c.jpg", at=0.5, title="It's 5:00 - \"late\" %{x} 100%")
    assert (tmp_path / "c.jpg").exists()


def test_cover_without_title(tmp_path):
    assert make_cover(FIXTURE, tmp_path / "c.jpg", at=0.5, title="").exists()


def test_sheet_written(tmp_path):
    assert make_sheet(FIXTURE, tmp_path / "sheet.jpg").exists()


def test_cover_cli(tmp_path, capsys):
    out = tmp_path / "c.jpg"
    assert main(["cover", str(FIXTURE), "--at", "1", "--title", "Hi", "--out", str(out)]) == 0
    assert out.exists() and str(out) in capsys.readouterr().out
    assert main(["cover", str(tmp_path / "nope.mp4"), "--out", str(out)]) == 2
    assert main(["cover", str(FIXTURE), "--sheet", "--out", str(tmp_path / "s.jpg")]) == 0

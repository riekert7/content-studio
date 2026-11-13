import shutil
import subprocess
from pathlib import Path

import pytest

from content_studio.cli import main
from content_studio.motion import cuts
from content_studio.watch import WatchError, watch

FIXTURE = Path(__file__).parent / "fixtures" / "ref.mp4"


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True)


def test_local_file_makes_sheets(tmp_path):
    d = watch(str(FIXTURE), tmp_path, transcribe=False)
    assert (d / "hook.jpg").exists() and (d / "scenes-01.jpg").exists()
    assert d == tmp_path / "local-ref" and (d / "video.mp4").exists()


def test_cut_found_at_2s():
    found = cuts(FIXTURE)
    assert len(found) == 1 and abs(found[0] - 2.0) < 0.2


def test_download_failure_names_local_file_option(monkeypatch, capsys):
    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")

    def fail(cmd, **kw):
        raise subprocess.CalledProcessError(1, cmd, stderr="blocked")

    monkeypatch.setattr(subprocess, "run", fail)
    with pytest.raises(WatchError, match="local file"):
        watch("https://x.invalid/v")
    assert main(["watch", "https://x.invalid/v"]) == 2
    assert "Traceback" not in capsys.readouterr().err


def test_missing_yt_dlp_message(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda name: None)
    with pytest.raises(WatchError, match="yt-dlp"):
        watch("https://x.invalid/v")


def test_missing_ffmpeg_message(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda name: None)
    with pytest.raises(WatchError, match="ffmpeg"):
        watch(str(FIXTURE))


def test_not_a_file_or_url(tmp_path, capsys):
    with pytest.raises(WatchError, match="not a file"):
        watch(str(tmp_path / "nope.mp4"))
    assert main(["watch", str(tmp_path / "nope.mp4")]) == 2
    assert "Traceback" not in capsys.readouterr().err


def test_unreadable_file(tmp_path):
    junk = tmp_path / "junk.mp4"
    junk.write_bytes(b"not a video at all")
    with pytest.raises(WatchError, match="video"):
        watch(str(junk), tmp_path / "out", transcribe=False)


def test_no_video_stream(tmp_path):
    wav = tmp_path / "tone.wav"
    ffmpeg("-f", "lavfi", "-i", "sine=d=1", wav)
    with pytest.raises(WatchError, match="video"):
        watch(str(wav), tmp_path / "out", transcribe=False)


def test_short_video_and_spaces_and_rerun(tmp_path):
    short = tmp_path / "my short clip.mp4"
    ffmpeg("-i", FIXTURE, "-t", "1", "-c", "copy", short)
    before = short.read_bytes()
    out = tmp_path / "out dir"
    d = watch(str(short), out, transcribe=False)
    assert d.name == "local-my short clip" and (d / "hook.jpg").exists()
    watch(str(short), out, transcribe=False)  # existing folder: reused
    assert short.read_bytes() == before


def test_no_audio_track_notes_it(tmp_path):
    silent = tmp_path / "silent.mp4"
    ffmpeg("-i", FIXTURE, "-an", "-c:v", "copy", silent)
    d = watch(str(silent), tmp_path / "out")
    assert "no audio" in (d / "transcript.txt").read_text()


def test_cli_prints_folder_last(tmp_path, capsys):
    assert main(["watch", str(FIXTURE), "--out", str(tmp_path), "--no-transcript"]) == 0
    cap = capsys.readouterr()
    assert cap.out.strip().splitlines()[-1] == str(tmp_path.resolve() / "local-ref")
    assert not (tmp_path / "local-ref" / "transcript.txt").exists()


@pytest.mark.slow
def test_transcript_written(tmp_path, monkeypatch):
    monkeypatch.setenv("CS_WHISPER_MODEL", "tiny")
    d = watch(str(FIXTURE), tmp_path)
    assert (d / "transcript.txt").exists()

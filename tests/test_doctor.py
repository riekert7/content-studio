import json
import subprocess

from content_studio.cli import main
from content_studio.doctor import allow_list, probe_url, run_checks

PRESENT = lambda name: f"/usr/bin/{name}"  # noqa: E731


def test_all_present_ok():
    checks = run_checks(which=PRESENT, whisper_cached=True)
    assert all(c.ok for c in checks if c.required)


def test_missing_ffmpeg_reports_fix():
    checks = run_checks(which=lambda n: None if n == "ffmpeg" else PRESENT(n), whisper_cached=True)
    ffmpeg = next(c for c in checks if c.name == "ffmpeg")
    assert not ffmpeg.ok and ffmpeg.required and ffmpeg.fix


def test_node_not_required_in_v01():
    checks = run_checks(which=lambda n: None if n in ("node", "npx") else PRESENT(n), whisper_cached=True)
    assert {c.name: c.required for c in checks}["node"] is False
    assert all(c.ok for c in checks if c.required)


def test_whisper_model_missing_is_not_blocking():
    c = next(c for c in run_checks(which=PRESENT, whisper_cached=False) if c.name == "whisper model")
    assert not c.ok and not c.required and "MB" in c.fix


def test_allow_list_is_valid_json_with_websearch():
    rules = json.loads(json.dumps(allow_list()))["permissions"]["allow"]
    assert "WebSearch" in rules and any(r.startswith("Bash(uvx --from") and "content-studio" in r for r in rules)


def test_probe_failure_mentions_local_file():
    run = lambda *a, **k: subprocess.CompletedProcess(a, 1, "", "ERROR: blocked")  # noqa: E731
    ok, msg = probe_url("https://x.invalid/v", run=run)
    assert not ok and "local file" in msg


def test_probe_success():
    run = lambda *a, **k: subprocess.CompletedProcess(a, 0, "", "")  # noqa: E731
    assert probe_url("https://x.invalid/v", run=run)[0] is True


def test_marker_written_to_cache_dir_not_plugin(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    main(["doctor"])
    marker = json.loads((tmp_path / "content-studio" / "doctor.json").read_text())
    assert set(marker) == {"checked", "ok"}
    assert "ffmpeg" in capsys.readouterr().out


def test_cli_allow_prints_json(capsys):
    assert main(["doctor", "--allow"]) == 0
    assert "WebSearch" in json.loads(capsys.readouterr().out)["permissions"]["allow"]


def test_cli_exit_1_when_required_missing(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    monkeypatch.setenv("PATH", str(tmp_path))  # nothing on PATH
    assert main(["doctor"]) == 1
    assert "MISSING" in capsys.readouterr().out

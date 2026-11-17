"""Environment checks for a first run. Reports only; never installs or downloads anything."""
import json
import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

NO_DOWNLOAD = ("Could not read that link (Instagram, TikTok and sometimes YouTube block downloads). "
               "Download the video yourself and use the local file instead.")


@dataclass
class Check:
    name: str
    ok: bool
    required: bool
    fix: str


def _fix(tool: str) -> str:
    os_name = platform.system()
    if tool == "yt-dlp":
        return "brew install yt-dlp" if os_name == "Darwin" else "winget install yt-dlp" if os_name == "Windows" else "pipx install yt-dlp   (or: uv tool install yt-dlp)"
    if tool == "uv":
        return "winget install astral-sh.uv" if os_name == "Windows" else "curl -LsSf https://astral.sh/uv/install.sh | sh   (or: brew install uv)"
    pkg = {"ffmpeg": "ffmpeg", "node": "nodejs", "npx": "nodejs"}[tool]
    if os_name == "Darwin":
        return f"brew install {'node' if pkg == 'nodejs' else pkg}"
    if os_name == "Windows":
        return "winget install Gyan.FFmpeg" if pkg == "ffmpeg" else "winget install OpenJS.NodeJS.LTS"
    return f"sudo apt install {pkg}   (Arch: sudo pacman -S {pkg}; Fedora: sudo dnf install {pkg})"


def whisper_model_cached() -> bool:
    hub = Path(os.environ.get("HF_HUB_CACHE") or Path(os.environ.get("HF_HOME") or Path.home() / ".cache" / "huggingface") / "hub")
    return any(hub.glob("models--*faster-whisper*"))


def run_checks(which=shutil.which, whisper_cached: bool | None = None) -> list[Check]:
    needed = [("ffmpeg", True), ("ffprobe", True), ("uv", True), ("yt-dlp", True), ("node", False), ("npx", False)]
    checks = [Check(n, bool(which(n)), req, _fix("ffmpeg" if n == "ffprobe" else n)) for n, req in needed]
    cached = whisper_model_cached() if whisper_cached is None else whisper_cached
    checks.append(Check("whisper model", cached, False,
                        "downloads about 500 MB the first time you run cs watch with a transcript (use --no-transcript to skip)"))
    return checks


def allow_list() -> dict:
    """Rules to paste into .claude/settings.json: a plugin cannot ship permissions, so the user adds them."""
    # the exact pinned source: a wildcard like *content-studio* would also approve any look-alike package
    from content_studio.cli import VERSION

    src = f"git+https://github.com/riekert7/content-studio@v{VERSION}"
    return {"permissions": {"allow": ["WebSearch", "WebFetch", f'Bash(uvx --from "{src}" cs *)']}}


def probe_url(url: str, run=subprocess.run) -> tuple[bool, str]:
    try:
        r = run(["yt-dlp", "--simulate", "--no-warnings", "--no-playlist", "--", url], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return False, NO_DOWNLOAD
    return (True, "that link can be downloaded") if r.returncode == 0 else (False, NO_DOWNLOAD)


def write_marker(ok: bool) -> None:
    d = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "content-studio"
    try:
        d.mkdir(parents=True, exist_ok=True)
        (d / "doctor.json").write_text(json.dumps({"checked": datetime.now(timezone.utc).isoformat(timespec="seconds"), "ok": ok}))
    except OSError:
        pass  # a read-only home must not make the check itself fail


def report(checks: list[Check]) -> str:
    lines = []
    for c in checks:
        status = "ok" if c.ok else "MISSING" if c.required else "later"
        lines.append(f"{status:8} {c.name}" + ("" if c.ok else f"\n         fix: {c.fix}"))
    return "\n".join(lines)

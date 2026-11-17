"""Cover frames: one 1080x1920 cover from a chosen second (with an optional title) plus its profile-grid preview, or a contact sheet to choose from."""
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path

from content_studio.check import probe

W, H, GRID_H = 1080, 1920, 1440  # the profile grid shows the middle 3:4 of a 9:16 cover: keep the title inside it


def _ffmpeg(args: list, cwd=None) -> None:
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], capture_output=True, text=True, cwd=cwd)
    if r.returncode:
        raise ValueError(f"ffmpeg failed: {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else r.returncode}")


def _font() -> str:
    if shutil.which("fc-match"):
        f = subprocess.run(["fc-match", "-f", "%{file}", "sans:bold"], capture_output=True, text=True).stdout.strip()
        if f:
            return f":fontfile='{f.replace(chr(92), '/').replace(':', chr(92) + ':')}'"
    return ""


def make_cover(video: Path, out: Path, at: float = 1.0, title: str = "") -> Path:
    video, out = Path(video), Path(out)
    probe(video)  # a readable video, or ValueError
    out.parent.mkdir(parents=True, exist_ok=True)
    vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
    with tempfile.TemporaryDirectory() as tmp:
        if title.strip():
            Path(tmp, "t.txt").write_text(textwrap.fill(title.strip(), 16), encoding="utf-8")
            vf += (f",drawtext=textfile=t.txt:expansion=none{_font()}:fontsize=88:fontcolor=white:box=1:boxcolor=black@0.65:"
                   "boxborderw=28:line_spacing=14:x=(w-text_w)/2:y=(h-text_h)/2")
        _ffmpeg(["-ss", at, "-i", video.resolve(), "-frames:v", 1, "-vf", vf, "-q:v", 2, out.resolve()], cwd=tmp)
    if not out.exists():
        raise ValueError(f"no frame at {at} s: the video is shorter than that")
    _ffmpeg(["-i", out, "-vf", f"crop={W}:{GRID_H}", "-q:v", 2, out.with_suffix(".grid.jpg")])
    return out


def make_sheet(video: Path, out: Path, frames: int = 8) -> Path:
    video, out = Path(video), Path(out)
    duration = probe(video)["duration"]
    out.parent.mkdir(parents=True, exist_ok=True)
    _ffmpeg(["-i", video, "-vf", f"fps={frames}/{duration},scale=270:480,drawtext=text='%{{pts\\:hms}}':x=4:y=4:fontsize=16:fontcolor=yellow:box=1:boxcolor=black,tile=4x{-(-frames // 4)}",
             "-frames:v", 1, "-q:v", 3, out])
    return out

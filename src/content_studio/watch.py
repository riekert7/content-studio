"""Watch a reference video: frame sheets and a timed transcript, all in one folder.

watch(source) writes <out>/<extractor>-<id>/ (a URL, via yt-dlp) or <out>/local-<stem>/ (a local file, copied):
  video.mp4     the video (a local file is copied, never modified)
  hook.jpg      the first 3 s at 2 fps (the hook: seen, said and written in 0 to 2 s)
  scenes-NN.jpg the first frame, one at every cut and 10 across, 8x3 per sheet
  transcript.txt  with transcribe: faster-whisper, one `[start-end] text` line per segment.
                  A video with no audio track gets one note line instead of failing.
Re-running into an existing folder overwrites the files. The whisper model is CS_WHISPER_MODEL (default small),
cached by faster-whisper in its default (Hugging Face) cache.
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from content_studio.check import ffmpeg as _ffmpeg, probe
from content_studio.motion import cuts

TS = "drawtext=text='%{pts\\:hms}':x=4:y=4:fontsize=16:fontcolor=yellow:box=1:boxcolor=black"
DOWNLOAD_FAILED = ("Could not download that link (Instagram, TikTok and sometimes YouTube block downloads). "
                   "Download the video yourself and run `cs watch <local file>`.")
INSTALL = {"ffmpeg": "install ffmpeg (for example `sudo pacman -S ffmpeg` or `sudo apt install ffmpeg`)",
           "yt-dlp": "install yt-dlp (for example `uv tool install yt-dlp` or `pipx install yt-dlp`)"}


class WatchError(ValueError):
    pass


def _need(tool: str) -> None:
    if not shutil.which(tool):
        raise WatchError(f"{tool} is not on your PATH: {INSTALL[tool]}.")


def _log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def _download(url: str, out: Path) -> Path:
    template = f"{str(out).replace('%', '%%')}/%(extractor)s-%(id)s/video.%(ext)s"
    try:
        r = subprocess.run(["yt-dlp", "-q", "--no-warnings", "--no-playlist", "-f", "mp4/bestvideo*+bestaudio/best",
                            "--merge-output-format", "mp4", "--write-info-json", "-o", template,
                            "--print", "after_move:filepath", "--", url], capture_output=True, text=True, check=True)
        return Path(r.stdout.strip().splitlines()[-1])
    except (subprocess.CalledProcessError, OSError, IndexError) as e:
        raise WatchError(DOWNLOAD_FAILED) from e


def _transcribe(video: Path, has_audio: bool) -> list[str]:
    if not has_audio:
        return ["(no audio track, nothing to transcribe)"]
    import numpy as np  # numpy hand-off: faster-whisper's av build breaks on file paths

    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", str(video), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    try:
        from faster_whisper import WhisperModel  # lazy: other subcommands and --no-transcript never load it

        # language detected (references vary); vad_filter stops whisper inventing lines over music
        segs, _ = WhisperModel(os.environ.get("CS_WHISPER_MODEL", "small"), device="cpu", compute_type="int8"
                               ).transcribe(x, vad_filter=True, condition_on_previous_text=False)
        return [f"[{s.start:6.2f}-{s.end:6.2f}] {s.text.strip()}" for s in segs]
    except Exception as e:  # model download, missing install, decode: all user-facing
        raise WatchError(f"Transcription failed ({type(e).__name__}: {e}). Retry, or use --no-transcript.") from e


def watch(source: str, out: Path = Path("watch"), transcribe: bool = True) -> Path:
    out = Path(out)
    src = Path(source).expanduser()
    if src.is_file():
        _need("ffmpeg")
        d = out / f"local-{src.stem}"
        d.mkdir(parents=True, exist_ok=True)
        v = d / "video.mp4"
        if not (v.exists() and src.resolve() == v.resolve()):
            shutil.copyfile(src, v)  # the original is never touched
    elif re.match(r"https?://", source):
        _need("yt-dlp")
        _need("ffmpeg")
        _log("downloading...")
        v = _download(source, out)
        d = v.parent
    else:
        raise WatchError(f"{source!r} is not a file that exists and not a link (http:// or https://).")

    try:
        info = probe(v)
    except ValueError as e:
        raise WatchError(str(e)) from None
    has_audio, dur = info["audio"], info["duration"]
    _log("hook sheet...")
    # trim=0:3 uses what exists in a video shorter than 3 s
    _ffmpeg(["-i", v.name, "-vf", f"trim=0:3,fps=2,scale=216:-1,{TS},tile=6x1", "-frames:v", "1", "hook.jpg"], cwd=d)
    _log("finding cuts...")
    ct = cuts(v)
    # every cut, plus 10 across so a one-shot talking head still gets a sheet
    at = sorted(set(ct) | {round(k * dur / 10, 1) for k in range(1, 10)})
    sel = "+".join(["eq(n\\,0)"] + [f"gte(t\\,{c})*lt(prev_t\\,{c})" for c in at])
    for old in d.glob("scenes-*.jpg"):
        old.unlink()
    _ffmpeg(["-i", v.name, "-vf", f"select='{sel}',scale=216:-1,{TS},tile=8x3", "-fps_mode", "vfr",
             "scenes-%02d.jpg"], cwd=d)
    (d / "transcript.txt").unlink(missing_ok=True)  # never leave another run's transcript behind
    if transcribe:
        _log(f"transcribing (model {os.environ.get('CS_WHISPER_MODEL', 'small')}; the first run downloads it)...")
        lines = _transcribe(v, has_audio)
        (d / "transcript.txt").write_text("\n".join(lines) + "\n" if lines else "", encoding="utf-8")
    _log(f"{dur:.1f}s, {len(ct)} cuts at {ct}")
    return d

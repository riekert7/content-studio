"""Check a finished video against the platform basics: 9:16, 30 fps, a real audio track, loudness near -14 LUFS."""
import json
import re
import subprocess
from pathlib import Path

MAX_SECONDS = 90


def probe(path: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)], capture_output=True, text=True)
    try:
        data = json.loads(r.stdout or "{}")
        video = next(s for s in data["streams"] if s["codec_type"] == "video")
        num, den = video["r_frame_rate"].split("/")
        return {"width": int(video["width"]), "height": int(video["height"]), "fps": round(int(num) / int(den), 2),
                "duration": float(data["format"]["duration"]), "audio": any(s["codec_type"] == "audio" for s in data["streams"])}
    except (KeyError, StopIteration, ValueError, ZeroDivisionError):
        raise ValueError(f"{Path(path).name} is unreadable or has no video stream") from None


def loudness(path: Path) -> tuple[float | None, float | None]:
    err = subprocess.run(["ffmpeg", "-nostats", "-i", str(path), "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    summary = err[err.rfind("Summary:"):] if "Summary:" in err else ""
    i, p = re.search(r"\bI:\s+(-?\d+(?:\.\d+)?) LUFS", summary), re.search(r"\bPeak:\s+(-?\d+(?:\.\d+)?) dBFS", summary)
    return (float(i[1]) if i else None), (float(p[1]) if p else None)


def check_video(path: Path) -> dict:
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"{path} does not exist")
    info = probe(path)
    flags = []
    if info["width"] * 16 != info["height"] * 9:
        flags.append(f"shape is {info['width']}x{info['height']}, expected 9:16 (for example 1080x1920)")
    if abs(info["fps"] - 30) > 0.1:
        flags.append(f"fps is {info['fps']}, expected 30")
    if info["duration"] > MAX_SECONDS:
        flags.append(f"length is {info['duration']:.0f} s, over {MAX_SECONDS} s")
    info["lufs"] = info["peak"] = None
    if not info["audio"]:
        flags.append("no audio track: never ship a silent edit")
    else:
        info["lufs"], info["peak"] = loudness(path)
        if info["lufs"] is None:
            flags.append("could not measure loudness")
        elif not -16 <= info["lufs"] <= -12:
            flags.append(f"loudness is {info['lufs']} LUFS, aim for -14 (between -16 and -12)")
        if info["peak"] is not None and info["peak"] > -1.0:
            flags.append(f"peak is {info['peak']} dBFS, keep it under -1")
    return {"info": info, "flags": flags}

"""Build ref.mp4: 2 s of colour bars then 2 s of blue (one hard cut at 2.0 s), burned text, a 1 kHz tone. No real person.

python tests/fixtures/make_fixture.py   (needs ffmpeg)
"""
import subprocess
from pathlib import Path

REF = Path(__file__).parent / "ref.mp4"


def make_fixture(out=REF):
    out.parent.mkdir(parents=True, exist_ok=True)
    txt = "drawtext=text='FIXTURE':fontsize=40:fontcolor=white:box=1:boxcolor=black:x=(w-tw)/2:y=h*0.7"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "smptebars=s=270x480:r=30:d=2",
                    "-f", "lavfi", "-i", "color=c=0x2040c0:s=270x480:r=30:d=2", "-f", "lavfi", "-i", "sine=f=1000:d=4:r=48000",
                    "-filter_complex", f"[0][1]concat=n=2,{txt},format=yuv420p[v];[2]volume=2.25[a]",
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "30", "-c:a", "aac", "-shortest", str(out)],
                   check=True)
    return out


if __name__ == "__main__":
    print(make_fixture())

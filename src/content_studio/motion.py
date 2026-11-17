"""Where the cuts are in a video: the picture changes in one step, not gradually.

cuts: more than half of the 8x8 cells change by over 10% and so does the whole frame. A fast pan moves pixels;
a cut replaces them. Plus jump cuts: an isolated one-step spike (same framing, a small shift or a ~9% zoom).
"""
import subprocess

import numpy as np

FPS = 10


def frames(path, fps=FPS, w=54, h=96):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", str(path), "-vf", f"fps={fps},scale={w}:{h},format=gray",
                          "-f", "rawvideo", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)


def cuts(path, fps=FPS):
    f = frames(path, fps, 64, 112) / 255
    d = np.abs(np.diff(f, axis=0))
    cells = d.reshape(len(d), 14, 8, 8, 8).mean(axis=(2, 4))  # 8x8 px cells
    hit = ((cells > 0.1).mean(axis=(1, 2)) > 0.5) & (d.mean(axis=(1, 2)) > 0.1)
    # jump cuts: a change over 12 that is more than twice both neighbours. Handheld wobble spreads over several steps.
    m = np.pad(d.mean(axis=(1, 2)) * 255, 1)
    hit |= (m[1:-1] > 12) & (m[1:-1] > 2 * np.maximum(m[:-2], m[2:]))
    out = []
    for i in np.flatnonzero(hit):
        t = float(round((i + 1) / fps, 1))
        if not out or t - out[-1] > 0.25:  # one cut, not its neighbouring frames
            out.append(t)
    return out


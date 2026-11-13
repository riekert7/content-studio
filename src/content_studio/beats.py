import math
import re
from dataclasses import dataclass


@dataclass
class Beat:
    start: float
    end: float
    text: str
    carries: str


def parse_beats(text: str) -> list[Beat]:
    """Read the `| Start | End | Beat | Carries |` Markdown table (times in seconds)."""
    lines = text.splitlines()
    beats, header, stray = [], None, None
    for n, line in enumerate(lines, 1):
        row = line.strip()
        cells = [c.strip() for c in row.strip("|").split("|")]
        if header is None:
            if [c.lower() for c in cells] == ["start", "end", "beat", "carries"]:
                header = n
            continue
        if not row:
            continue
        if not row.startswith("|"):
            stray = stray or n  # prose is fine after the table, not inside it
            continue
        if stray:
            raise ValueError(f"line {stray}: unexpected text inside the beats table")
        if set("".join(cells)) <= set("-: "):
            continue  # separator row
        if [c.lower() for c in cells] == ["start", "end", "beat", "carries"]:
            raise ValueError(f"line {n}: second beats table header")
        if len(cells) != 4:
            raise ValueError(f"line {n}: expected 4 columns, got {len(cells)}")
        try:
            start, end = float(cells[0]), float(cells[1])
        except ValueError:
            raise ValueError(f"line {n}: start and end must be numbers of seconds") from None
        if not (math.isfinite(start) and math.isfinite(end)):
            raise ValueError(f"line {n}: start and end must be finite numbers")
        if start < 0:
            raise ValueError(f"line {n}: start must not be negative")
        if end <= start:
            raise ValueError(f"line {n}: end must be after start")
        beats.append(Beat(start, end, cells[2], cells[3]))
    if header is None:
        raise ValueError("line 1: no '| Start | End | Beat | Carries |' table found")
    if not beats:
        raise ValueError(f"line {header}: the beats table has no rows")
    return beats


def _words(s: str) -> set[str]:
    return set(re.findall(r"[a-z]{4,}", s.lower()))


def check_beats(beats: list[Beat], hook_max: float = 3.0, beat_max: float = 4.0) -> list[str]:
    flags = []
    lens = [b.end - b.start for b in beats]
    if lens and lens[0] > hook_max:
        flags.append(f"hook runs {lens[0]:g}s; keep it to {hook_max:g}s or less")
    for i, n in enumerate(lens[1:], 2):
        if n > beat_max:
            flags.append(f"beat {i} runs {n:g}s; keep each beat to {beat_max:g}s or less")
    for i, n in enumerate(lens, 1):
        if n <= 0:
            flags.append(f"zero or negative length on row {i}")
    if len(lens) > 1 and min(lens) > 0 and max(lens) / min(lens) < 4:
        flags.append(f"shot lengths do not vary: longest {max(lens):g}s vs shortest {min(lens):g}s, want 4x or more")
    for i, b in enumerate(beats[:-1], 1):
        if not b.carries:
            flags.append(f"row {i} has empty carries: say what it hands to the next row")
    if len(beats) > 1 and not _words(beats[0].text) & _words(beats[-1].text):
        flags.append("no loop: last row shares no word of 4+ letters with the first")
    return flags

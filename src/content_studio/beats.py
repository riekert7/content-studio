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
    beats, in_table = [], False
    for n, line in enumerate(text.splitlines(), 1):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not in_table:
            in_table = [c.lower() for c in cells] == ["start", "end", "beat", "carries"]
            continue
        if not line.strip().startswith("|"):
            break
        if set("".join(cells)) <= set("-: "):
            continue  # separator row
        if len(cells) != 4:
            raise ValueError(f"line {n}: expected 4 columns, got {len(cells)}")
        try:
            start, end = float(cells[0]), float(cells[1])
        except ValueError:
            raise ValueError(f"line {n}: start and end must be numbers of seconds") from None
        if end <= start:
            raise ValueError(f"line {n}: end must be after start")
        beats.append(Beat(start, end, cells[2], cells[3]))
    if not in_table:
        raise ValueError("line 1: no '| Start | End | Beat | Carries |' table found")
    if not beats:
        raise ValueError("line 1: the beats table has no rows")
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
    if len(lens) > 1 and max(lens) / min(lens) < 4:
        flags.append(f"shot lengths do not vary: longest {max(lens):g}s vs shortest {min(lens):g}s, want 4x or more")
    for i, b in enumerate(beats[:-1], 1):
        if not b.carries:
            flags.append(f"beat {i} carries nothing into the next beat")
    if len(beats) > 1 and not _words(beats[0].text) & _words(beats[-1].text):
        flags.append("no loop: last beat shares no word of 4+ letters with the first")
    return flags

"""Check a brand folder (brands/<brand>/) and the folder Claude was started in."""
import re
from pathlib import Path

REQUIRED: dict[str, list[str]] = {
    "brand.md": ["# Who it is for", "# The offer", "# What counts as a conversion", "# Claims we may and may not make"],
    "voice.md": ["# How they sound", "# Phrases they use", "# Never write"],
    "style.md": ["# Colours", "# Font", "# Captions", "# Logo"],
    "formats.md": ["# Face or voice", "# Length", "# Energy", "# The first 1.5 seconds"],
    "viewers.md": ["# Viewer 1", "# Viewer 2", "# Viewer 3"],
}
PROMPT = re.compile(r"^(\*[^*].*[^*]\*|_[^_].*[^_]_)$")  # a whole line in italics is a template prompt, not an answer


def _sections(text: str) -> dict[str, list[str]]:
    out, current = {}, None
    for line in text.splitlines():
        if line.startswith("# "):
            current = out.setdefault(line.strip(), [])
        elif current is not None and line.strip():
            current.append(line.strip())
    return out


def check_brand(path: Path, filled: bool = False) -> list[str]:
    """Problems found; an empty list means valid. With filled=True the template prompts do not count as answers."""
    problems = []
    for name, headings in REQUIRED.items():
        f = Path(path) / name
        if not f.is_file():
            problems.append(f"{name}: missing file")
            continue
        sections = _sections(f.read_text(encoding="utf-8-sig"))
        for h in headings:
            key = next((k for k in sections if k == h or k.startswith(h + " ") or k.startswith(h + ":")), None)
            if key is None:
                problems.append(f"{name}: missing heading {h}")
                continue
            body = [ln for ln in sections[key] if not (filled and PROMPT.match(ln))]
            if not body:
                problems.append(f"{name}: nothing under {h}")
    return problems


def check_workspace(path: Path, home: Path) -> str | None:
    p, h = Path(path).resolve(), Path(home).resolve()
    if p == h or p in h.parents or p == Path(p.anchor):
        return (f"{p} is your home folder or above it. Content Studio writes a brands/ folder and your videos into the folder "
                "you start in, so pick or create a project folder first (for example ~/content), then start Claude Code there.")
    return None

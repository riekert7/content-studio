"""The blind critic packet: evidence first, then the options, shuffled and relabelled, with every sign of our pick removed."""
import random
import re

PICK = re.compile(r"recommend|our pick|my pick|best option", re.I)


def _clean(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+|\n", str(text))
    return " ".join(s for s in sentences if s.strip() and not PICK.search(s))


def build_packet(options: list[dict], evidence: str, seed: int = 0) -> tuple[str, dict[str, str]]:
    shuffled = list(options)
    random.Random(seed).shuffle(shuffled)
    labels = {chr(65 + i): o["id"] for i, o in enumerate(shuffled)}
    parts = ["# Evidence", _clean(evidence) if PICK.search(evidence) else evidence.strip(), "", "# Options"]
    for label, o in zip(labels, shuffled):
        parts += ["", f"## Option {label}", f"**Title:** {_clean(o['title'])}", f"**Hook:** {_clean(o['hook'])}",
                  f"**Beats:** {_clean(o['beats'])}", f"**Send reason:** {_clean(o['send_reason'])}"]
    return "\n".join(parts) + "\n", labels
